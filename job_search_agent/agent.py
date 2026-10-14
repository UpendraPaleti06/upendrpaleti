"""Run the job-search agent from the command line.

Example:
    python -m job_search_agent "Find remote Python backend jobs" --profile my_profile.txt
"""

import argparse
import json
import sys
from pathlib import Path

import anthropic
from anthropic import beta_tool

from .tools import get_job_details, make_save_shortlist, search_jobs

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You are a job-search assistant. You find real openings that fit the \
candidate and explain clearly why each one fits.

How to work:
1. Read the candidate profile and the request. Pick 3-5 search phrasings (job titles and \
key skills) and run search_jobs for each.
2. Open the most promising postings with get_job_details before judging them.
3. Rank the best {top} jobs by fit with the profile: skills, experience level, location \
and remote preference, and anything the candidate said they want or don't want.
4. Call save_shortlist once with a Markdown shortlist. For each job include: title, \
company, link, a fit score out of 10, 2-3 reasons it fits, any skill gaps, and a \
2-3 sentence pitch the candidate can adapt for their application.
5. Finish with a short summary of the shortlist and suggestions for widening or narrowing \
the search.

Only list jobs that came back from the tools, with their exact links. Never invent jobs, \
companies, salaries or requirements. If the searches find few good matches, say so."""


def run(request: str, profile: str, top: int, output: Path, effort: str) -> int:
    client = anthropic.Anthropic()
    tools = [
        beta_tool(search_jobs),
        beta_tool(get_job_details),
        beta_tool(make_save_shortlist(output)),
    ]
    user_message = f"Candidate profile:\n{profile or '(not provided)'}\n\nRequest: {request}"

    runner = client.beta.messages.tool_runner(
        model=MODEL,
        max_tokens=16000,
        max_iterations=25,
        system=SYSTEM_PROMPT.format(top=top),
        output_config={"effort": effort},
        # If a safety classifier declines, retry on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        tools=tools,
        messages=[{"role": "user", "content": user_message}],
    )

    final = None
    for message in runner:
        final = message
        for block in message.content:
            if block.type == "tool_use":
                print(f"-> {block.name}({json.dumps(block.input, ensure_ascii=False)[:120]})")

    if final is None:
        print("The agent returned no response.", file=sys.stderr)
        return 1
    if final.stop_reason == "refusal":
        print("The model declined this request. Try rephrasing it.", file=sys.stderr)
        return 1
    print()
    print("".join(block.text for block in final.content if block.type == "text"))
    if final.stop_reason == "max_tokens":
        print("\n(The answer was cut off by the token limit.)", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find and rank jobs that fit your profile.")
    parser.add_argument("request", help='What you are looking for, e.g. "remote Python backend jobs"')
    parser.add_argument("--profile", type=Path, help="Text file with your skills and experience")
    parser.add_argument("--top", type=int, default=5, help="How many jobs to shortlist (default 5)")
    parser.add_argument("--output", type=Path, default=Path("shortlist.md"), help="Where to save the shortlist")
    parser.add_argument(
        "--effort",
        choices=["low", "medium", "high", "xhigh", "max"],
        default="high",
        help="How hard the model thinks; higher is more thorough but uses more tokens",
    )
    args = parser.parse_args(argv)
    profile = args.profile.read_text(encoding="utf-8") if args.profile else ""
    return run(args.request, profile, args.top, args.output, args.effort)
