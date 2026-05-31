#!/usr/bin/env python3
"""Audit script — every personality-agent run-log entry must satisfy the
four attribution invariants from spec 008 data-model.md E6 (SC-004 + SC-008):

  - ``display_name`` ends with ``" (simulated)"``.
  - ``model_kind == "personality_simulator"``.
  - ``model_name == "qwen.qwen3.5-122b"``.
  - ``agent_name == "personality"``.

Walks every JSONL file under ``state/run-log/`` and prints any
violations. Exits non-zero if any violations are found, zero otherwise.

Usage:
  python scripts/audit_personality_attribution.py
"""

from __future__ import annotations

import json
from pathlib import Path

EXPECTED_AGENT = "personality"
EXPECTED_MODEL = "qwen.qwen3.5-122b"
EXPECTED_KIND = "personality_simulator"
EXPECTED_SUFFIX = " (simulated)"


def audit(run_log_root: Path) -> tuple[int, int, list[dict[str, str]]]:
    """Walk every JSONL line in ``state/run-log/**/*.jsonl``.

    Returns ``(n_personality_entries, n_violations, violation_rows)``.
    A "personality entry" is one where ``agent_name == "personality"``.
    A "violation" is any such entry that fails one of the four invariants.
    """
    n_entries = 0
    violations: list[dict[str, str]] = []
    if not run_log_root.is_dir():
        return 0, 0, []
    for jsonl in run_log_root.rglob("*.jsonl"):
        for lineno, line in enumerate(jsonl.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("agent_name") != EXPECTED_AGENT:
                continue
            n_entries += 1
            problems = []
            if entry.get("model_name") != EXPECTED_MODEL:
                problems.append(f"model_name={entry.get('model_name')!r} (expected {EXPECTED_MODEL!r})")
            if entry.get("model_kind") != EXPECTED_KIND:
                problems.append(f"model_kind={entry.get('model_kind')!r} (expected {EXPECTED_KIND!r})")
            dn = entry.get("display_name") or ""
            # display_name MAY be None for tick-level failures (rate_limited
            # before persona was chosen, etc.). Only flag if a slug was
            # picked AND the display_name doesn't end with the suffix.
            if entry.get("personality_slug") and not dn.endswith(EXPECTED_SUFFIX):
                problems.append(f"display_name={dn!r} (expected ...' (simulated)')")
            if problems:
                violations.append({
                    "file": str(jsonl),
                    "line": str(lineno),
                    "personality_slug": entry.get("personality_slug", "<null>"),
                    "outcome": entry.get("outcome", "<null>"),
                    "problems": "; ".join(problems),
                })
    return n_entries, len(violations), violations


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    n_entries, n_violations, rows = audit(repo / "state" / "run-log")
    print(f"[audit_personality_attribution] scanned {n_entries} personality entries")
    if n_violations == 0:
        print("[audit_personality_attribution] OK: zero violations")
        return 0
    print(f"[audit_personality_attribution] FAIL: {n_violations} violation(s):")
    for r in rows:
        print(f"  {r['file']}:{r['line']} (slug={r['personality_slug']}, outcome={r['outcome']})")
        print(f"    {r['problems']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
