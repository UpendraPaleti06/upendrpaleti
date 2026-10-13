import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from anthropic import beta_tool

from job_search_agent import tools

REMOTIVE = {
    "jobs": [
        {
            "id": 101,
            "title": "Python Backend Engineer",
            "company_name": "Acme",
            "candidate_required_location": "Worldwide",
            "job_type": "full_time",
            "salary": "$80k",
            "tags": ["python", "django"],
            "publication_date": "2026-10-01",
            "url": "https://remotive.com/jobs/101",
            "description": "<p>Build APIs with <b>Django</b> &amp; Postgres.</p>",
        }
    ]
}
ARBEITNOW = {
    "data": [
        {
            "slug": "python-dev-berlin",
            "title": "Python Developer",
            "company_name": "Beta GmbH",
            "location": "Berlin",
            "remote": True,
            "job_types": ["full time"],
            "tags": ["Python"],
            "created_at": 1760000000,
            "url": "https://www.arbeitnow.com/jobs/python-dev-berlin",
            "description": "<p>Python and FastAPI</p>",
        },
        {
            "slug": "onsite-python",
            "title": "Python Developer (onsite)",
            "company_name": "Gamma",
            "location": "Munich",
            "remote": False,
            "job_types": [],
            "tags": [],
            "created_at": 1760000000,
            "url": "https://www.arbeitnow.com/jobs/onsite-python",
            "description": "Python",
        },
        {
            "slug": "java-dev",
            "title": "Java Developer",
            "company_name": "Delta",
            "location": "Remote",
            "remote": True,
            "job_types": [],
            "tags": ["Java"],
            "created_at": 1760000000,
            "url": "https://www.arbeitnow.com/jobs/java-dev",
            "description": "Spring",
        },
    ]
}


def fake_fetch(url):
    if url.startswith(tools.REMOTIVE_URL):
        return REMOTIVE
    if url.endswith("page=1"):
        return ARBEITNOW
    return {"data": []}


class ToolTests(unittest.TestCase):
    def setUp(self):
        tools._job_cache.clear()

    def test_html_to_text(self):
        self.assertEqual(tools.html_to_text("<p>One</p><br><br><p>Two</p>"), "One\n\nTwo")
        self.assertEqual(tools.html_to_text("<p>A &amp; B</p><p>C</p>"), "A & B\nC")

    @mock.patch.object(tools, "_fetch_json", side_effect=fake_fetch)
    def test_search_combines_sources_and_filters(self, _):
        result = json.loads(tools.search_jobs("python"))
        ids = [job["id"] for job in result["jobs"]]
        self.assertEqual(ids, ["remotive:101", "arbeitnow:python-dev-berlin"])
        self.assertEqual(result["errors"], [])
        self.assertNotIn("description", result["jobs"][0])
        self.assertIn("Django & Postgres", result["jobs"][0]["snippet"])

    @mock.patch.object(tools, "_fetch_json", side_effect=fake_fetch)
    def test_search_can_include_onsite(self, _):
        result = json.loads(tools.search_jobs("python", remote_only=False))
        self.assertIn("arbeitnow:onsite-python", [job["id"] for job in result["jobs"]])

    def test_one_failing_source_is_reported(self):
        def flaky(url):
            if url.startswith(tools.ARBEITNOW_URL):
                raise OSError("network down")
            return fake_fetch(url)

        with mock.patch.object(tools, "_fetch_json", side_effect=flaky):
            result = json.loads(tools.search_jobs("python"))
        self.assertEqual([job["id"] for job in result["jobs"]], ["remotive:101"])
        self.assertEqual(result["errors"], ["arbeitnow: network down"])

    @mock.patch.object(tools, "_fetch_json", side_effect=fake_fetch)
    def test_get_job_details(self, _):
        tools.search_jobs("python")
        details = json.loads(tools.get_job_details("remotive:101"))
        self.assertEqual(details["company"], "Acme")
        self.assertIn("Unknown job id", tools.get_job_details("remotive:999"))

    def test_save_shortlist(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "out" / "shortlist.md"
            message = tools.make_save_shortlist(path)("# Jobs")
            self.assertEqual(path.read_text(), "# Jobs")
            self.assertIn(str(path), message)

    def test_tools_have_schemas(self):
        tool = beta_tool(tools.search_jobs)
        schema = tool.to_dict()
        self.assertEqual(schema["name"], "search_jobs")
        self.assertIn("keywords", schema["input_schema"]["properties"])
        self.assertEqual(schema["input_schema"]["required"], ["keywords"])


if __name__ == "__main__":
    unittest.main()
