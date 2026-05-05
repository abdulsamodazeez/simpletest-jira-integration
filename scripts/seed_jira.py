"""Seed the configured JIRA Cloud site with sample data.

Idempotent: skips creating issues for projects that already have any.
Run with::

    source .venv/bin/activate
    python scripts/seed_jira.py            # seeds the default project (KAN)
    python scripts/seed_jira.py --project EMAL --force

Use ``--force`` to add more issues even when the project is non-empty.

Requires JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in ``.env``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")

BASE_URL = (os.getenv("JIRA_BASE_URL") or "").rstrip("/")
EMAIL = os.getenv("JIRA_EMAIL") or ""
TOKEN = os.getenv("JIRA_API_TOKEN") or ""

if not (BASE_URL and EMAIL and TOKEN):
    print("ERROR: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN must all be set in .env")
    sys.exit(2)

AUTH = (EMAIL, TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
TIMEOUT = 30

API = BASE_URL + "/rest/api/3"


def adf(text: str) -> dict:
    """Wrap plain text in Atlassian Document Format - required by Cloud /comment, etc."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        ],
    }


def get(path: str, **kwargs):
    resp = requests.get(API + path, auth=AUTH, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    resp.raise_for_status()
    return resp.json()


def post(path: str, payload: dict):
    resp = requests.post(API + path, auth=AUTH, headers=HEADERS, json=payload, timeout=TIMEOUT)
    if not resp.ok:
        print(f"  POST {path} -> {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    if resp.text:
        try:
            return resp.json()
        except ValueError:
            return None
    return None


def existing_issue_count(project_key: str) -> int:
    """Quick presence check using the new /search/jql endpoint.

    JIRA Cloud removed /rest/api/3/search in its 2024 breaking-change rollout
    (returns HTTP 410). The replacement is /rest/api/3/search/jql, which uses
    nextPageToken pagination and no longer returns a total. We just need
    "is there at least one issue", so a maxResults=1 fetch is enough.
    """
    data = get(
        "/search/jql",
        params={"jql": f"project = {project_key}", "maxResults": 1, "fields": "summary"},
    )
    return len(data.get("issues", []))


SAMPLE_ISSUES: list[dict] = [
    {
        "summary": "Seed: foundation epic",
        "issuetype": "Epic",
        "description": "Top-level epic that groups the seeded backlog. Used to prove parent/child relationships.",
        "comments": [
            "Kicking off the seed run.",
            "Roadmap and acceptance criteria will be added next sprint.",
        ],
    },
    {
        "summary": "Seed: implement login flow",
        "issuetype": "Story",
        "description": "Allow a user to log in with email + password. Should rate-limit failed attempts.",
        "comments": ["Spec confirmed with design team.", "Ready for sprint planning."],
        "worklog_minutes": 90,
    },
    {
        "summary": "Seed: add password reset endpoint",
        "issuetype": "Story",
        "description": "POST /auth/reset accepts email and emails a magic link.",
        "comments": ["Need rate limiting and audit logs."],
    },
    {
        "summary": "Seed: fix off-by-one in pagination",
        "issuetype": "Task",
        "description": "Page 0 returns one fewer item than every other page. Reproduce with maxResults=10.",
        "comments": [],
        "worklog_minutes": 30,
    },
    {
        "summary": "Seed: clean up unused feature flag",
        "issuetype": "Task",
        "description": "Flag launchdarkly_old_pricing has been at 100% for 6 months - remove the branches.",
    },
    {
        "summary": "Seed: write integration test for billing webhook",
        "issuetype": "Task",
        "description": "Stripe webhook handler is currently untested end-to-end.",
        "comments": ["Use the recorded payload in fixtures/webhook_2025_03.json."],
    },
]

SUBTASK_PARENT_INDEX = 1
SAMPLE_SUBTASKS: list[str] = [
    "Seed: subtask - design login form",
    "Seed: subtask - hash and salt passwords",
]


def find_subtask_type_id(project_id: str) -> str | None:
    """Return the issue type ID for 'Subtask' in this project, if available."""
    types = get("/issuetype")
    for t in types:
        if t.get("name", "").lower() in {"subtask", "sub-task"}:
            scope = t.get("scope") or {}
            scope_pid = (scope.get("project") or {}).get("id")
            if scope_pid is None or str(scope_pid) == str(project_id):
                return t.get("id")
    return None


def create_issue(project_key: str, summary: str, issue_type: str, description: str | None = None) -> dict:
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    if description:
        fields["description"] = adf(description)
    return post("/issue", {"fields": fields})


def create_subtask(project_key: str, parent_key: str, summary: str, subtask_type_id: str) -> dict:
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"id": subtask_type_id},
        "parent": {"key": parent_key},
    }
    return post("/issue", {"fields": fields})


def add_comment(issue_key: str, body: str) -> None:
    post(f"/issue/{issue_key}/comment", {"body": adf(body)})


def add_worklog(issue_key: str, minutes: int) -> None:
    post(f"/issue/{issue_key}/worklog", {"timeSpentSeconds": minutes * 60})


def seed_project(project_key: str, force: bool) -> None:
    print(f"Target project: {project_key}")
    project = get(f"/project/{project_key}")
    project_id = project.get("id")
    print(f"  id={project_id} | name={project.get('name')} | type={project.get('projectTypeKey')}")

    count = existing_issue_count(project_key)
    print(f"  existing issues: {count}")

    if count > 0 and not force:
        print("  Skipping - project already has issues. Use --force to seed more.")
        return

    print("\nCreating issues...")
    created = []
    for spec in SAMPLE_ISSUES:
        try:
            res = create_issue(
                project_key,
                summary=spec["summary"],
                issue_type=spec["issuetype"],
                description=spec.get("description"),
            )
            key = res.get("key")
            print(f"  + {key:8}  {spec['issuetype']:6}  {spec['summary']}")
            created.append((key, spec))
        except requests.HTTPError as exc:
            print(f"  ! Failed to create '{spec['summary']}': {exc}")

    if not created:
        print("\nNo issues created - aborting follow-up steps.")
        return

    print("\nAdding comments...")
    for key, spec in created:
        for body in spec.get("comments", []):
            try:
                add_comment(key, body)
                print(f"  + comment on {key}: {body[:60]}")
            except requests.HTTPError as exc:
                print(f"  ! Failed comment on {key}: {exc}")

    print("\nAdding worklogs...")
    for key, spec in created:
        minutes = spec.get("worklog_minutes")
        if minutes:
            try:
                add_worklog(key, minutes)
                print(f"  + worklog on {key}: {minutes} minutes")
            except requests.HTTPError as exc:
                print(f"  ! Failed worklog on {key}: {exc}")

    print("\nCreating subtasks...")
    subtask_type_id = find_subtask_type_id(project_id)
    if not subtask_type_id:
        print("  Skipping - no Subtask issue type available in this project.")
    else:
        parent_key = created[SUBTASK_PARENT_INDEX][0] if len(created) > SUBTASK_PARENT_INDEX else created[0][0]
        for summary in SAMPLE_SUBTASKS:
            try:
                res = create_subtask(project_key, parent_key, summary, subtask_type_id)
                print(f"  + {res.get('key'):8}  Subtask  parent={parent_key}  {summary}")
            except requests.HTTPError as exc:
                print(f"  ! Failed subtask '{summary}': {exc}")

    print("\nDone. Verifying...")
    final_data = get(
        "/search/jql",
        params={
            "jql": f"project = {project_key} ORDER BY created DESC",
            "maxResults": 100,
            "fields": "summary,issuetype,status",
        },
    )
    issue_count = len(final_data.get("issues", []))
    print(f"  {project_key} now has {issue_count} issues (showing first {min(10, issue_count)}):")
    for issue in final_data.get("issues", [])[:10]:
        f = issue.get("fields", {})
        print(
            f"    - {issue.get('key'):8} {f.get('issuetype', {}).get('name', '?'):8} "
            f"{f.get('status', {}).get('name', '?'):12} {f.get('summary', '')[:60]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="KAN", help="Project key to seed (default: KAN)")
    parser.add_argument("--force", action="store_true", help="Seed even if project already has issues")
    args = parser.parse_args()
    seed_project(args.project, args.force)


if __name__ == "__main__":
    main()
