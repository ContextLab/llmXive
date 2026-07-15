#!/usr/bin/env python
"""One-time migration: classify the existing untyped advance-error ledger.

Issue #1139 (defect D5) replaced the untyped ``state/advance_errors/<id>.json``
log (``{project_id, stage, last_error, last_seen, count}``) with a typed control
record that the scheduler honours (see :mod:`llmxive.pipeline.advance_ledger`).
This script upgrades the ~74 legacy records IN PLACE: it fingerprints each stored
``last_error`` into one of the nine real classes, carries the old ``count`` over as
``consecutive_count``, assigns the control disposition (class + status +
retry_after), and prints a before/after table (worst offenders first, so the four
``count >= 10`` records — PROJ-077=365, PROJ-770=91, PROJ-047=84, PROJ-362=76 —
lead the report).

DEFAULT is a DRY-RUN (nothing written). Pass ``--apply`` to write the upgraded
records. Run with ``PYTHONPATH=src``::

    ./.venv/bin/python scripts/maintenance/classify_advance_errors.py            # dry-run
    ./.venv/bin/python scripts/maintenance/classify_advance_errors.py --apply    # write
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.pipeline import advance_ledger as al
from llmxive.state._io import atomic_write_text


def _parse_dt(value: str | None) -> datetime:
    if value:
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            pass
    return datetime.now(UTC)


def _upgrade(old: dict) -> dict:
    """Build the typed record from a legacy (or already-typed) record."""
    message = old.get("last_error", "") or ""
    # Legacy schema used ``count``; a re-run over an already-typed record uses
    # ``consecutive_count`` — accept either so the migration is idempotent.
    count = int(old.get("consecutive_count", old.get("count", 1)) or 1)
    last_seen = _parse_dt(old.get("last_seen"))
    first_seen = old.get("first_seen") or (old.get("last_seen") or last_seen.isoformat())
    return al.make_record(
        project_id=old.get("project_id", ""),
        stage=old.get("stage", ""),
        message=message,
        consecutive_count=count,
        first_seen=first_seen,
        last_seen=last_seen,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="write the upgraded records (default: dry-run, no writes)",
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="repo root (default: llmxive.config.repo_root())",
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo_root) if args.repo_root else _repo_root()
    ledger_dir = repo.joinpath(*al.LEDGER_SUBDIR)
    files = sorted(ledger_dir.glob("*.json"))
    if not files:
        print(f"[classify] no records under {ledger_dir}")
        return 0

    rows: list[tuple[int, str, dict, dict]] = []
    for path in files:
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"[classify] SKIP {path.name}: unreadable ({exc})", file=sys.stderr)
            continue
        new = _upgrade(old)
        count = int(old.get("consecutive_count", old.get("count", 1)) or 1)
        rows.append((count, path.name, old, new))

    # Worst offenders (highest count) first.
    rows.sort(key=lambda r: (-r[0], r[1]))

    hdr = f"{'count':>5}  {'stage':<18} {'fingerprint':<22} {'class':<20} {'status'}"
    print(f"\n{'DRY-RUN (no writes) — ' if not args.apply else 'APPLYING — '}"
          f"{len(rows)} record(s) under {ledger_dir}\n")
    print(hdr)
    print("-" * len(hdr))
    class_hist: dict[str, int] = {}
    written = 0
    for count, name, _old, new in rows:
        class_hist[new["class"]] = class_hist.get(new["class"], 0) + 1
        print(
            f"{count:>5}  {new['stage']:<18} {new['fingerprint']:<22} "
            f"{new['class']:<20} {new['status']}"
        )
        if args.apply:
            atomic_write_text(ledger_dir / name, json.dumps(new, indent=2))
            written += 1

    print("\nby class:")
    for cls, n in sorted(class_hist.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {cls:<20} {n}")
    if args.apply:
        print(f"\n[classify] wrote {written} upgraded record(s).")
    else:
        print("\n[classify] dry-run only; re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
