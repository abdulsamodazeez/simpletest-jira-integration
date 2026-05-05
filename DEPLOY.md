# Deploying SimpleTest JIRA lab (permanent URL)

This app is a standard **Streamlit** project (`app.py` + `requirements.txt`).
Below are practical ways to get a **stable public URL**.

---

## Option A — Streamlit Community Cloud (easiest, free tier)

Gives you a permanent link like **`https://<your-app-name>.streamlit.app`**
as long as the app stays deployed and within [Streamlit Cloud limits](https://streamlit.io/cloud).

### 1. Push the repo to GitHub

From the project folder (do **not** commit `.env` or `.streamlit/secrets.toml`):

```bash
cd simpletest-jira-demo
git init
git add app.py jira_client.py objects.py test_runner.py branding.py \
  requirements.txt .streamlit/config.toml README.md DEPLOY.md \
  test_cases/ scripts/
git commit -m "Add SimpleTest JIRA lab Streamlit app"
```

Create an empty repo on GitHub, then:

```bash
git remote add origin https://github.com/abdulsamodazeez/simpletest-jira-integration.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io) (GitHub login).
2. **New app** → pick your repository and branch.
3. **Main file path:** `app.py`
4. **Deploy.**

### 3. Add JIRA secrets (required for live API)

In the Cloud UI: **App settings → Secrets**, paste TOML (replace with your real values):

```toml
JIRA_BASE_URL = "https://your-site.atlassian.net"
JIRA_EMAIL = "you@company.com"
JIRA_API_TOKEN = "your-atlassian-api-token"
```

Save. The app reads these via `st.secrets` (see `_read_jira_setting` in `app.py`)
and **auto-activates** the connection when all three are present, so visitors
do not need to click **Apply** unless you want to override.

### 4. Optional: pin Python version

If Cloud’s default Python ever mismatches your stack, add `runtime.txt` at
the repo root with one line, e.g. `python-3.12.8` (check Streamlit Cloud docs
for supported versions).

---

## Option B — Docker on Fly.io / Railway / Render (full control)

Useful if you need a custom domain, VPC, or non-GitHub deploy.

1. Add a `Dockerfile` that installs `requirements.txt` and runs:

   ```bash
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```

2. Set **`JIRA_BASE_URL`**, **`JIRA_EMAIL`**, **`JIRA_API_TOKEN`** as platform
   environment variables (same names as `.env`).

3. Map HTTPS port 443 → container **8501** (or whatever you configure).

The sidebar still works for session overrides; env vars seed the first load
after `load_dotenv()` — on Docker you typically rely on real env vars, not a
`.env` file baked into the image.

---

## Security checklist

- **Never** commit `JIRA_API_TOKEN` or `.env` to git.
- Prefer **Streamlit Cloud secrets** or the host’s **secret env vars**.
- **Rotate** the Atlassian token if it was ever committed or pasted in chat.
- JIRA tokens are as sensitive as passwords; treat the public URL like any
  internal tool — use Streamlit Cloud **private app** / team access if
  available.

---

## Custom domain (Streamlit Cloud)

Streamlit Cloud supports custom domains on paid / team plans. See
[Streamlit documentation](https://docs.streamlit.io/streamlit-community-cloud) for the current workflow.

---

## After deploy

- Open the **Library** tab: saved `test_cases/*.json` are part of the repo;
  each **Run** still calls **live JIRA**.
- If `test_cases/` is empty on first clone, create cases from **Build & Run**
  and commit the JSON files you want shared.
