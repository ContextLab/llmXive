#!/usr/bin/env python3
"""One-time maintenance: drain the stranded ``[~]`` (under-review) task backlog.

The independent task-verifier historically consumed only ``DEFAULT_VERIFY_CAP``
LLM calls per tick while the implementer claimed up to ``IMPLEMENT_TASK_BATCH``
tasks — so everything past the cap was force-marked ``[~]`` and rarely re-visited.
Across the in_progress corpus that produced a large ``[~]`` backlog (issue #1139).

This script re-runs the NEW deterministic checks (LLM-FREE) over every in_progress
project's ``[~]`` tasks and reclassifies each:

  * ``[~]`` → ``[X]``  — its declared artifacts now exist and validate;
  * ``[~]`` → ``[ ]``  — a production task whose declared artifacts are missing
                          (recorded UNVERIFIABLE if it already hit REJECT_CAP);
  * ``[~]`` stays ``[~]`` — genuinely ambiguous (no detectable artifact path); it
                          still needs the semantic verifier on a later tick.

Default is DRY-RUN: it prints a per-project + total before/after count table and
writes nothing. Pass ``--apply`` to persist the reclassification.

Usage::

    PYTHONPATH=src python scripts/maintenance/drain_under_review.py           # dry-run
    PYTHONPATH=src python scripts/maintenance/drain_under_review.py --apply
    PYTHONPATH=src python scripts/maintenance/drain_under_review.py --project PROJ-552-foo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _fmt_counts(c: dict[str, int]) -> str:
    return f"X={c['X']:<4} open={c[' ']:<4} ~={c['~']:<4}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="write the reclassification to tasks.md (default: dry-run only)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=None,
        help="repository root (default: resolved via llmxive.config.repo_root)",
    )
    parser.add_argument(
        "--project", action="append", default=None, metavar="PROJ-ID",
        help="limit to specific project id(s); repeatable",
    )
    args = parser.parse_args(argv)

    from llmxive.agents.task_verifier import drain_under_review
    from llmxive.config import repo_root as _repo_root
    from llmxive.state import project as project_store
    from llmxive.state.project import feature_dir_for
    from llmxive.types import Stage

    root = args.repo_root.resolve() if args.repo_root else _repo_root()
    want = set(args.project) if args.project else None

    targets = [
        p for p in project_store.list_all(repo_root=root)
        if p.current_stage == Stage.IN_PROGRESS and (want is None or p.id in want)
    ]

    mode = "APPLY (writing)" if args.apply else "DRY-RUN (no writes)"
    print(f"drain_under_review — {mode}")
    print(f"repo root: {root}")
    print(f"in_progress projects considered: {len(targets)}\n")

    header = f"{'PROJECT':<34} {'BEFORE':<26} -> {'AFTER':<26} acc  reopen unv  amb"
    print(header)
    print("-" * len(header))

    tot_before = {"X": 0, " ": 0, "~": 0}
    tot_after = {"X": 0, " ": 0, "~": 0}
    tot_acc = tot_reopen = tot_unv = tot_amb = 0
    touched = 0

    for p in targets:
        project_dir = root / "projects" / p.id
        fdir = feature_dir_for(project_dir, track="research")
        if fdir is None:
            continue
        tasks_path = fdir / "tasks.md"
        if not tasks_path.is_file():
            continue
        try:
            if "- [~]" not in tasks_path.read_text(encoding="utf-8"):
                continue  # nothing under review — skip the deterministic sweep
        except OSError:
            continue
        try:
            res = drain_under_review(
                project_dir, tasks_path,
                project_id=p.id, repo_root=root, apply=args.apply,
            )
        except Exception as exc:  # one bad project must not abort the sweep
            print(f"{p.id:<34} ERROR: {type(exc).__name__}: {exc}")
            continue

        touched += 1
        for k in tot_before:
            tot_before[k] += res["before"][k]
            tot_after[k] += res["after"][k]
        tot_acc += res["accepted"]
        tot_reopen += res["reopened"]
        tot_unv += len(res["unverifiable"])
        tot_amb += res["ambiguous"]
        print(
            f"{p.id:<34} {_fmt_counts(res['before']):<26} -> "
            f"{_fmt_counts(res['after']):<26} "
            f"{res['accepted']:<4} {res['reopened']:<6} "
            f"{len(res['unverifiable']):<4} {res['ambiguous']}"
        )

    print("-" * len(header))
    print(
        f"{'TOTAL (' + str(touched) + ' projects w/ [~])':<34} "
        f"{_fmt_counts(tot_before):<26} -> {_fmt_counts(tot_after):<26} "
        f"{tot_acc:<4} {tot_reopen:<6} {tot_unv:<4} {tot_amb}"
    )
    if not args.apply:
        print("\n(dry-run — re-run with --apply to persist these changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
