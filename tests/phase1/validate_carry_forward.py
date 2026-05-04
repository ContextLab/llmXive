"""Phase 1 carry-forward manifest validator (informative).

Implements the validator described in
``specs/003-phase1-idea-lifecycle-testing/contracts/carry-forward.md``.

Reads ``specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`` and
walks each ``project_id`` to confirm:

  * The ``projects/<project_id>/`` directory exists.
  * ``state/projects/<project_id>.yaml`` exists and has
    ``current_stage: project_initialized``.
  * The slug-named ``idea/<slug>.md`` file exists and parses to ≥1 citation
    (via the citation extractor in ``citation_resolver``).

Prints per-project pass/fail to stdout. Exits non-zero ONLY on parse errors
(per the contract — validator is informative, not gating).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from tests.phase1 import citation_resolver

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "specs"
    / "003-phase1-idea-lifecycle-testing"
    / "carry-forward.yaml"
)


def _slug_part(project_id: str) -> str:
    m = re.match(r"^PROJ-\d{3}-(.+?)(?:-iter\d+)?$", project_id)
    if not m:
        raise ValueError(f"malformed project ID: {project_id}")
    return m.group(1)


def validate_project(project_id: str) -> tuple[bool, list[str]]:
    """Return (passed, list-of-issues) for one project."""
    issues: list[str] = []

    proj_dir = PROJECT_ROOT / "projects" / project_id
    if not proj_dir.is_dir():
        issues.append(f"project directory missing: {proj_dir}")

    state_yaml = PROJECT_ROOT / "state" / "projects" / f"{project_id}.yaml"
    if not state_yaml.is_file():
        issues.append(f"state YAML missing: {state_yaml}")
    else:
        try:
            data = yaml.safe_load(state_yaml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            return False, [f"state YAML unparseable: {e}"]
        if data.get("current_stage") != "project_initialized":
            issues.append(
                f"state YAML current_stage is "
                f"{data.get('current_stage')!r}, expected 'project_initialized'"
            )

    if proj_dir.is_dir():
        slug = _slug_part(project_id)
        idea_file = proj_dir / "idea" / f"{slug}.md"
        if not idea_file.is_file():
            issues.append(f"idea file missing: {idea_file}")
        else:
            text = idea_file.read_text(encoding="utf-8")
            citations = citation_resolver.extract_citations(text)
            if not citations:
                issues.append(
                    f"idea file has no parseable citations: {idea_file}"
                )

    return (len(issues) == 0), issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Phase 1 carry-forward manifest (informative)."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default=str(DEFAULT_MANIFEST),
        help=f"path to carry-forward.yaml (default: {DEFAULT_MANIFEST})",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"error: manifest unparseable: {e}", file=sys.stderr)
        return 1

    if not isinstance(manifest, dict) or "projects" not in manifest:
        print(f"error: manifest missing top-level 'projects' key", file=sys.stderr)
        return 1

    projects = manifest["projects"] or []
    if not isinstance(projects, list):
        print(f"error: 'projects' must be a list", file=sys.stderr)
        return 1

    print(f"validating {len(projects)} carry-forward project(s) from {manifest_path}")
    print()

    any_failures = False
    for entry in projects:
        if not isinstance(entry, dict) or "project_id" not in entry:
            print(f"  ✗ MALFORMED entry (missing project_id): {entry!r}")
            any_failures = True
            continue
        pid = entry["project_id"]
        passed, issues = validate_project(pid)
        if passed:
            print(f"  ✓ {pid}: PASS")
        else:
            any_failures = True
            print(f"  ✗ {pid}: FAIL")
            for i in issues:
                print(f"      - {i}")

    if any_failures:
        print()
        print("(informative validator — issues above do NOT cause non-zero exit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
