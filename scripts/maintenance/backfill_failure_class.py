#!/usr/bin/env python
"""One-time migration: backfill the durable ``failure_class`` on legacy
execution-status records.

Issue #1139 (P1-2) made :func:`llmxive.state.execution_status.record` persist a
durable :class:`llmxive.execution.failure_class.FailureClass` on every failed
execution attempt, so downstream re-plan feedback and terminal routing branch on
the REAL cause instead of re-parsing ``reason``/``failures`` strings. But the ~44
of 48 live records that predate the fix have no ``failure_class`` key (or a null
one), so class-specific routing is INERT for them until each project re-executes.

This script upgrades those records IN PLACE. For each
``state/execution_status/*.json`` with ``ok == false`` and a missing/null
``failure_class``, it reconstructs the class with the SAME logic the live path
uses (:mod:`llmxive.execution.stage`'s ``_compute_infra_failures`` /
``_data_unavailable_failures`` signature matchers + fabrication/hollow detection),
calls :meth:`FailureClass.from_signals`, and writes ``failure_class`` + ``evidence``
via the shared atomic writer. Records with ``ok == true`` — or that already carry a
non-null ``failure_class`` — are left untouched (the migration is idempotent).

DEFAULT is a DRY-RUN (nothing written). Pass ``--apply`` to write. Run with
``PYTHONPATH=src``::

    ./.venv/bin/python scripts/maintenance/backfill_failure_class.py            # dry-run
    ./.venv/bin/python scripts/maintenance/backfill_failure_class.py --apply    # write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llmxive.config import repo_root as _repo_root
from llmxive.execution.failure_class import FailureClass
from llmxive.execution.stage import _compute_infra_failures, _data_unavailable_failures
from llmxive.state._io import atomic_write_text


def _reconstruct(rec: dict) -> tuple[str, list[str]]:
    """Reconstruct ``(failure_class, evidence)`` from a stored record using the
    SAME signature logic the live execution path uses.

    ``_compute_infra_failures`` / ``_data_unavailable_failures`` run over the
    persisted ``failures`` list AND the ``reason`` string (a legacy record may
    carry the signal in either), and fabrication/hollow are read off the
    ``reason`` text (the live path had the SemanticGate booleans, which the
    ``SemanticGate.reason()`` prose faithfully reflects: "fabricated/simulated"
    and "hollow-result")."""
    reason = str(rec.get("reason", "") or "")
    failures = [str(f) for f in (rec.get("failures") or [])]
    signals = [*failures, reason]
    infra = _compute_infra_failures(signals)
    dataunavail = _data_unavailable_failures(signals)
    fclass = FailureClass.from_signals(
        compute_infra=bool(infra),
        data_unavailable=bool(dataunavail),
        fabrication="fabricat" in reason.lower(),
        hollow="hollow" in reason.lower(),
        has_command_failures=bool(failures),
    )
    evidence = (infra + dataunavail)[:20]
    return fclass.value, evidence


def _needs_backfill(rec: dict) -> bool:
    """A failed record with no (or null) ``failure_class`` — the only kind we
    touch. ok=true records and records already classified are left alone."""
    return rec.get("ok") is not True and not rec.get("failure_class")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="write the backfilled records (default: dry-run, no writes)",
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="repo root (default: llmxive.config.repo_root())",
    )
    args = parser.parse_args(argv)

    repo = Path(args.repo_root) if args.repo_root else _repo_root()
    status_dir = repo / "state" / "execution_status"
    files = sorted(status_dir.glob("*.json"))
    if not files:
        print(f"[backfill] no records under {status_dir}")
        return 0

    rows: list[tuple[str, str, list[str]]] = []  # (project_id, new_class, evidence)
    skipped_ok = 0
    skipped_classified = 0
    for path in files:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"[backfill] SKIP {path.name}: unreadable ({exc})", file=sys.stderr)
            continue
        if rec.get("ok") is True:
            skipped_ok += 1
            continue
        if rec.get("failure_class"):
            skipped_classified += 1
            continue
        if not _needs_backfill(rec):
            continue
        new_class, evidence = _reconstruct(rec)
        rows.append((path.name, new_class, evidence))
        if args.apply:
            rec["failure_class"] = new_class
            rec["evidence"] = [str(e)[:600] for e in evidence][:20]
            atomic_write_text(path, json.dumps(rec, indent=2) + "\n")

    hdr = f"{'record':<40} {'old':<10} -> {'new class':<18} {'evidence'}"
    print(f"\n{'DRY-RUN (no writes) — ' if not args.apply else 'APPLYING — '}"
          f"{len(rows)} record(s) to backfill under {status_dir}\n")
    print(hdr)
    print("-" * len(hdr))
    class_hist: dict[str, int] = {}
    for name, new_class, evidence in rows:
        class_hist[new_class] = class_hist.get(new_class, 0) + 1
        ev = (evidence[0][:40] + "…") if evidence else "-"
        print(f"{name:<40} {'(none)':<10} -> {new_class:<18} {ev}")

    print("\nby class:")
    for cls, n in sorted(class_hist.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {cls:<20} {n}")
    print(
        f"\nskipped: {skipped_ok} ok=true, {skipped_classified} already-classified."
    )
    if args.apply:
        print(f"\n[backfill] wrote {len(rows)} backfilled record(s).")
    else:
        print("\n[backfill] dry-run only; re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
