"""Persist, load, and execute test cases.

A "test case" is a small JSON file describing one JIRA object pull plus
the assertions that must hold for the result to be considered a pass.

Schema::

    {
        "name": "Smoke: Pull Issues",
        "object": "Issues",                # name from objects.CATALOG
        "params": { "jql": "...", "maxResults": "25" },
        "assertions": {
            "min_records": 1,              # optional, default 0
            "max_records": null,           # optional, no upper bound when null
            "required_fields": ["key"]     # optional dotted paths checked on every record
        }
    }
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jira_client import JiraResponse, fetch
from objects import CATALOG, JiraObject

TEST_CASES_DIR = Path(__file__).parent / "test_cases"
TEST_CASES_DIR.mkdir(exist_ok=True)


@dataclass
class AssertionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class TestCaseRun:
    case_name: str
    object_name: str
    passed: bool
    record_count: int
    assertions: list[AssertionResult] = field(default_factory=list)
    response: JiraResponse | None = None
    started_at: str = ""
    duration_ms: int = 0


_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")


def _slugify(name: str) -> str:
    slug = _FILENAME_SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "test_case"


def list_cases() -> list[dict[str, Any]]:
    """Return all saved test cases, sorted by name."""
    cases: list[dict[str, Any]] = []
    for path in sorted(TEST_CASES_DIR.glob("*.json")):
        try:
            cases.append({"path": str(path), **json.loads(path.read_text())})
        except json.JSONDecodeError:
            continue
    return cases


def load_case(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def save_case(case: dict[str, Any]) -> Path:
    """Write a test case to disk under ``test_cases/<slug>.json``."""
    if "name" not in case or "object" not in case:
        raise ValueError("Test case requires both 'name' and 'object'.")
    if case["object"] not in CATALOG:
        raise ValueError(f"Unknown object: {case['object']}")

    payload = {
        "name": case["name"],
        "object": case["object"],
        "params": case.get("params", {}),
        "assertions": case.get("assertions", {}),
    }

    path = TEST_CASES_DIR / f"{_slugify(case['name'])}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def delete_case(path: str | Path) -> None:
    Path(path).unlink(missing_ok=True)


def _resolve_field(record: Any, dotted: str) -> Any:
    cur = record
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


def _evaluate_assertions(
    response: JiraResponse,
    assertions: dict[str, Any],
) -> list[AssertionResult]:
    results: list[AssertionResult] = []

    if not response.ok:
        results.append(
            AssertionResult(
                name="response_ok",
                passed=False,
                detail=response.error or f"HTTP {response.status_code}",
            )
        )
        return results

    results.append(
        AssertionResult(name="response_ok", passed=True, detail=f"HTTP {response.status_code}")
    )

    count = len(response.records)

    min_records = assertions.get("min_records")
    if min_records is not None:
        ok = count >= int(min_records)
        results.append(
            AssertionResult(
                name=f"min_records >= {min_records}",
                passed=ok,
                detail=f"got {count}",
            )
        )

    max_records = assertions.get("max_records")
    if max_records is not None:
        ok = count <= int(max_records)
        results.append(
            AssertionResult(
                name=f"max_records <= {max_records}",
                passed=ok,
                detail=f"got {count}",
            )
        )

    required_fields: list[str] = assertions.get("required_fields") or []
    for field_path in required_fields:
        if not response.records:
            results.append(
                AssertionResult(
                    name=f"required_field present: {field_path}",
                    passed=False,
                    detail="no records returned",
                )
            )
            continue
        missing_count = sum(
            1 for r in response.records if _resolve_field(r, field_path) is None
        )
        ok = missing_count == 0
        results.append(
            AssertionResult(
                name=f"required_field present: {field_path}",
                passed=ok,
                detail=("present on all records" if ok else f"missing on {missing_count} records"),
            )
        )

    return results


def run_case(case: dict[str, Any]) -> TestCaseRun:
    """Execute a test case and return a structured run result."""
    started = datetime.utcnow()
    object_name = case["object"]
    obj: JiraObject = CATALOG[object_name]

    params = {k: str(v) for k, v in (case.get("params") or {}).items() if v is not None and v != ""}

    response = fetch(obj, params)
    assertions = _evaluate_assertions(response, case.get("assertions") or {})
    duration_ms = int((datetime.utcnow() - started).total_seconds() * 1000)

    return TestCaseRun(
        case_name=case.get("name", "<unnamed>"),
        object_name=object_name,
        passed=all(a.passed for a in assertions) and response.ok,
        record_count=len(response.records) if response.ok else 0,
        assertions=assertions,
        response=response,
        started_at=started.isoformat(timespec="seconds") + "Z",
        duration_ms=duration_ms,
    )
