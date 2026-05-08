#!/usr/bin/env python3
"""Emit objects.CATALOG as JSON for the Next.js app (run from repo root)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repo root is on path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from objects import CATALOG  # noqa: E402


def main() -> None:
    out: list[dict] = []
    for name in sorted(CATALOG):
        o = CATALOG[name]
        out.append(
            {
                "name": o.name,
                "description": o.description,
                "endpoint": o.endpoint,
                "api": o.api,
                "response_path": o.response_path,
                "notes": o.notes,
                "cloud_supported": o.cloud_supported,
                "params": [
                    {
                        "name": p.name,
                        "description": p.description,
                        "required": p.required,
                        "placement": p.placement,
                        "default": p.default,
                    }
                    for p in o.params
                ],
            }
        )
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
