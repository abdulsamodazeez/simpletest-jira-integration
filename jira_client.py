"""HTTP client for JIRA Cloud REST APIs (live only).

Credentials come from the Streamlit sidebar (*Apply connection*) or from
``JIRA_BASE_URL``, ``JIRA_EMAIL``, ``JIRA_API_TOKEN`` in the process
environment / ``.env``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

load_dotenv()

PLATFORM_API_BASE = "/rest/api/3"
AGILE_API_BASE = "/rest/agile/1.0"
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass
class _RuntimeCredentials:
    base_url: str
    email: str
    api_token: str


_runtime_creds: _RuntimeCredentials | None = None


def configure_runtime(
    base_url: str | None = None,
    email: str | None = None,
    api_token: str | None = None,
) -> None:
    """Apply JIRA settings from the Streamlit sidebar after *Apply connection*.

    All three values must be non-empty (after strip). Otherwise runtime
    override is cleared and ``.env`` is used on the next read.
    """
    global _runtime_creds
    bu = (base_url or "").strip().rstrip("/")
    em = (email or "").strip()
    tok = (api_token or "").strip()
    if bu and em and tok:
        _runtime_creds = _RuntimeCredentials(bu, em, tok)
    else:
        _runtime_creds = None


def clear_runtime_configuration() -> None:
    """Remove sidebar overrides; use ``.env`` / environment only."""
    global _runtime_creds
    _runtime_creds = None


@dataclass
class JiraResponse:
    """Outcome of a single JIRA call."""

    ok: bool
    status_code: int
    records: list[Any]
    raw: Any
    url: str
    error: str | None = None


def credentials_configured() -> bool:
    """True when URL + email + token are available (sidebar or ``.env``)."""
    if _runtime_creds:
        return True
    return all(
        os.getenv(var)
        for var in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
    )


def base_url() -> str:
    if _runtime_creds:
        return _runtime_creds.base_url.rstrip("/")
    return (os.getenv("JIRA_BASE_URL") or "").rstrip("/")


def _auth_tuple() -> tuple[str, str]:
    if _runtime_creds:
        return (_runtime_creds.email, _runtime_creds.api_token)
    return (os.getenv("JIRA_EMAIL", ""), os.getenv("JIRA_API_TOKEN", ""))


def _resolve_path(value: Any, dotted_key: str) -> Any:
    cur: Any = value
    for part in dotted_key.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return cur


def _normalize_records(payload: Any, response_path: str | None) -> list[Any]:
    if response_path:
        extracted = _resolve_path(payload, response_path)
        if extracted is None:
            return []
        return extracted if isinstance(extracted, list) else [extracted]

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("values", "issues", "records"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return [payload]


def _resolve_endpoint(template: str, params: dict[str, str]) -> str:
    out = template
    for key, value in params.items():
        token = "{" + key + "}"
        if token in out:
            out = out.replace(token, str(value))
    return out


def fetch(jira_object, params: dict[str, str] | None = None) -> JiraResponse:
    """Execute a GET for the given catalog object against live JIRA."""
    params = dict(params or {})

    if not credentials_configured():
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url="",
            error=(
                "JIRA is not configured. Enter URL, email, and API token in the "
                "sidebar and click **Apply connection**, or set JIRA_* in `.env`."
            ),
        )

    return _fetch_live(jira_object, params)


def _fetch_live(jira_object, params: dict[str, str]) -> JiraResponse:
    path_params = {p.name: params.get(p.name, "") for p in jira_object.params if p.placement == "path"}
    query_params = {
        p.name: params.get(p.name, p.default)
        for p in jira_object.params
        if p.placement == "query" and (params.get(p.name) or p.default)
    }

    missing = [name for name, value in path_params.items() if not value]
    if missing:
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url="",
            error=f"Missing required path parameter(s): {', '.join(missing)}",
        )

    resolved_endpoint = _resolve_endpoint(jira_object.endpoint, path_params)
    api_base = AGILE_API_BASE if jira_object.api == "agile" else PLATFORM_API_BASE
    url = urljoin(base_url() + "/", (api_base + resolved_endpoint).lstrip("/"))

    auth = _auth_tuple()
    headers = {"Accept": "application/json"}

    try:
        resp = requests.get(
            url,
            params=query_params or None,
            auth=auth,
            headers=headers,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url=url,
            error=f"Network error: {exc}",
        )

    payload: Any
    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.ok:
        return JiraResponse(
            ok=False,
            status_code=resp.status_code,
            records=[],
            raw=payload,
            url=resp.url,
            error=f"HTTP {resp.status_code}",
        )

    records = _normalize_records(payload, jira_object.response_path)

    if jira_object.name == "IssueCustomFields" and isinstance(records, list):
        records = [r for r in records if isinstance(r, dict) and r.get("custom") is True]

    return JiraResponse(
        ok=True,
        status_code=resp.status_code,
        records=records,
        raw=payload,
        url=resp.url,
    )


def preview_url(jira_object, params: dict[str, str] | None = None) -> str:
    """Render the URL the client would call. For UI display only."""
    params = dict(params or {})
    path_params = {
        p.name: params.get(p.name) or f"<{p.name}>"
        for p in jira_object.params
        if p.placement == "path"
    }
    resolved = _resolve_endpoint(jira_object.endpoint, path_params)
    api_base = AGILE_API_BASE if jira_object.api == "agile" else PLATFORM_API_BASE
    site = base_url() or "https://your-site.atlassian.net"
    url = site + api_base + resolved
    qp = {
        p.name: params.get(p.name, p.default)
        for p in jira_object.params
        if p.placement == "query" and (params.get(p.name) or p.default)
    }
    if qp:
        url += "?" + "&".join(f"{k}={v}" for k, v in qp.items())
    return url


def whoami() -> JiraResponse:
    """Verify credentials by calling ``GET /rest/api/3/myself``."""
    if not credentials_configured():
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url="",
            error=(
                "JIRA credentials are missing. Use the sidebar (*Apply connection*) "
                "or set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in `.env`."
            ),
        )

    bu = base_url()
    if not bu:
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url="",
            error="JIRA site URL is missing. Set it in the sidebar or JIRA_BASE_URL in `.env`.",
        )

    url = bu + PLATFORM_API_BASE + "/myself"
    try:
        resp = requests.get(
            url,
            auth=_auth_tuple(),
            headers={"Accept": "application/json"},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return JiraResponse(
            ok=False,
            status_code=0,
            records=[],
            raw=None,
            url=url,
            error=f"Network error: {exc}",
        )

    try:
        payload = resp.json()
    except ValueError:
        payload = resp.text

    if not resp.ok:
        return JiraResponse(
            ok=False,
            status_code=resp.status_code,
            records=[],
            raw=payload,
            url=resp.url,
            error=f"HTTP {resp.status_code}",
        )

    return JiraResponse(
        ok=True,
        status_code=resp.status_code,
        records=[payload],
        raw=payload,
        url=resp.url,
    )
