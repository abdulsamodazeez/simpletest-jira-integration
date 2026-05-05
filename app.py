"""Streamlit UI for the JIRA pull-objects prototype (live JIRA only).

Two main areas:

1. **Build & Run** — pick a JIRA object, parameters, assertions; run against
   your live site; optionally save the definition as JSON.
2. **Library** — lists those saved JSON files so you can **re-run** the same
   pull/assertion flow without rebuilding the form (handy for demos and
   regression checks). This is not mock data: each **Run** still calls JIRA.

Credentials: **sidebar** (*Apply connection*), **`.env`**, or **`st.secrets`**
(on Streamlit Community Cloud). See ``jira_client.configure_runtime``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parent


def _env_file_present() -> bool:
    return (_APP_DIR / ".env").is_file()

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import jira_client
from objects import CATALOG, list_object_names
from test_runner import (
    TestCaseRun,
    delete_case,
    list_cases,
    run_case,
    save_case,
)

st.set_page_config(
    page_title="JIRA lab",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _read_jira_setting(name: str) -> str:
    """Resolve a credential from the process environment or Streamlit secrets."""
    env_v = (os.getenv(name) or "").strip()
    if env_v:
        return env_v
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except (FileNotFoundError, KeyError, TypeError, AttributeError):
        pass
    return ""


def _seed_jira_sidebar_defaults_once() -> None:
    """Pre-fill sidebar fields from ``.env`` / ``st.secrets`` once per session."""
    if "_jira_sidebar_defaults_seeded" in st.session_state:
        return
    load_dotenv()
    st.session_state["jira_url"] = _read_jira_setting("JIRA_BASE_URL")
    st.session_state["jira_email"] = _read_jira_setting("JIRA_EMAIL")
    st.session_state["jira_token"] = _read_jira_setting("JIRA_API_TOKEN")
    st.session_state["_jira_sidebar_defaults_seeded"] = True


def _bootstrap_sidebar_applied_once() -> None:
    """If all three values exist (from env or secrets) and the user has not
    already toggled *Apply*, activate the runtime so hosted deploys work
    without an extra click.
    """
    if st.session_state.get("_jira_sidebar_bootstrap_done"):
        return
    st.session_state["_jira_sidebar_bootstrap_done"] = True
    if st.session_state.get("_jira_sidebar_applied"):
        return
    url = (st.session_state.get("jira_url") or "").strip()
    email = (st.session_state.get("jira_email") or "").strip()
    token = (st.session_state.get("jira_token") or "").strip()
    if url and email and token:
        st.session_state["_jira_sidebar_applied"] = True


def _sync_jira_runtime_from_session() -> None:
    """Push sidebar *Apply* state into ``jira_client`` every rerun."""
    if st.session_state.get("_jira_sidebar_applied"):
        jira_client.configure_runtime(
            base_url=st.session_state.get("jira_url", ""),
            email=st.session_state.get("jira_email", ""),
            api_token=st.session_state.get("jira_token", ""),
        )
    else:
        jira_client.clear_runtime_configuration()


def render_jira_sidebar() -> None:
    """Live JIRA URL / email / token — optional override of ``.env``."""
    st.sidebar.markdown("#### JIRA connection")
    st.sidebar.caption(
        "Enter your **JIRA Cloud** site URL, account email, and API token, then "
        "**Apply connection**. Fields can be pre-filled from **App secrets** "
        "(Streamlit Cloud) or a local **`.env`** file next to the app."
    )
    with st.sidebar.form("jira_credentials_form"):
        st.text_input(
            "Site URL",
            placeholder="https://your-site.atlassian.net",
            key="jira_url",
            help="Include https:// — same host as in the browser.",
        )
        st.text_input("Atlassian account email", key="jira_email")
        st.text_input(
            "API token",
            type="password",
            key="jira_token",
            help="id.atlassian.com → Security → API tokens",
        )
        submitted = st.form_submit_button("Apply connection")

    if submitted:
        url = (st.session_state.get("jira_url") or "").strip()
        email = (st.session_state.get("jira_email") or "").strip()
        token = (st.session_state.get("jira_token") or "").strip()
        if not (url and email and token):
            st.session_state["_jira_sidebar_applied"] = False
            st.sidebar.error("URL, email, and API token are all required.")
        else:
            st.session_state["_jira_sidebar_applied"] = True
            st.session_state.pop("_sidebar_whoami", None)
            st.sidebar.success("Credentials saved for this session.")

    if _env_file_present():
        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("Clear override", key="jira_btn_clear_override"):
                st.session_state["_jira_sidebar_applied"] = False
                st.session_state.pop("_sidebar_whoami", None)
                jira_client.clear_runtime_configuration()
                st.rerun()
        with c2:
            if st.button("Reload .env", key="jira_btn_reload_env"):
                load_dotenv(override=True)
                st.session_state["jira_url"] = _read_jira_setting("JIRA_BASE_URL")
                st.session_state["jira_email"] = _read_jira_setting("JIRA_EMAIL")
                st.session_state["jira_token"] = _read_jira_setting("JIRA_API_TOKEN")
                st.session_state["_jira_sidebar_applied"] = False
                st.session_state.pop("_sidebar_whoami", None)
                jira_client.clear_runtime_configuration()
                st.rerun()
    else:
        if st.sidebar.button("Clear override", key="jira_btn_clear_override"):
            st.session_state["_jira_sidebar_applied"] = False
            st.session_state.pop("_sidebar_whoami", None)
            jira_client.clear_runtime_configuration()
            st.rerun()

    if st.sidebar.button("Test connection", key="jira_btn_test_conn"):
        st.session_state["_sidebar_whoami"] = jira_client.whoami()

    who = st.session_state.get("_sidebar_whoami")
    if who is not None:
        if who.ok and who.records:
            u = who.records[0]
            st.sidebar.success(
                f"**{u.get('displayName', '?')}** · {u.get('emailAddress', '')}"
            )
        else:
            st.sidebar.error(who.error or "Connection test failed")


def _connection_status_banner() -> None:
    """Status strip at the top of the main area."""
    if jira_client.credentials_configured():
        st.success(
            "**Connected to JIRA successfully.** "
            f"Site: `{jira_client.base_url()}`",
            icon="✅",
        )
    else:
        st.warning(
            "**Not connected to JIRA yet.** "
            "Enter your site URL, email, and API token in the sidebar, then "
            "**Apply connection** — or set `JIRA_BASE_URL`, `JIRA_EMAIL`, and "
            "`JIRA_API_TOKEN` in `.env`.",
            icon="⚠️",
        )


def _records_to_dataframe(records: list[Any]) -> pd.DataFrame | None:
    if not records:
        return None
    try:
        return pd.json_normalize(records)
    except (TypeError, ValueError):
        try:
            return pd.DataFrame(records)
        except Exception:
            return None


def _render_run_result(run: TestCaseRun) -> None:
    summary_cols = st.columns(4)
    summary_cols[0].metric(
        "Result",
        "PASS" if run.passed else "FAIL",
        delta=None,
    )
    summary_cols[1].metric("Records", run.record_count)
    summary_cols[2].metric("HTTP", run.response.status_code if run.response else "-")
    summary_cols[3].metric("Duration", f"{run.duration_ms} ms")

    if not run.passed:
        st.error("Test case failed. See assertion details below.")
    else:
        st.success("Test case passed.")

    with st.expander("Assertions", expanded=True):
        for assertion in run.assertions:
            icon = ":white_check_mark:" if assertion.passed else ":x:"
            st.markdown(f"- {icon} **{assertion.name}** - {assertion.detail}")

    if run.response and run.response.url:
        st.caption(f"Request: `{run.response.url}`")

    if run.response and run.response.error:
        st.error(f"Upstream error: {run.response.error}")

    df = _records_to_dataframe(run.response.records if run.response else [])
    if df is not None and not df.empty:
        st.subheader("Records")
        st.dataframe(df, use_container_width=True)
    elif run.response and run.response.ok:
        st.info("Endpoint returned no records.")

    if run.response is not None:
        with st.expander("Raw response"):
            try:
                st.code(json.dumps(run.response.raw, indent=2, default=str), language="json")
            except (TypeError, ValueError):
                st.code(str(run.response.raw))


def render_build_run_tab() -> None:
    st.markdown("### Build & run a test case")
    st.caption("Pick a JIRA object, assert on the live response, save JSON to the Library.")

    object_names = list_object_names()
    default_index = object_names.index("Issues") if "Issues" in object_names else 0
    object_name = st.selectbox(
        "JIRA object",
        object_names,
        index=default_index,
        help="Objects aligned with the Salesforce Data Cloud JIRA Structured Connector catalog.",
    )
    obj = CATALOG[object_name]
    st.caption(obj.description)
    if obj.notes:
        st.info(obj.notes, icon="ℹ️")
    if not obj.cloud_supported:
        st.warning(
            "This object may not be available on JIRA Cloud with API token auth.",
            icon="⚠️",
        )

    with st.form("build_test_case"):
        case_name = st.text_input(
            "Test case name",
            value=f"Pull {object_name}",
            help="Used as the saved file name in the Library.",
        )

        st.markdown("**Parameters**")
        params: dict[str, str] = {}
        if obj.params:
            for param in obj.params:
                label = (
                    f"{param.name} ({'required' if param.required else 'optional'}) "
                    f"- {param.description}"
                )
                params[param.name] = st.text_input(
                    label,
                    value=param.default or "",
                    key=f"param_{object_name}_{param.name}",
                )
        else:
            st.caption("This object takes no parameters.")

        st.markdown("**Assertions**")
        a_cols = st.columns(3)
        min_records = a_cols[0].number_input(
            "min_records", min_value=0, value=1, step=1,
            help="Minimum records expected. Set to 0 to skip.",
        )
        max_records_enabled = a_cols[1].checkbox("Cap max_records", value=False)
        max_records = a_cols[1].number_input(
            "max_records", min_value=0, value=1000, step=10,
            disabled=not max_records_enabled,
        )
        required_fields_raw = st.text_input(
            "required_fields (comma-separated dotted paths)",
            value="",
            help="Example for Issues: key, fields.summary, fields.status.name",
        )
        required_fields = [
            f.strip() for f in required_fields_raw.split(",") if f.strip()
        ]

        st.caption(f"Request preview: `{jira_client.preview_url(obj, params)}`")

        run_clicked = st.form_submit_button("Run test case")
        save_clicked = st.form_submit_button("Save test case")

    case_payload = {
        "name": case_name,
        "object": object_name,
        "params": params,
        "assertions": {
            "min_records": int(min_records),
            **({"max_records": int(max_records)} if max_records_enabled else {}),
            "required_fields": required_fields,
        },
    }

    if run_clicked:
        with st.spinner(f"Pulling {object_name} from JIRA..."):
            run = run_case(case_payload)
        st.session_state["_last_run"] = run

    if save_clicked:
        try:
            path = save_case(case_payload)
            st.success(f"Saved test case to `{path.name}` — open the **Library** tab to run it again.")
        except ValueError as exc:
            st.error(str(exc))

    last_run: TestCaseRun | None = st.session_state.get("_last_run")
    if last_run is not None:
        st.divider()
        st.subheader(f"Last run — {last_run.case_name}")
        _render_run_result(last_run)


def render_library_tab() -> None:
    st.markdown("### Library")
    st.caption(
        "Each entry is a **saved test case** (JSON on disk): same object, params, "
        "and assertions you defined in *Build & Run*. **Run** calls **live JIRA** "
        "again — useful for demos and repeat checks."
    )

    cases = list_cases()
    if not cases:
        st.info("No saved test cases yet. Save one from the **Build & Run** tab.")
        return

    for case in cases:
        with st.expander(f"{case.get('name', '?')}  —  {case.get('object', '?')}"):
            st.code(json.dumps(
                {k: v for k, v in case.items() if k != "path"},
                indent=2,
            ), language="json")
            cols = st.columns([1, 1, 6])
            run_key = f"run_{case['path']}"
            del_key = f"del_{case['path']}"

            if cols[0].button("Run", key=run_key):
                with st.spinner(f"Running {case.get('name')}..."):
                    run = run_case(case)
                _render_run_result(run)

            if cols[1].button("Delete", key=del_key):
                delete_case(case["path"])
                st.success(f"Deleted {case.get('name')}.")
                st.rerun()


def main() -> None:
    _seed_jira_sidebar_defaults_once()
    _bootstrap_sidebar_applied_once()
    render_jira_sidebar()
    _sync_jira_runtime_from_session()
    _connection_status_banner()

    tab_build, tab_lib = st.tabs(["Build & Run", "Library"])
    with tab_build:
        with st.container(border=True):
            render_build_run_tab()
    with tab_lib:
        with st.container(border=True):
            render_library_tab()


if __name__ == "__main__":
    main()
