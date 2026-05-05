# JIRA lab (live pull)

Streamlit app to **pull objects from JIRA Cloud** using the same object list as
the [Salesforce Data Cloud JIRA Structured Connector](https://developer.salesforce.com/docs/data/data-cloud-int/guide/c360-a-jira-objects.html).

- **Build & Run** — choose an object, parameters, assertions; run against JIRA.
- **Library** — re-run saved JSON test definitions (each run still hits JIRA).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: pre-fill JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
streamlit run app.py
```

Credentials: **sidebar** (Apply), **`.env`**, or **`st.secrets`** on Streamlit Cloud.

## Layout

| File | Role |
|------|------|
| `app.py` | UI |
| `jira_client.py` | Live REST client |
| `objects.py` | Object → endpoint catalog |
| `test_runner.py` | Load / save / run test case JSON |
| `test_cases/` | Saved definitions (created when you save) |
