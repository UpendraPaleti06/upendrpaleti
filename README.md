# upendrpaleti

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Upendra%20Paleti-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/upendra-paleti-a7778216b)

Connect with me on [LinkedIn](https://www.linkedin.com/in/upendra-paleti-a7778216b).

## Job Search Agent

An AI agent built on the [Claude API](https://platform.claude.com/docs). You describe the job you want, and it:

1. searches free job boards ([Remotive](https://remotive.com) and [Arbeitnow](https://www.arbeitnow.com)) using several different search phrasings,
2. reads the most promising postings in full,
3. ranks the best matches against your profile, giving a fit score, reasons and skill gaps for each,
4. saves a shortlist to `shortlist.md`, with a short pitch for each job that you can adapt.

The agent decides by itself what to search for and which postings to open. The code only defines its tools (`search_jobs`, `get_job_details` and `save_shortlist`), and the Anthropic SDK's tool runner handles the loop.

### Run it

You need Python 3.10 or newer, which includes pip. **New to Python on Windows?** Follow the step-by-step [Windows setup guide](docs/windows-setup.md).

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # get one at https://platform.claude.com

cp example_profile.txt my_profile.txt     # then edit it with your skills and preferences
python -m job_search_agent "Find remote Python backend jobs" --profile my_profile.txt
```

Options: `--top 5` (how many jobs to shortlist), `--output shortlist.md` (where to save the shortlist), and `--effort high` (`low` to `max`; higher effort is more thorough but uses more tokens).

### Project layout

| Path | What it does |
| --- | --- |
| `job_search_agent/tools.py` | The tools: job-board search, posting details, saving the shortlist |
| `job_search_agent/agent.py` | System prompt, the agent loop and the command-line interface |
| `tests/test_tools.py` | Unit tests with mocked job-board responses (`python -m unittest`) |
