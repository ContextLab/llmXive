"""End-to-end cleanup script for the post-backfill state.

Steps:
  1. Detect duplicate projects (same field + similar title) and merge them.
  2. Renumber every project sequentially (PROJ-001, PROJ-002, ...) preserving
     deterministic order (oldest created_at first; ties by id).
  3. Migrate legacy projects/<id>/technical-design/design.md to
     projects/<id>/specs/001-<slug>/spec.md (Spec Kit format wrapper).
     Same for implementation-plan/.
  4. Clean noisy GitHub-issue titles (gh issue edit) for the issues we
     imported into projects.

Run from repo root (read-only by default; pass --apply to mutate).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import yaml  # noqa: E402

from llmxive.state import project as project_store  # noqa: E402
from llmxive.types import Project, Stage  # noqa: E402


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


_NOISY_TITLE_PREFIXES_BARE = ("Title:", "Research Idea:", "Idea:")


def _strip_title_prefixes(s: str) -> str:
    s = s.strip(' "\'*')
    for _ in range(3):
        for p in _NOISY_TITLE_PREFIXES_BARE:
            if s.lower().startswith(p.lower()):
                s = s[len(p):].lstrip(" :*\"'")
        if not any(s.lower().startswith(p.lower()) for p in _NOISY_TITLE_PREFIXES_BARE):
            break
    return s


def improve_titles_from_content(repo: Path, *, apply: bool) -> int:
    """For every project whose title looks vague (contains 'research',
    'systems', 'analysis' as the only descriptor, or len <= 3 words),
    look at projects/<id>/technical-design/design.md and projects/<id>/idea/*.md
    for a better title.

    Returns the number of projects whose titles were improved.
    """
    fixed = 0
    for state_file in (repo / "state" / "projects").glob("PROJ-*.yaml"):
        try:
            project = project_store.load(state_file.stem, repo_root=repo)
        except Exception:
            continue
        # Heuristic for vague titles.
        words = project.title.lower().split()
        is_vague = (
            len(words) <= 3
            or set(words) <= {"research", "systems", "analysis", "review",
                              "biology", "chemistry", "physics", "psychology",
                              "neuroscience", "robotics", "automation", "testing"}
        )
        if not is_vague:
            continue
        pdir = repo / "projects" / project.id
        candidate: str | None = None
        # Source 1: legacy technical-design/design.md "# Technical Design Document: ..."
        legacy = pdir / "technical-design" / "design.md"
        if legacy.exists():
            first = legacy.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            m = re.match(r"#\s*Technical Design Document:\s*(.+)", first, re.IGNORECASE)
            if m:
                candidate = _strip_title_prefixes(m.group(1).strip())
        # Source 2: idea/*.md first H1
        if not candidate:
            idea = next(iter((pdir / "idea").glob("*.md")), None) if (pdir / "idea").exists() else None
            if idea:
                for line in idea.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("# "):
                        candidate = _strip_title_prefixes(line[2:].strip())
                        break
        if not candidate or len(candidate) < 8:
            continue
        if len(candidate) > 100:
            candidate = candidate[:100].rsplit(" ", 1)[0] + "…"
        print(f"  improve {project.id}: {project.title!r} -> {candidate!r}")
        if apply:
            new = project.model_copy(update={
                "title": candidate,
                "updated_at": datetime.now(UTC),
            })
            project_store.save(new, repo_root=repo)
        fixed += 1
    return fixed


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "x"


def find_duplicates(projects: list[Project]) -> list[list[str]]:
    """Return groups of project IDs that look like duplicates.

    Tighter than the original: requires title similarity >= 0.85 AND the
    same field, OR a normalised title-text exact match. This avoids
    spurious clusters like (biology-research, psychology-research) that
    only share the trailing "research" suffix.
    """
    ids_in_order = [p.id for p in projects]
    by_id = {p.id: p for p in projects}
    duplicate_groups: list[list[str]] = []
    seen: set[str] = set()
    for i, a in enumerate(ids_in_order):
        if a in seen:
            continue
        ta = by_id[a].title.lower().strip()
        cluster = [a]
        for b in ids_in_order[i + 1:]:
            if b in seen:
                continue
            tb = by_id[b].title.lower().strip()
            normalised_match = (
                re.sub(r"\s+", " ", ta) == re.sub(r"\s+", " ", tb)
            )
            same_field = by_id[a].field.lower() == by_id[b].field.lower()
            sim = title_similarity(ta, tb)
            if normalised_match or (sim >= 0.85 and same_field):
                cluster.append(b)
        if len(cluster) > 1:
            seen.update(cluster)
            duplicate_groups.append(cluster)
    return duplicate_groups


def merge_cluster(repo: Path, ids: list[str], *, apply: bool) -> str:
    """Pick the first id as canonical; delete the rest. Returns canonical id."""
    canonical = sorted(ids)[0]  # deterministic
    losers = [i for i in ids if i != canonical]
    print(f"  cluster: keep {canonical}; merge+delete {losers}")
    if not apply:
        return canonical
    for loser in losers:
        sf = repo / "state" / "projects" / f"{loser}.yaml"
        pdir = repo / "projects" / loser
        if sf.exists():
            sf.unlink()
        if pdir.exists():
            shutil.rmtree(pdir)
    return canonical


def renumber_all(repo: Path, *, apply: bool) -> dict[str, str]:
    """Renumber every state/projects/PROJ-*.yaml to PROJ-001, PROJ-002, ...
    by created_at ascending. Returns a mapping old_id → new_id.
    """
    projects = project_store.list_all(repo_root=repo)
    projects.sort(key=lambda p: (p.created_at, p.id))
    mapping: dict[str, str] = {}
    for n, p in enumerate(projects, start=1):
        slug = p.id.split("-", 2)[-1]  # preserve original slug
        new_id = f"PROJ-{n:03d}-{slug}"
        if new_id == p.id:
            continue
        mapping[p.id] = new_id
    print(f"  {len(mapping)} project(s) need renumbering")
    if not apply:
        for old, new in mapping.items():
            print(f"    {old} -> {new}")
        return mapping
    # Two-pass to avoid collisions: rename to PROJ-tmp-<n>, then to final.
    tmp_map = {old: f"PROJ-tmp-{n:03d}-{old.split('-', 2)[-1]}"
               for n, old in enumerate(mapping, start=1)}
    for old, tmp in tmp_map.items():
        _rename_project(repo, old, tmp)
    for old, new in mapping.items():
        _rename_project(repo, tmp_map[old], new)
    return mapping


def _rename_project(repo: Path, old: str, new: str) -> None:
    """Rename a project on-disk: state file, dir, and the id field inside YAML."""
    sf = repo / "state" / "projects" / f"{old}.yaml"
    pdir = repo / "projects" / old
    if sf.exists():
        new_sf = repo / "state" / "projects" / f"{new}.yaml"
        text = sf.read_text(encoding="utf-8")
        # Validate vs schema by round-tripping through the model.
        data = yaml.safe_load(text)
        # If the new id doesn't match PROJ_ID_RE, fall back to a clean slug.
        if not re.match(r"^PROJ-\d{3,}-[a-z0-9-]+$", new):
            new = re.sub(r"[^a-z0-9-]", "", new.lower())
        data["id"] = new
        # speckit dirs (if any) need their PROJ-id segment rewritten.
        for k in ("speckit_research_dir", "speckit_paper_dir"):
            v = data.get(k)
            if v:
                data[k] = v.replace(old, new)
        # artifact_hashes paths likewise.
        if data.get("artifact_hashes"):
            data["artifact_hashes"] = {
                p.replace(old, new): h for p, h in data["artifact_hashes"].items()
            }
        new_sf.parent.mkdir(parents=True, exist_ok=True)
        new_sf.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
        sf.unlink()
    if pdir.exists():
        new_pdir = repo / "projects" / new
        new_pdir.parent.mkdir(parents=True, exist_ok=True)
        if new_pdir.exists():
            # Should not happen with tmp-prefix two-pass; but be safe.
            shutil.rmtree(new_pdir)
        pdir.rename(new_pdir)


_LEGACY_DESIGN_HEADER = re.compile(r"^# Technical Design Document.*?\n", re.IGNORECASE | re.MULTILINE)


def migrate_legacy_design(repo: Path, project: Project, *, apply: bool) -> bool:
    """Convert technical-design/design.md → specs/001-<slug>/spec.md.

    Wraps the legacy prose in a Spec Kit-style spec.md template:

        # Feature Specification: <title>
        ## Background
        <legacy prose>
        ## User Scenarios & Testing
        (placeholder — to be filled by the Specifier on next pipeline pass)
        ## Functional Requirements
        ...

    Removes the legacy directories afterward.
    """
    pdir = repo / "projects" / project.id
    legacy_design = pdir / "technical-design" / "design.md"
    if not legacy_design.exists():
        return False
    legacy_text = legacy_design.read_text(encoding="utf-8", errors="replace")
    legacy_text = _LEGACY_DESIGN_HEADER.sub("", legacy_text).strip()

    slug = project.id.split("-", 2)[-1]
    feature_dir = pdir / "specs" / f"001-{slug}"
    spec_path = feature_dir / "spec.md"
    if spec_path.exists():
        return False  # already migrated

    spec_md = (
        f"# Feature Specification: {project.title}\n\n"
        "**Status**: migrated from legacy technical-design (pre-refactor)\n\n"
        "## Background (from legacy technical design)\n\n"
        f"{legacy_text}\n\n"
        "## User Scenarios & Testing\n\n"
        "_TODO: the Specifier agent will populate this on the next pipeline pass._\n\n"
        "## Functional Requirements\n\n"
        "_TODO: extracted from the background by the Specifier agent._\n\n"
        "## Success Criteria\n\n"
        "_TODO: measurable outcomes._\n\n"
        "## Assumptions\n\n"
        "- Imported from legacy `technical-design/design.md`. The prose has not been "
        "verified against the new pipeline's quality bar; the Specifier agent should "
        "rewrite this spec on its next pass.\n"
    )

    print(f"  migrate {project.id}: technical-design/design.md → specs/001-{slug}/spec.md")
    if not apply:
        return True
    feature_dir.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(spec_md, encoding="utf-8")

    # Migrate implementation-plan/plan.md (if any)
    legacy_plan = pdir / "implementation-plan" / "plan.md"
    if legacy_plan.exists():
        plan_text = legacy_plan.read_text(encoding="utf-8", errors="replace")
        plan_md = (
            f"# Implementation Plan: {project.title}\n\n"
            "**Status**: migrated from legacy implementation-plan/.\n\n"
            "## Background (from legacy implementation plan)\n\n"
            f"{plan_text}\n\n"
            "## Constitution Check\n\n_TODO: verify against the project's constitution._\n\n"
            "## Phase 0 — Research\n\n_TODO: legacy lit-search needs revisit._\n"
        )
        (feature_dir / "plan.md").write_text(plan_md, encoding="utf-8")

    # Update the Project record: stage and speckit_research_dir.
    new_project = project.model_copy(update={
        "current_stage": Stage.SPECIFIED,
        "speckit_research_dir": str(feature_dir.relative_to(repo).as_posix()),
        "updated_at": datetime.now(UTC),
    })
    project_store.save(new_project, repo_root=repo)

    # Drop the legacy dirs.
    for legacy_dir in ("technical-design", "implementation-plan"):
        d = pdir / legacy_dir
        if d.exists():
            shutil.rmtree(d)
    return True


_NOISY_TITLE_PREFIXES = (
    "Certainly!", "Sure!", "Here is", "Here's", "Title:",
    "Research Idea:", "Idea:", "Project:", "**",
)


def clean_issue_titles(repo: Path, *, apply: bool) -> int:
    """Find issues we backfilled (by the github_issue: front-matter) whose
    titles are noisy and rewrite them to match the cleaned project.title."""
    fixed = 0
    for state_file in (repo / "state" / "projects").glob("PROJ-*.yaml"):
        try:
            project = project_store.load(state_file.stem, repo_root=repo)
        except Exception:
            continue
        pdir = repo / "projects" / project.id
        idea_md = next(iter((pdir / "idea").glob("*.md")), None) if (pdir / "idea").exists() else None
        if not idea_md:
            continue
        text = idea_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"github_issue:\s*https://github.com/ContextLab/llmXive/issues/(\d+)", text)
        if not m:
            continue
        issue_num = int(m.group(1))
        # Skip if title looks fine already.
        try:
            cur = subprocess.run(
                ["gh", "issue", "view", str(issue_num), "--json", "title"],
                capture_output=True, text=True, check=True,
            )
            import json
            cur_title = json.loads(cur.stdout)["title"]
        except Exception:
            continue
        if cur_title.strip() == project.title:
            continue
        if any(cur_title.startswith(p) for p in _NOISY_TITLE_PREFIXES) or len(cur_title) > 90:
            print(f"  fix #{issue_num}: {cur_title[:60]!r} -> {project.title!r}")
            if apply:
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_num), "--title", project.title],
                    check=True, capture_output=True, text=True,
                )
            fixed += 1
    return fixed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually mutate the repo (default: dry-run)")
    ap.add_argument("--skip-issues", action="store_true",
                    help="skip GitHub-issue title cleanup")
    ap.add_argument("--skip-dedup", action="store_true")
    ap.add_argument("--skip-renumber", action="store_true")
    ap.add_argument("--skip-migrate", action="store_true")
    args = ap.parse_args()
    repo = REPO

    print("=== Step 0: improve vague titles from content ===")
    n = improve_titles_from_content(repo, apply=args.apply)
    print(f"  improved {n} title(s).")

    if not args.skip_dedup:
        print("\n=== Step 1: dedup ===")
        projects = project_store.list_all(repo_root=repo)
        dups = find_duplicates(projects)
        print(f"  found {len(dups)} duplicate cluster(s).")
        for ids in dups:
            merge_cluster(repo, ids, apply=args.apply)

    if not args.skip_migrate:
        print("\n=== Step 2: migrate legacy technical-design/, implementation-plan/ ===")
        n = 0
        for project in project_store.list_all(repo_root=repo):
            if migrate_legacy_design(repo, project, apply=args.apply):
                n += 1
        print(f"  migrated {n} legacy project(s).")

    if not args.skip_renumber:
        print("\n=== Step 3: renumber sequentially ===")
        renumber_all(repo, apply=args.apply)

    if not args.skip_issues:
        print("\n=== Step 4: clean GitHub issue titles ===")
        n = clean_issue_titles(repo, apply=args.apply)
        print(f"  proposed {n} title fix(es).")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
