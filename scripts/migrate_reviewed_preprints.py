#!/usr/bin/env python3
"""One-time migration of the 177 externally-ingested papers to Reviewed Preprints.

Ethics change (2026-07-01): before this, intake ran ``branch_code`` /
``branch_nocode`` which BACK-FILLED specs, revised the paper, and (for no-code)
transformed the project into a brainstormed follow-up with the original byline
dropped — i.e. llmXive MODIFIED third-party work and presented it (often still
crediting the original authors) without consent. The 177 intakes are now spread
across every pipeline stage as a result.

This script REVERTS each intake to a clean **Reviewed Preprint** by:

  1. discarding llmXive's scaffolding — ``paper/source/*-llmxive.*``,
     ``paper/pdf/*-llmxive.*`` (+ their aux), the back-filled ``specs/`` dirs,
     the stale ``paper/reviews/`` (they reviewed the MODIFIED paper),
     ``paper/revision_history.yaml``, ``upstream_feedback.yaml``, and the
     transformed ``idea/*.md`` follow-up;
  2. preserving the ORIGINAL work byte-for-byte — ``paper/source`` (minus the
     ``*-llmxive`` files), the original ``paper/pdf``/``metadata.json`` (original
     authors intact; recovered from git for the rare project whose byline was
     dropped);
  3. resetting project state to a clean ``paper_ingested`` (clearing the speckit
     dirs / revision fields / points), so the LIVE pipeline — whose
     ``PAPER_INGESTED`` handler now calls ``finalize_reviewed_preprint`` — marks
     it a terminal Reviewed Preprint, auto-reviews it once, spawns the separate
     citing follow-up, and builds the two themed PDFs, ONE project per tick
     (natural load-balancing; SSoT with the production path).

``code/`` and ``data/`` are NOT auto-deleted (they may be the original authors'
code added as a git submodule); the dry-run flags them for manual review.

USAGE:
    python scripts/migrate_reviewed_preprints.py --dry-run          # report only
    python scripts/migrate_reviewed_preprints.py --dry-run --details # + per-project
    python scripts/migrate_reviewed_preprints.py --execute --confirm [--limit N]

``--execute`` REFUSES to run without ``--confirm`` — eyeball the dry-run first.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Allow running as a plain script (repo-root/scripts/...).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llmxive.config import repo_root as _repo_root
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@dataclass
class MigrationPlan:
    project_id: str
    current_stage: str
    title: str
    original_authors: list[str]
    authors_dropped: bool  # metadata.json authors empty (byline was dropped)
    discard: list[str] = field(default_factory=list)  # repo-relative paths (auto)
    review_manually: list[str] = field(default_factory=list)  # code/ data/ (submodules)


def _intake_project_dirs(repo: Path) -> list[Path]:
    """Every project dir carrying an ingested ``paper/metadata.json``."""
    return sorted(
        d for d in (repo / "projects").glob("PROJ-*")
        if (d / "paper" / "metadata.json").is_file()
    )


def _load_metadata(pdir: Path) -> dict:
    try:
        data = json.loads((pdir / "paper" / "metadata.json").read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def build_plan(project: Project, pdir: Path, repo: Path) -> MigrationPlan:
    meta = _load_metadata(pdir)
    authors = [str(a).strip() for a in (meta.get("authors") or []) if str(a).strip()]
    rel = lambda p: p.relative_to(repo).as_posix()  # noqa: E731

    discard: list[str] = []
    source = pdir / "paper" / "source"
    if source.is_dir():
        discard += [rel(p) for p in sorted(source.glob("*-llmxive.*"))]
    pdf = pdir / "paper" / "pdf"
    if pdf.is_dir():
        discard += [rel(p) for p in sorted(pdf.glob("*-llmxive.*"))]
    for sub in ("specs", "paper/reviews"):
        d = pdir / sub
        if d.is_dir() and any(d.iterdir()):
            discard.append(rel(d))
    for fn in ("paper/revision_history.yaml", "upstream_feedback.yaml"):
        f = pdir / fn
        if f.is_file():
            discard.append(rel(f))
    idea = pdir / "idea"
    if idea.is_dir():
        discard += [rel(p) for p in sorted(idea.glob("*.md"))]

    review_manually: list[str] = []
    for sub in ("code", "data"):
        d = pdir / sub
        if d.is_dir() and any(d.iterdir()):
            review_manually.append(rel(d))

    return MigrationPlan(
        project_id=project.id,
        current_stage=project.current_stage.value,
        title=str(meta.get("title") or project.title or "")[:80],
        original_authors=authors,
        authors_dropped=not authors,
        discard=discard,
        review_manually=review_manually,
    )


def _recover_authors_from_git(repo: Path, pid: str) -> list[str]:
    """Recover the original author list from the earliest git version of
    ``metadata.json`` that still had a non-empty ``authors`` array."""
    relpath = f"projects/{pid}/paper/metadata.json"
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--format=%H", "--", relpath],
        capture_output=True, text=True,
    )
    # Oldest first — the pre-modification version.
    for sha in reversed(log.stdout.split()):
        show = subprocess.run(
            ["git", "-C", str(repo), "show", f"{sha}:{relpath}"],
            capture_output=True, text=True,
        )
        if show.returncode != 0:
            continue
        try:
            data = json.loads(show.stdout)
        except json.JSONDecodeError:
            continue
        authors = [str(a).strip() for a in (data.get("authors") or []) if str(a).strip()]
        if authors:
            return authors
    return []


def execute_plan(plan: MigrationPlan, project: Project, pdir: Path, repo: Path) -> None:
    """Revert ONE project to a clean ``paper_ingested`` Reviewed Preprint."""
    # 1. Restore dropped authors from git (the rare byline-dropped case).
    if plan.authors_dropped:
        recovered = _recover_authors_from_git(repo, plan.project_id)
        if recovered:
            meta_path = pdir / "paper" / "metadata.json"
            meta = _load_metadata(pdir)
            meta["authors"] = recovered
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    # 2. Discard llmXive's scaffolding (files + dirs).
    for relpath in plan.discard:
        target = repo / relpath
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink(missing_ok=True)

    # 3. Reset project state to a clean paper_ingested — the LIVE pipeline's
    #    PAPER_INGESTED handler (finalize_reviewed_preprint) does the rest.
    reverted = project.model_copy(update={
        "current_stage": Stage.PAPER_INGESTED,
        "speckit_research_dir": None,
        "speckit_paper_dir": None,
        "revision_spec_path": None,
        "revision_round": 0,
        "failed_stage": None,
        "human_escalation_reason": None,
        "points_research": {},
        "points_paper": {},
        "updated_at": datetime.now(UTC),
    })
    project_store.save(reverted, repo_root=repo)


def _print_report(plans: list[MigrationPlan], *, details: bool) -> None:
    from collections import Counter

    stages = Counter(p.current_stage for p in plans)
    total_discard = sum(len(p.discard) for p in plans)
    with_code = [p for p in plans if p.review_manually]
    dropped = [p for p in plans if p.authors_dropped]

    print("=" * 72)
    print(f"REVIEWED-PREPRINTS MIGRATION — DRY RUN ({len(plans)} intake projects)")
    print("=" * 72)
    print("\nCurrent stage distribution (all will revert to paper_ingested):")
    for stage, n in stages.most_common():
        print(f"  {n:4d}  {stage}")
    print(f"\nTotal llmXive-scaffolding artifacts to discard: {total_discard}")
    print(f"Projects with code/ or data/ to REVIEW MANUALLY (possible submodule): {len(with_code)}")
    print(f"Projects whose byline was dropped (authors recovered from git): {len(dropped)}")
    for p in dropped:
        print(f"    - {p.project_id}")
    print("\nAfter revert, the live pipeline (PAPER_INGESTED handler) will, per project:")
    print("  mark it a terminal Reviewed Preprint (never modified),")
    print("  auto-review it once, spawn a SEPARATE citing follow-up, build both PDFs.")

    if details:
        print("\n" + "-" * 72)
        for p in plans:
            print(f"\n{p.project_id}  [{p.current_stage}]")
            print(f"  title: {p.title}")
            print(f"  original authors: {', '.join(p.original_authors) or '(DROPPED — recover from git)'}")
            if p.discard:
                print(f"  discard ({len(p.discard)}):")
                for d in p.discard:
                    print(f"    - {d}")
            if p.review_manually:
                print(f"  REVIEW MANUALLY (possible submodule): {', '.join(p.review_manually)}")
    print("\n" + "=" * 72)
    print("This was a DRY RUN — nothing changed. Re-run with --execute --confirm to apply.")
    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="report what would change; change nothing")
    mode.add_argument("--execute", action="store_true", help="apply the reversion (requires --confirm)")
    ap.add_argument("--confirm", action="store_true", help="required with --execute; you have eyeballed the dry-run")
    ap.add_argument("--details", action="store_true", help="dry-run: print per-project detail")
    ap.add_argument("--limit", type=int, default=None, help="process only the first N projects (deterministic, resumable)")
    ap.add_argument("--json-out", type=Path, default=None, help="also write the full plan list as JSON")
    args = ap.parse_args(argv)

    repo = _repo_root()
    projects = {p.id: p for p in project_store.list_all(repo_root=repo)}
    plans: list[tuple[MigrationPlan, Project, Path]] = []
    for pdir in _intake_project_dirs(repo):
        proj = projects.get(pdir.name)
        if proj is None:
            continue
        plans.append((build_plan(proj, pdir, repo), proj, pdir))
    plans.sort(key=lambda t: t[0].project_id)
    if args.limit is not None:
        plans = plans[: args.limit]

    plan_list = [p for p, _, _ in plans]
    if args.json_out:
        args.json_out.write_text(
            json.dumps([p.__dict__ for p in plan_list], indent=2), encoding="utf-8"
        )

    if args.dry_run:
        _print_report(plan_list, details=args.details)
        return 0

    # --execute
    if not args.confirm:
        print(
            "REFUSING to execute without --confirm.\n"
            "Run `--dry-run` first, eyeball the report, then re-run with "
            "`--execute --confirm` (optionally `--limit N` to stage the rollout).",
            file=sys.stderr,
        )
        return 2
    n = 0
    for plan, proj, pdir in plans:
        execute_plan(plan, proj, pdir, repo)
        n += 1
        print(f"reverted {plan.project_id} -> paper_ingested "
              f"({len(plan.discard)} artifacts discarded)")
    print(f"\nReverted {n} projects to paper_ingested. The pipeline will now "
          "process each into a Reviewed Preprint + follow-up + PDFs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
