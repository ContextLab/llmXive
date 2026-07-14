"""One-time backfill of the monotonic execution-churn counters from git history.

``total_attempts`` and ``replan_rounds`` were added after the fact, so every existing
``state/execution_status/*.json`` reads 0 — which would blind BOTH new guards to the
churn that already happened: the scheduler's anti-monopoly penalty would not fire, and
a project that has already been round the ladder several times would be granted
MAX_REPLAN_ROUNDS *more* full ladders before being honestly rejected.

Git is the exact record. Each commit of a record is one execution attempt, so we
replay them:
  * an attempt with ``ok=false``            -> total_attempts += 1
  * ``fix_rounds`` dropping to 0 while the
    tier does NOT rise (the reset_fix_loop
    signature)                              -> replan_rounds += 1
  * ``ok=true``                             -> both counters reset (success is clean)

Idempotent: re-running recomputes from history rather than accumulating. Run from the
repo root:  python scripts/backfill_execution_churn_counters.py [--apply]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STATE = Path("state/execution_status")


def _history(path: Path) -> list[dict]:
    shas = subprocess.run(
        ["git", "log", "--format=%H", "--reverse", "--", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    out = []
    for sha in shas:
        blob = subprocess.run(
            ["git", "show", f"{sha}:{path}"], capture_output=True, text=True
        ).stdout
        try:
            out.append(json.loads(blob))
        except json.JSONDecodeError:
            continue
    return out


def replay(revisions: list[dict]) -> tuple[int, int]:
    """-> (total_attempts, replan_rounds) reconstructed from the record's history."""
    attempts = replans = 0
    prev_rounds = prev_tier = 0
    for rec in revisions:
        rounds = rec.get("fix_rounds") or 0
        tier = rec.get("model_tier") or 0
        if rec.get("ok") is True:
            attempts = replans = 0            # a clean run wipes the churn
        else:
            if rounds > prev_rounds:
                attempts += rounds - prev_rounds
            elif rounds < prev_rounds and tier <= prev_tier:
                # fix_rounds fell WITHOUT a tier bump => reset_fix_loop => a re-plan.
                replans += 1
                attempts += rounds           # the rounds accrued since the reset
        prev_rounds, prev_tier = rounds, tier
    return attempts, replans


def main() -> int:
    apply = "--apply" in sys.argv
    changed = 0
    for path in sorted(STATE.glob("*.json")):
        revs = _history(path)
        if not revs:
            continue
        attempts, replans = replay(revs)
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("ok") is True:
            attempts = replans = 0
        if rec.get("total_attempts") == attempts and rec.get("replan_rounds") == replans:
            continue
        print(
            f"{path.stem[:46]:48s} attempts={attempts:3d} replans={replans}"
            f"  (fix_rounds={rec.get('fix_rounds')} tier={rec.get('model_tier')})"
        )
        changed += 1
        if apply:
            rec["total_attempts"] = attempts
            rec["replan_rounds"] = replans
            path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"\n{changed} record(s) {'updated' if apply else 'would change (dry run)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
