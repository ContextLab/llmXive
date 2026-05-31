"""Phase 1 sibling project spawner.

⚠️ DEPRECATED post spec 004 (2026-05-06): the sibling-iteration pattern
was retired in favor of in-place iteration on canonical projects, with
git history (commits + log notes) tracking the iteration trail. The
proliferation of ``PROJ-NNN-<slug>-iterN`` directories produced messy
project trees with no offsetting benefit. This file is preserved for
spec 003's historical reproducibility, but new phase-test specs MUST
NOT call it. See ``notes/2026-05-06-iteration-convention-change.md``
for rationale.

Original contract:
``specs/003-phase1-idea-lifecycle-testing/contracts/sibling-project.md``.

Spawns ``PROJ-NNN-<slug>-iterN`` from canonical ``PROJ-NNN-<slug>``:

  1. Validates the canonical exists and the sibling does not.
  2. Copies the canonical's idea seed (slug-named .md file under idea/) to
     the new sibling's idea/ directory, byte-for-byte (sha256 verified).
  3. Writes a fresh state YAML at ``state/projects/<sibling>.yaml`` with
     a clean state at the requested ``--start-stage`` (default: brainstormed).
  4. Prints the new sibling's project ID to stdout.

Refuses to clobber an existing sibling. State surgery on the canonical is
never performed — each sibling is a fresh, independently replayable run.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import shutil
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = PROJECT_ROOT / "projects"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

PROJ_ID_RE = re.compile(r"^PROJ-\d{3}-[a-z0-9-]{1,50}$")
ALLOWED_START_STAGES = {"brainstormed", "flesh_out_in_progress", "flesh_out_complete", "validated"}


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _slug_part(project_id: str) -> str:
    """Return the slug portion of ``PROJ-NNN-<slug>``."""
    m = re.match(r"^PROJ-\d{3}-(.+)$", project_id)
    if not m:
        raise ValueError(f"malformed project ID: {project_id}")
    return m.group(1)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def spawn_sibling(canonical_id: str, iter_num: int, start_stage: str) -> str:
    """Create the sibling project; return its ID. Raises on validation errors."""
    if not PROJ_ID_RE.match(canonical_id):
        raise ValueError(
            f"malformed canonical_project_id: {canonical_id} (expected PROJ-NNN-<slug>)"
        )
    if iter_num < 2:
        raise ValueError(f"--iter must be >= 2, got {iter_num}")
    if start_stage not in ALLOWED_START_STAGES:
        raise ValueError(
            f"--start-stage must be one of {sorted(ALLOWED_START_STAGES)}, got {start_stage!r}"
        )

    canonical_dir = PROJECTS_DIR / canonical_id
    if not canonical_dir.is_dir():
        raise FileNotFoundError(f"canonical project not found: {canonical_dir}")

    sibling_id = f"{canonical_id}-iter{iter_num}"
    sibling_dir = PROJECTS_DIR / sibling_id
    sibling_state = STATE_DIR / f"{sibling_id}.yaml"

    if sibling_dir.exists():
        raise FileExistsError(
            f"sibling already exists: {sibling_dir} (refusing to clobber)"
        )
    if sibling_state.exists():
        raise FileExistsError(
            f"sibling state already exists: {sibling_state} (refusing to clobber)"
        )

    slug = _slug_part(canonical_id)
    canonical_idea = canonical_dir / "idea" / f"{slug}.md"
    if not canonical_idea.is_file():
        raise FileNotFoundError(
            f"canonical idea seed not found: {canonical_idea}"
        )

    canonical_state = STATE_DIR / f"{canonical_id}.yaml"
    if not canonical_state.is_file():
        raise FileNotFoundError(
            f"canonical state YAML not found: {canonical_state}"
        )
    canonical_state_data = yaml.safe_load(canonical_state.read_text(encoding="utf-8"))
    title = canonical_state_data.get("title", "")
    field = canonical_state_data.get("field", "")

    # Build sibling.
    (sibling_dir / "idea").mkdir(parents=True, exist_ok=False)
    sibling_idea = sibling_dir / "idea" / f"{slug}.md"
    shutil.copyfile(canonical_idea, sibling_idea)

    src_sha = _sha256_file(canonical_idea)
    dst_sha = _sha256_file(sibling_idea)
    if src_sha != dst_sha:
        # Roll back sibling on mismatch.
        shutil.rmtree(sibling_dir)
        raise RuntimeError(
            f"sha256 mismatch after copy: src={src_sha[:12]}... dst={dst_sha[:12]}..."
        )

    print(f"[sibling] canonical: {canonical_id}", file=sys.stderr)
    print(f"[sibling] sibling:   {sibling_id}", file=sys.stderr)
    print(
        f"[sibling] copied   {canonical_idea.relative_to(PROJECT_ROOT)} → "
        f"{sibling_idea.relative_to(PROJECT_ROOT)} (sha256 verified: {src_sha[:12]}...)",
        file=sys.stderr,
    )

    now = _now_iso()
    sibling_state_data = {
        "id": sibling_id,
        "title": title,
        "field": field,
        "current_stage": start_stage,
        "last_run_id": None,
        "last_run_status": None,
        "assigned_agent": None,
        "created_at": now,
        "updated_at": now,
        "failed_stage": None,
        "human_escalation_reason": None,
        "revision_round": 0,
        "points_paper": {},
        "points_research": {},
        "speckit_paper_dir": None,
        "speckit_research_dir": None,
        "artifact_hashes": {},
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    sibling_state.write_text(
        yaml.safe_dump(sibling_state_data, sort_keys=True), encoding="utf-8"
    )
    print(
        f"[sibling] wrote    {sibling_state.relative_to(PROJECT_ROOT)} "
        f"(start_stage={start_stage})",
        file=sys.stderr,
    )

    print(sibling_id)
    return sibling_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Spawn a Phase 1 sibling iteration project."
    )
    parser.add_argument("canonical_project_id")
    parser.add_argument("--iter", dest="iter_num", type=int, required=True)
    parser.add_argument(
        "--start-stage", dest="start_stage", default="brainstormed",
        choices=sorted(ALLOWED_START_STAGES),
    )
    args = parser.parse_args(argv)

    try:
        spawn_sibling(args.canonical_project_id, args.iter_num, args.start_stage)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except (FileNotFoundError, FileExistsError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
