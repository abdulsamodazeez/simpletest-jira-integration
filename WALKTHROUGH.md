# Simpletest JIRA Demo - Build Walkthrough

A plain-English breakdown of what was built, why, and how the pieces fit
together. Read top to bottom for the full story; jump to a section if
you only need one part.

> **Note (May 2026):** The app is **live JIRA only** — mock mode, `sample_data/`,
> and shipped `smoke_*.json` files were removed. Credentials live in the
> **sidebar** (with **Test connection**) or `.env`. The **Connection** tab is
> gone; use **Build & Run** and **Library** only. Some sections below retain
> earlier narrative detail.

---

## 1. The original ask

- A request came in: **"Create a test case that demonstrates pulling
  objects from JIRA"**, with a link to the Salesforce Data Cloud JIRA
  Connector documentation that lists every JIRA object the connector can
  ingest (Issue, Project, Board, Sprint, Comment, Worklog, etc. - 64 in
  total).
- Two real constraints:
  - **No Salesforce Data Cloud org** is available right now, so a "real"
    end-to-end demo of the connector wasn't possible.
  - **No JIRA site** at the start, so even pulling raw JIRA data wasn't
    immediately possible.

---

## 2. How we interpreted it

We considered four readings of the ask and picked the one that was both
honest and deliverable:

- **(a) Real Data Cloud connector flow** - blocked, no org.
- **(b) JIRA-only test case via REST** - feasible once JIRA login exists.
- **(c) Streamlit prototype as a stand-in for Data Cloud** - good demo
  surface, gives stakeholders something to look at.
- **(d) Loose proof-of-concept** - too vague to be useful.

We chose **(b) + (c) combined**: a Streamlit app that authors and runs
**test cases** which pull JIRA objects via the JIRA REST API. The app is
the "system under test" stand-in until Data Cloud access exists; the
test cases are real, reusable, version-controllable artifacts.

---

## 3. The project layout we ended up with

```
simpletest-jira-demo/
├── app.py                # Streamlit UI (2 tabs + sidebar)
├── jira_client.py        # HTTP client (live JIRA only)
├── objects.py            # Catalog of all 64 JIRA objects from the SF doc
├── test_runner.py        # Loads, saves, runs test cases; evaluates assertions
├── scripts/
│   └── seed_jira.py      # Populates a JIRA project with sample issues
├── branding.py           # SimpleTest-aligned CSS + hero
├── test_cases/           # Saved test case JSON files
├── README.md             # Quick-start + setup
├── WALKTHROUGH.md        # This file
├── requirements.txt
├── .env                  # Real JIRA creds (gitignored)
└── .env.example          # Template
```

---

## 4. What each component does

### 4.1 `objects.py` - the JIRA object catalog

- Single source of truth: every one of the 64 objects listed in the
  Salesforce JIRA Connector doc has an entry.
- Each entry maps the object name to:
  - the JIRA REST endpoint that returns it,
  - whether it lives under `/rest/api/3` (platform) or
    `/rest/agile/1.0` (Software / Agile),
  - what parameters the user must supply (e.g. `Comments` needs
    `issueIdOrKey`),
  - a `response_path` that tells the client how to dig the records out
    of JIRA's inconsistent response shapes (some endpoints wrap data in
    `"issues"`, some in `"values"`, some return a bare list).
- Adding or fixing an object is a **one-line change** in this file.

### 4.2 `jira_client.py` - the HTTP layer

- One function (`fetch`) handles every object in the catalog.
- Two modes, picked at call time from environment variables:
  - **LIVE** - hits real JIRA Cloud over HTTP Basic with email + API token.
  - **MOCK** - serves canned JSON from `sample_data/`. Falls back to
    `_default.json` for any object without specific mock data.
- Returns a uniform `JiraResponse` shape regardless of mode, so the
  rest of the app doesn't care which path was taken.
- A `whoami()` helper hits `/myself` and is used to verify credentials
  on the **Connection** tab.

### 4.3 `test_runner.py` - the test case engine

- A **test case** is just a JSON file describing one pull plus the
  assertions that must hold.
- Schema: `name`, `object` (catalog name), `params` (dict),
  `assertions` (`min_records`, `max_records`, `required_fields`).
- `run_case()` executes the pull, evaluates assertions, returns a
  structured `TestCaseRun` with PASS/FAIL, record count, HTTP status,
  duration, and per-assertion detail.
- `save_case()`, `load_case()`, `list_cases()`, `delete_case()` make
  test cases first-class artifacts under `test_cases/`.

### 4.4 `app.py` - the Streamlit UI

Three tabs, all sharing a mode badge at the top (LIVE / MOCK):

- **Connection** - shows current mode, has a *Re-check connection*
  button that hits `/myself`, and a how-to panel for hooking up your
  own JIRA.
- **Build & Run** - choose any of the 64 objects, the form
  auto-generates inputs from the catalog (path params, query params,
  defaults). Set assertions, hit *Run* to execute live, or *Save* to
  persist as a JSON file.
- **Library** - lists every saved test case. Expand any case to see
  its definition, run it again, or delete it.

Result rendering is consistent across tabs: a 4-metric summary bar
(result, record count, HTTP, duration), an assertions checklist, the
records as a dataframe, and the raw response in a collapsible panel.

### 4.5 `scripts/seed_jira.py` - sample data populator

- Idempotent: skips creating issues for projects that already have any
  (override with `--force`).
- Creates a varied backlog: 1 Epic, 2 Stories, 3 Tasks, 2 Subtasks,
  several comments, a couple of worklogs.
- Uses Atlassian Document Format (ADF) for comment/description bodies,
  which JIRA Cloud requires.
- Lets the prototype demonstrate every relevant object without needing
  the user to author content by hand.

### 4.6 `sample_data/` - canned mock responses

- One JSON file per representative object (`Issues`, `Projects`,
  `Users`, `Comments`, `Boards`, `Sprints`).
- A generic `_default.json` covers any object we didn't author specific
  mock data for.
- These mirror the real JIRA response shapes so the rest of the code
  doesn't need a separate code path for mock vs live.

### 4.7 `test_cases/` - shipped smoke tests

- `smoke_pull_issues.json` - pulls recent issues, asserts at least one
  exists with key/summary/status fields.
- `smoke_pull_projects.json` - pulls projects, asserts at least one
  exists with key/name/projectTypeKey fields.

---

## 5. What's now sitting in the connected JIRA site

The seed script populated `KAN` (the user's *Simpletest* project) with:

- **8 issues** (KAN-1 through KAN-8): 1 Epic, 2 Stories, 3 Tasks, 2 Subtasks
- **6 comments** spread across KAN-1, KAN-2, KAN-3, KAN-6
- **2 worklogs**: KAN-2 (1h 30m) and KAN-4 (30m)
- **2 subtasks** under KAN-2 (KAN-7, KAN-8)

Plus the pre-existing Atlassian "Example Mobile App Launch" project
(`EMAL`) and its sample issues, both auto-created with the JIRA Cloud
trial.

---

## 6. The four stumbles (and the fixes)

### 6.1 Streamlit emoji shortcodes don't work in `icon=`

- **Symptom:** `st.warning(icon="warning")` raised
  `StreamlitAPIException: ... is not a valid emoji`.
- **Why:** Streamlit's alert components require a literal emoji
  character; shortcodes like `"warning"` are not accepted there.
- **Fix:** Replaced shortcodes with literal emojis (`✅`, `⚠️`, `ℹ️`, `🔍`).

### 6.2 `st.dataframe(width="stretch")` is too new

- **Symptom:** `TypeError: 'str' object cannot be interpreted as an integer`.
- **Why:** `width="stretch"` was added in Streamlit ≥1.40. We pinned
  1.39.0. The 1.39 API expects an `int` for `width` or
  `use_container_width=True`.
- **Fix:** Switched to `use_container_width=True`, which is forward
  and backward compatible.

### 6.3 The first JIRA URL was a non-existent site

- **Symptom:** Auth check returned HTTP 404
  `"Site temporarily unavailable"`.
- **Why:** The initial URL guess didn't match the real JIRA site
  subdomain that Atlassian provisioned for the trial.
- **Fix:** User pulled the actual URL from their browser
  (`abdulsamod589-1777642915504.atlassian.net`) and we updated `.env`.

### 6.4 Atlassian removed `/rest/api/3/search`

- **Symptom:** Pulls of `Issues` returned HTTP 410 Gone.
- **Why:** Atlassian retired the legacy `/search` endpoint in their
  2024 breaking-change rollout, replaced it with `/search/jql`.
- **Fix part 1:** Updated the catalog (`Issues`, `IssueSubtasks`) to
  use `/search/jql`. Added a `fields` parameter, because the new
  endpoint defaults to ID-only - without it you get records with no
  `summary`, `status`, etc.
- **Fix part 2 (follow-up bug):** The new endpoint also rejects
  *unbounded* JQL queries (`ORDER BY created DESC` alone returns 400
  `"Unbounded JQL queries are not allowed here"`). Updated the default
  to `created >= -30d ORDER BY created DESC` and the help text
  explains the constraint.

---

## 7. How verification was done

- **Compile + lint** - all four Python modules pass `py_compile`, no
  linter warnings.
- **Mock-mode end-to-end** - both shipped smoke tests pass against
  canned data.
- **Live-mode end-to-end** - both shipped smoke tests pass against the
  real connected JIRA site (15 records returned for Issues, 2 for
  Projects, 2 for Comments, 1 for Worklogs, 2 for Subtasks, 2 for
  Boards).
- **Streamlit AppTest harness** - drives the script the same way a
  browser session does. Both *Run test case* and *Save test case*
  buttons execute without exceptions on every script change.

The AppTest harness was added specifically because the first headless
smoke check (which only confirmed the homepage returned HTTP 200) gave
false confidence: it never actually ran the script, so it missed the
emoji and dataframe bugs. AppTest now catches that whole class of
issues before the user sees them.

---

## 8. How to run it

```bash
cd simpletest-jira-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: hook up real JIRA. Without these the app runs in MOCK mode.
cp .env.example .env
#   edit JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN

# Optional: populate JIRA with sample data (LIVE mode only)
python scripts/seed_jira.py --project KAN

# Launch the UI
streamlit run app.py
```

The app opens at <http://localhost:8501>.

---

## 9. What this gets us towards the original ask

- **A reusable test case format** - JSON, version-controllable, one file
  per case, portable across teams.
- **64 supported object types** - matching the Salesforce Data Cloud
  JIRA Connector catalog 1:1.
- **A real demo surface** - Streamlit UI showing a JIRA pull happening
  live, suitable for a stakeholder walk-through.
- **A clean migration path** - when Data Cloud access arrives, the
  test cases stay the same; only the runner needs an alternate
  implementation that hits Data Cloud DLOs instead of JIRA directly.
  The catalog and the assertion model already encode the right
  mental model.
- **Honest scope** - the README and this walkthrough are explicit that
  this is a stand-in, not the real connector flow. No one will be
  misled about what was actually demonstrated.

---

## 10. Reasonable next steps

- Add **status transitions** to the seed script so demo data isn't all
  "To Do".
- Add **pagination** (currently capped at one page / `maxResults`).
- Add **Data Cloud runner** alongside the JIRA runner once an org is
  available - existing test cases run unchanged, just point the runner
  at a different URL.
- Add a small **`pytest` wrapper** so all saved test cases can run as a
  CI job (`pytest tests/`) without launching Streamlit.
- Optionally **rotate the JIRA API token** if it has been shared outside
  this project.
