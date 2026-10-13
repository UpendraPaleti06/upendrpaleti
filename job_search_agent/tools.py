"""Tools the agent can call: search public job boards, read a posting, save a shortlist.

Job data comes from two free, key-less APIs:
- Remotive (https://remotive.com/api/remote-jobs) - remote jobs, server-side search
- Arbeitnow (https://www.arbeitnow.com/api/job-board-api) - mostly EU jobs, filtered here
"""

import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
USER_AGENT = "job-search-agent/0.1 (+https://github.com/UpendraPaleti06/upendrpaleti)"
MAX_DESCRIPTION_CHARS = 4000

# Every job returned by search_jobs, keyed by its id, so get_job_details can look it up.
_job_cache: dict[str, dict] = {}


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def html_to_text(raw: str) -> str:
    """Turn an HTML job description into plain text."""
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _matches(job: dict, words: list[str]) -> bool:
    haystack = " ".join(
        [job["title"], job["company"], " ".join(job["tags"]), job["description"]]
    ).lower()
    return all(word in haystack for word in words)


def _search_remotive(keywords: str, limit: int) -> list[dict]:
    query = urllib.parse.urlencode({"search": keywords, "limit": limit})
    data = _fetch_json(f"{REMOTIVE_URL}?{query}")
    return [
        {
            "id": f"remotive:{job['id']}",
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("candidate_required_location") or "Remote",
            "remote": True,
            "job_type": job.get("job_type", ""),
            "salary": job.get("salary", ""),
            "tags": job.get("tags") or [],
            "posted": job.get("publication_date", ""),
            "url": job.get("url", ""),
            "description": html_to_text(job.get("description", "")),
        }
        for job in data.get("jobs", [])
    ]


def _search_arbeitnow(keywords: str, remote_only: bool, limit: int) -> list[dict]:
    words = keywords.lower().split()
    found = []
    for page in (1, 2):  # the API has no search parameter, so scan the newest pages
        data = _fetch_json(f"{ARBEITNOW_URL}?page={page}")
        for job in data.get("data", []):
            item = {
                "id": f"arbeitnow:{job['slug']}",
                "title": job.get("title", ""),
                "company": job.get("company_name", ""),
                "location": job.get("location", ""),
                "remote": bool(job.get("remote")),
                "job_type": ", ".join(job.get("job_types") or []),
                "salary": "",
                "tags": job.get("tags") or [],
                "posted": str(job.get("created_at", "")),
                "url": job.get("url", ""),
                "description": html_to_text(job.get("description", "")),
            }
            if (item["remote"] or not remote_only) and _matches(item, words):
                found.append(item)
                if len(found) >= limit:
                    return found
    return found


def search_jobs(keywords: str, remote_only: bool = True, limit: int = 10) -> str:
    """Search public job boards for openings matching the keywords.

    Returns a JSON list of job summaries (id, title, company, location, tags, url,
    and a short snippet). Use get_job_details with a job's id to read the full posting.
    Try a few different keyword phrasings (e.g. "python backend", "django") to find more jobs.

    Args:
        keywords: Search terms such as a job title or main skill, e.g. "python developer".
        remote_only: If true, only return remote jobs.
        limit: Maximum number of jobs to return from each job board (1-25).
    """
    limit = max(1, min(int(limit), 25))
    results, errors = [], []
    for source, search in (
        ("remotive", lambda: _search_remotive(keywords, limit)),
        ("arbeitnow", lambda: _search_arbeitnow(keywords, remote_only, limit)),
    ):
        try:
            jobs = search()
        except Exception as exc:  # one board being down shouldn't stop the search
            errors.append(f"{source}: {exc}")
            continue
        for job in jobs:
            _job_cache[job["id"]] = job
            summary = {k: v for k, v in job.items() if k != "description"}
            summary["snippet"] = job["description"][:300]
            results.append(summary)
    return json.dumps({"jobs": results, "errors": errors}, ensure_ascii=False)


def get_job_details(job_id: str) -> str:
    """Get the full description of a job returned by search_jobs.

    Args:
        job_id: The job's id exactly as returned by search_jobs, e.g. "remotive:123456".
    """
    job = _job_cache.get(job_id)
    if job is None:
        return f"Unknown job id {job_id!r}. Only ids returned by search_jobs can be looked up."
    details = dict(job)
    if len(details["description"]) > MAX_DESCRIPTION_CHARS:
        details["description"] = details["description"][:MAX_DESCRIPTION_CHARS] + " [truncated]"
    return json.dumps(details, ensure_ascii=False)


def make_save_shortlist(output_path: Path):
    """Build the save_shortlist tool, writing to output_path."""

    def save_shortlist(markdown: str) -> str:
        """Save the final ranked shortlist of jobs as a Markdown file for the user.

        Call this once at the end with the complete shortlist.

        Args:
            markdown: The full shortlist in Markdown: each job's title, company, link,
                fit score, why it fits, skill gaps, and a short pitch the user can adapt.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        return f"Saved shortlist to {output_path}"

    return save_shortlist
