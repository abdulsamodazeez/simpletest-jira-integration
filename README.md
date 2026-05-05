# Simpletest JIRA Demo

A Streamlit prototype that stands in for the **Salesforce Data Cloud JIRA
Structured Connector**. You author lightweight "test cases" that pull objects
from JIRA, run them, and inspect the results. Every JIRA object listed in the
[Salesforce JIRA Connector docs](https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-jira-objects.html)
is represented in the catalog.

## What this is

- A **System Under Test stand-in** for the Salesforce Data Cloud JIRA
  connector while no Data Cloud org is available.
- A way to **author and persist test cases** as JSON. Each test case
  declares which JIRA object to pull, with what filters, and what
  assertions must hold for it to pass.
- A **demo surface** to show stakeholders the same objects the SF
  connector ingests, pulled live from a real JIRA Cloud site.

## Quick start

```bash
cd simpletest-jira-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: default credentials for first load (sidebar can override).
cp .env.example .env
# edit .env with your JIRA Cloud creds

streamlit run app.py
```

The app will be at <http://localhost:8501>.

## Credentials

The app talks to **live JIRA Cloud** only. Configure either:

1. **Sidebar** (recommended) — URL, email, API token → **Apply connection**
   (per browser tab; overrides `.env` until **Clear override**).
2. **`.env`** — set `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` so fields
   pre-fill and the app works before you open the sidebar.

A green **JIRA ready** banner appears when all three values are available
(from sidebar or `.env`).

## Connecting your own JIRA

You need a JIRA **Cloud** site (`*.atlassian.net`). Self-hosted Server / Data
Center uses a different auth flow and is not supported here.

1. **Find your site URL** — log into JIRA and copy the domain, e.g.
   `https://acme.atlassian.net`.
2. **Generate an API token** at
   <https://id.atlassian.com/manage-profile/security/api-tokens>.
   Click *Create API token*, label it `simpletest-jira-demo`, copy the
   value immediately (it is only shown once).
3. **Note your Atlassian account email** — the one you log in with.
4. **Populate `.env`** in this folder (or paste the same values in the
   sidebar and click **Apply connection**):
   ```
   JIRA_BASE_URL=https://your-site.atlassian.net
   JIRA_EMAIL=you@company.com
   JIRA_API_TOKEN=ATATT3xFf...
   ```
5. Use **Test connection** in the sidebar to verify `/myself` returns 200.

### Optional JIRA features

Some objects only return data if your JIRA site has the relevant feature:

- **JIRA Software** — required for `Boards`, `Sprints`, `Epics`,
  `BoardIssues`, `SprintIssues`, `BoardConfiguration`, `BoardSprints`.
- **JIRA Service Management** — required for service-desk-flavored
  objects.

The app does not hide unavailable objects — it surfaces the API error so
you can see exactly what JIRA returned.

## How a "test case" works

A test case is a single JSON file in `test_cases/`. Example:

```json
{
  "name": "Pull recent issues",
  "object": "Issues",
  "params": {
    "jql": "created >= -30d ORDER BY created DESC",
    "maxResults": "25"
  },
  "assertions": {
    "min_records": 1,
    "required_fields": ["key", "fields.summary", "fields.status.name"]
  }
}
```

Running it:

1. The runner looks up `Issues` in the object catalog and resolves the
   JIRA REST endpoint.
2. It executes a **live** GET against your JIRA site.
3. It evaluates assertions against the response.
4. It returns a pass/fail result with details, surfaced in the UI.

You can build new test cases interactively in the **Build & Run** tab and
save them with one click. The **Library** tab lists those JSON files so you
can **Run** the same pull again against live JIRA.

## Seeding sample data into your JIRA site

If you've connected your own JIRA Cloud site but the project
has no issues yet, run:

```bash
source .venv/bin/activate
python scripts/seed_jira.py --project KAN          # default project
python scripts/seed_jira.py --project KAN --force  # add more even if non-empty
```

The script creates ~6 issues (mix of Epic, Story, Task), a couple of
subtasks, several comments, and a few worklogs - enough to make every
relevant test case return data. It is idempotent unless `--force` is
passed.

## Project layout

```
simpletest-jira-demo/
├── app.py                # Streamlit UI
├── branding.py           # SimpleTest-aligned CSS + hero/footer
├── jira_client.py        # JIRA REST client (live only)
├── objects.py            # Catalog of all 64 SF JIRA connector objects
├── test_runner.py        # Executes a test case, evaluates assertions
├── scripts/
│   └── seed_jira.py      # Populates a real JIRA project with sample issues
├── requirements.txt
├── .env.example
└── test_cases/           # Saved test case JSON files (Library tab)
```

## Limitations

- The Streamlit app is read-only. The app never writes to JIRA. Only the
  optional `scripts/seed_jira.py` writes (and only if you run it).
- Cloud-only auth (email + API token via HTTP Basic).
- Pagination is single-page for now (`maxResults` cap).
- Some objects in the SF catalog are documented as Server-only or
  OAuth-only and may return empty / 404 against Cloud + Basic Auth.
  These are kept in the catalog and labeled.
- The `Issues` and `IssueSubtasks` objects use JIRA Cloud's new
  `/rest/api/3/search/jql` endpoint. The legacy `/rest/api/3/search`
  was removed by Atlassian in their 2024 breaking-change rollout
  (returns HTTP 410 Gone).

## Deploy (public URL)

See **[DEPLOY.md](DEPLOY.md)** — recommended path is **Streamlit Community Cloud**
(`https://<name>.streamlit.app`) with JIRA credentials in **App secrets**.
