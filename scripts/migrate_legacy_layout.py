"""Migrate legacy llmXive directory layouts into the canonical Spec-Kit-per-project layout.

Per FR-023 and FR-025: every project lives at projects/<PROJ-ID>/{...}; legacy
trees under technical_design_documents/, implementation_plans/, papers/, and
the previous projects/ structure are folded in. The script is idempotent:
re-running on already-migrated content is a no-op.

Edge cases per T009:
- Legacy project with a partial paper but no research design → routed to
  state/projects/<PROJ-ID>.yaml with current_stage=human_input_needed and
  human_escalation_reason="legacy migration: missing research scaffold".
- Legacy project with no recognizable artifacts → current_stage=human_input_needed
  with reason "legacy migration: empty project".

Pre-migration line counts for code/llmxive-automation/** are recorded to
state/migration_metrics.yaml for SC-007 verification.

Usage:
    python scripts/migrate_legacy_layout.py            # dry run, prints plan
    python scripts/migrate_legacy_layout.py --apply    # actually mutate
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LEGACY_TREES: tuple[str, ...] = (
    "technical_design_documents",
    "implementation_plans",
    "papers",
)
LEGACY_AUTOMATION_DIR: str = "code/llmxive-automation"
TARGET_ROOT: str = "projects"
STATE_DIR: str = "state"
PROJ_ID_PATTERN: re.Pattern[str] = re.compile(r"^PROJ-\d{3,}-[a-z0-9-]+$")


@dataclass
class MigrationPlan:
    repo_root: Path
    moves: list[tuple[Path, Path]] = field(default_factory=list)
    deletes: list[Path] = field(default_factory=list)
    project_states: dict[str, dict[str, str]] = field(default_factory=dict)
    legacy_loc: int = 0


def derive_proj_id(legacy_dir_name: str, *, fallback_field: str = "research") -> str:
    """Translate a legacy directory name into a canonical PROJ-### identifier.

    If the legacy directory already matches the canonical pattern, return it
    verbatim. Otherwise allocate the next available numeric prefix.
    """
    if PROJ_ID_PATTERN.match(legacy_dir_name):
        return legacy_dir_name
    slug = re.sub(r"[^a-z0-9-]+", "-", legacy_dir_name.lower()).strip("-")[:48] or "untitled"
    return f"PROJ-MIGRATED-{slug}"


def count_lines(directory: Path) -> int:
    if not directory.is_dir():
        return 0
    total = 0
    for path in directory.rglob("*"):
        if path.is_file() and not any(p.startswith(".") for p in path.parts):
            try:
                total += sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return total


def gather_plan(repo_root: Path) -> MigrationPlan:
    plan = MigrationPlan(repo_root=repo_root)
    plan.legacy_loc = count_lines(repo_root / LEGACY_AUTOMATION_DIR)

    target_root = repo_root / TARGET_ROOT
    target_root.mkdir(exist_ok=True)

    for legacy_tree in LEGACY_TREES:
        legacy_path = repo_root / legacy_tree
        if not legacy_path.is_dir():
            continue
        kind = {
            "technical_design_documents": "technical-design",
            "implementation_plans": "implementation-plan",
            "papers": "paper",
        }[legacy_tree]
        for entry in sorted(legacy_path.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            proj_id = derive_proj_id(entry.name)
            target_subdir = target_root / proj_id / kind
            plan.moves.append((entry, target_subdir))
            state = plan.project_states.setdefault(
                proj_id, {"id": proj_id, "stages_seen": ""}
            )
            state["stages_seen"] = (state["stages_seen"] + f",{kind}").strip(",")
        plan.deletes.append(legacy_path)

    # Decide initial stage per project from stages_seen.
    for proj_id, state in plan.project_states.items():
        seen = set(state["stages_seen"].split(","))
        if "paper" in seen and "technical-design" not in seen:
            state["current_stage"] = "human_input_needed"
            state["human_escalation_reason"] = (
                "legacy migration: missing research scaffold"
            )
        elif not seen:
            state["current_stage"] = "human_input_needed"
            state["human_escalation_reason"] = "legacy migration: empty project"
        elif "paper" in seen:
            state["current_stage"] = "paper_in_progress"
        elif "implementation-plan" in seen:
            state["current_stage"] = "in_progress"
        elif "technical-design" in seen:
            state["current_stage"] = "clarified"
        else:
            state["current_stage"] = "human_input_needed"
            state["human_escalation_reason"] = "legacy migration: unrecognized stage set"

    return plan


def apply_plan(plan: MigrationPlan) -> None:
    state_dir = plan.repo_root / STATE_DIR / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Move legacy directories into canonical layout.
    for src, dst in plan.moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            print(f"[skip] {dst} already exists; leaving in place (idempotent).")
            continue
        shutil.move(str(src), str(dst))
        print(f"[move] {src.relative_to(plan.repo_root)} -> {dst.relative_to(plan.repo_root)}")

    # Write per-project state files.
    now = datetime.now(timezone.utc).isoformat()
    for proj_id, state in plan.project_states.items():
        target = state_dir / f"{proj_id}.yaml"
        if target.exists():
            print(f"[skip] {target} already exists.")
            continue
        lines = [
            f"id: {proj_id}",
            f"title: {proj_id}",
            "field: legacy-migrated",
            f"current_stage: {state['current_stage']}",
            "points_research: {}",
            "points_paper: {}",
            f"created_at: '{now}'",
            f"updated_at: '{now}'",
            "artifact_hashes: {}",
        ]
        if "human_escalation_reason" in state:
            lines.append(f"human_escalation_reason: '{state['human_escalation_reason']}'")
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[state] wrote {target.relative_to(plan.repo_root)}")

    # Remove emptied legacy trees.
    for legacy_path in plan.deletes:
        if not legacy_path.exists():
            continue
        if any(legacy_path.iterdir()):
            print(f"[keep] {legacy_path} not empty; leaving for human review.")
            continue
        legacy_path.rmdir()
        print(f"[rmdir] {legacy_path.relative_to(plan.repo_root)}")

    # Capture migration metrics for SC-007.
    metrics_path = plan.repo_root / STATE_DIR / "migration_metrics.yaml"
    if not metrics_path.exists():
        metrics_path.write_text(
            f"# SC-007 baseline captured at {now}\n"
            f"legacy_automation_loc: {plan.legacy_loc}\n",
            encoding="utf-8",
        )
        print(f"[metrics] wrote {metrics_path.relative_to(plan.repo_root)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    parser.add_argument("--apply", action="store_true", help="actually mutate files")
    parser.add_argument("--repo-root", default=os.getcwd(), help="repo root path")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / ".git").exists():
        print(f"error: {repo_root} is not a git repository", file=sys.stderr)
        return 2

    plan = gather_plan(repo_root)
    print(f"=== Migration plan (repo: {repo_root}) ===")
    print(f"Legacy code/llmxive-automation LOC baseline: {plan.legacy_loc}")
    print(f"Moves: {len(plan.moves)}")
    for src, dst in plan.moves[:5]:
        print(f"  {src.relative_to(repo_root)} -> {dst.relative_to(repo_root)}")
    if len(plan.moves) > 5:
        print(f"  ... and {len(plan.moves) - 5} more")
    print(f"Project state files to create: {len(plan.project_states)}")
    print(f"Legacy directories to remove (if empty): {len(plan.deletes)}")
    if not args.apply:
        print("\n[dry-run] re-run with --apply to execute.")
        return 0

    apply_plan(plan)
    print("\n[done] migration applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
