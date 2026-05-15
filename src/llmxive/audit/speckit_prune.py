"""Speckit artifact audit + prune (spec 010, FR-007/008/009).

Scans every speckit `.md` under projects/**/specs/**/ and projects/**/.specify/**/,
classifies REAL or TEMPLATE via `_real_only_guard.is_real()`, optionally deletes
templates transitively (with all downstream artifacts generated from them) and
rolls the affected project's `current_stage` back to the latest surviving real
stage.

CLI:
    python -m llmxive speckit audit-artifacts [--out PATH] [--dry-run]
    python -m llmxive speckit prune-templates --apply
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from llmxive.speckit._real_only_guard import is_real

# Stage → expected artifact filenames, ordered by stage progression. Used by
# audit_artifacts() to compute transitive_dependents: when an artifact at stage
# X is TEMPLATE, all artifacts at stages > X for the same project are downstream.
STAGE_ARTIFACTS: list[tuple[str, list[str]]] = [
    ("project_initialized", ["data-model.md"]),  # placeholder; mostly stage marker
    ("specified", ["spec.md"]),
    ("clarified", ["spec.md"]),  # same file; updated in place
    ("planned", ["plan.md", "research.md", "data-model.md", "quickstart.md"]),
    ("tasked", ["tasks.md"]),
    ("analyzed", ["analyze.md"]),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_id_from_path(p: Path) -> str | None:
    """Extract PROJ-NNN-... from any path that includes a PROJ-* segment.

    Strips trailing file-suffix tokens (e.g. `.history.jsonl`, `.yaml`) when the
    PROJ-id appears as a filename rather than a directory.
    """
    for part in p.parts:
        if part.startswith("PROJ-"):
            # Strip any trailing dotted suffix(es): "PROJ-001-foo.history.jsonl"
            # → "PROJ-001-foo"; but keep dashes (the slug uses them).
            if "." in part:
                return part.split(".", 1)[0]
            return part
    return None


def _stage_from_artifact_path(p: Path) -> str:
    """Map an artifact filename to the speckit stage that produces it."""
    name = p.name
    if name == "spec.md":
        return "specified"
    if name in {"plan.md", "research.md", "quickstart.md"}:
        return "planned"
    if name == "tasks.md":
        return "tasked"
    if name in {"analyze.md", "analysis.md"}:
        return "analyzed"
    if name == "data-model.md":
        return "planned"
    # Artifacts under .specify/memory/ are stage markers, treat as project_initialized
    return "project_initialized"


def _stage_rank(stage: str) -> int:
    for i, (s, _) in enumerate(STAGE_ARTIFACTS):
        if s == stage:
            return i
    return -1  # unknown stage → treat as before everything


def _transitive_dependents(
    artifact_path: Path,
    project_root: Path,
) -> list[Path]:
    """Find artifacts in the same project produced AFTER `artifact_path`'s stage."""
    artifact_stage = _stage_from_artifact_path(artifact_path)
    artifact_rank = _stage_rank(artifact_stage)
    if artifact_rank < 0:
        return []

    # Look for downstream .md artifacts in the same spec subdir.
    spec_dir = artifact_path.parent
    deps: list[Path] = []
    for f in spec_dir.glob("*.md"):
        if f == artifact_path:
            continue
        f_stage = _stage_from_artifact_path(f)
        if _stage_rank(f_stage) > artifact_rank:
            deps.append(f)
    return sorted(deps)


def audit_artifacts(repo_root: Path) -> dict[str, Any]:
    """Audit every speckit artifact in the repo. FR-007.

    Returns a dict matching contracts/speckit_artifact_audit.schema.json.
    """
    artifacts: list[dict[str, Any]] = []
    projects_dir = repo_root / "projects"

    md_paths: list[Path] = []
    if projects_dir.is_dir():
        md_paths.extend(projects_dir.glob("**/specs/**/*.md"))
        md_paths.extend(projects_dir.glob("**/.specify/**/*.md"))

    # Skip reference template directories — these are by design templates that
    # the auditor uses as comparison references; they MUST NOT be deleted by
    # the prune. Anything under `.specify/templates/` is reference material.
    def _is_reference_template(p: Path) -> bool:
        parts = p.parts
        return ".specify" in parts and "templates" in parts

    md_paths = [p for p in md_paths if not _is_reference_template(p)]

    seen: set[Path] = set()
    for p in sorted(md_paths):
        if p in seen:
            continue
        seen.add(p)
        project_id = _project_id_from_path(p)
        if not project_id:
            continue

        try:
            real = is_real(p, repo_root=repo_root)
            classification = "REAL" if real else "TEMPLATE"
            reason = "" if real else "classified template by _real_only_guard.is_real()"
        except Exception as exc:  # noqa: BLE001 — capture all classifier failures
            classification = "TEMPLATE"
            reason = f"guard raised: {exc}"

        stage = _stage_from_artifact_path(p)
        deps_paths = (
            [str(d.relative_to(repo_root)) for d in _transitive_dependents(p, repo_root)]
            if classification == "TEMPLATE"
            else []
        )
        artifacts.append(
            {
                "path": str(p.relative_to(repo_root)),
                "classification": classification,
                "reason": reason,
                "project_id": project_id,
                "stage": stage,
                "transitive_dependents": deps_paths,
            }
        )

    real_count = sum(1 for a in artifacts if a["classification"] == "REAL")
    template_count = sum(1 for a in artifacts if a["classification"] == "TEMPLATE")
    templates_with_deps = sum(
        1 for a in artifacts if a["classification"] == "TEMPLATE" and a["transitive_dependents"]
    )
    affected_projects = {a["project_id"] for a in artifacts if a["classification"] == "TEMPLATE"}

    return {
        "audited_at": _now_iso(),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
        "summary": {
            "real": real_count,
            "template": template_count,
            "templates_with_dependents": templates_with_deps,
            "projects_to_roll_back": len(affected_projects),
        },
    }


def _walk_back_to_real_stage(history_path: Path, repo_root: Path) -> str:
    """Walk history.jsonl backwards; return the most recent stage whose artifacts exist + classify REAL."""
    if not history_path.exists():
        return "flesh_out_complete"
    events: list[dict[str, Any]] = []
    for line in history_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    events.reverse()

    project_id = _project_id_from_path(history_path)
    if not project_id:
        return "flesh_out_complete"
    project_dir = repo_root / "projects" / project_id

    # Walk backwards; for each stage in events, see if its artifacts survive + classify REAL.
    seen_stages: list[str] = []
    for e in events:
        stage = e.get("to_stage") or e.get("new_stage") or e.get("current_stage")
        if not stage or stage in seen_stages:
            continue
        seen_stages.append(stage)
        # Check whether this stage's expected artifacts still exist + are REAL.
        artifacts_for_stage = [s_arts for s_name, s_arts in STAGE_ARTIFACTS if s_name == stage]
        if not artifacts_for_stage:
            continue
        all_real = True
        any_found = False
        for fname in artifacts_for_stage[0]:
            for candidate in project_dir.glob(f"specs/**/{fname}"):
                any_found = True
                if not is_real(candidate, repo_root=repo_root):
                    all_real = False
                    break
            if not all_real:
                break
        # A stage 'survives' only if AT LEAST ONE expected artifact exists AND
        # every existing artifact for that stage classifies REAL. A stage whose
        # artifacts have all been deleted by the prune is treated as no-longer
        # surviving — walk further back.
        if any_found and all_real:
            return stage
    return "flesh_out_complete"


def prune_templates(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    """Audit then optionally delete templates + roll stages back. FR-008/FR-009."""
    report = audit_artifacts(repo_root)
    report["apply"] = apply
    report["deleted_paths"]: list[str] = []
    report["rolled_back_projects"]: dict[str, dict[str, str]] = {}
    report["run_id"] = str(uuid4())

    if not apply:
        return report

    # Group templates by project to do one rollback per project after deletion.
    templates_by_project: dict[str, list[dict[str, Any]]] = {}
    for a in report["artifacts"]:
        if a["classification"] == "TEMPLATE":
            templates_by_project.setdefault(a["project_id"], []).append(a)

    # Build the set of REAL artifact paths (so we don't transitively delete
    # them even if they happen to be downstream of a TEMPLATE).
    real_paths: set[str] = {
        a["path"] for a in report["artifacts"] if a["classification"] == "REAL"
    }

    for project_id, templates in templates_by_project.items():
        deleted_for_project: list[str] = []
        for a in templates:
            # Always delete the template itself; for transitive dependents,
            # only delete those that are NOT classified REAL (downstream of
            # a template that has been independently regenerated as real is
            # rare but possible — we must not blow such cases away).
            for path_str in [a["path"], *a["transitive_dependents"]]:
                if path_str != a["path"] and path_str in real_paths:
                    continue
                full = repo_root / path_str
                if full.exists():
                    full.unlink()
                    deleted_for_project.append(path_str)
                    report["deleted_paths"].append(path_str)

        # Decide whether to roll back: only when a deleted artifact is part of
        # the STAGE_ARTIFACTS set AND that stage is at-or-before the current
        # project stage. Deletions of `.specify/memory/*.md` markers are NOT
        # stage-defining and MUST NOT trigger a rollback (they'd otherwise blow
        # away project state for files the rollback can't recover from).
        proj_yaml = repo_root / "state" / "projects" / f"{project_id}.yaml"
        prior_stage = ""
        doc = {}
        if proj_yaml.exists():
            doc = yaml.safe_load(proj_yaml.read_text()) or {}
            prior_stage = doc.get("current_stage", "")

        stage_defining_artifact_names = {
            fname for _stage, fnames in STAGE_ARTIFACTS for fname in fnames
        }
        deleted_stage_defining = [
            p for p in deleted_for_project if Path(p).name in stage_defining_artifact_names
        ]

        history_path = repo_root / "state" / "projects" / f"{project_id}.history.jsonl"
        if not deleted_stage_defining:
            # No stage-defining artifact deleted → preserve current_stage.
            new_stage = prior_stage or "flesh_out_complete"
        else:
            new_stage = _walk_back_to_real_stage(history_path, repo_root)

        if proj_yaml.exists() and new_stage != prior_stage:
            doc["current_stage"] = new_stage
            doc["updated_at"] = _now_iso()
            proj_yaml.write_text(yaml.safe_dump(doc, sort_keys=True))

            # Append history event.
            event = {
                "event": "template_artifact_purge",
                "ts": _now_iso(),
                "deleted_paths": deleted_for_project,
                "prior_stage": prior_stage,
                "new_stage": new_stage,
                "reason": "speckit_prune purged TEMPLATE artifact(s) and downstream dependents",
                "run_id": report["run_id"],
            }
            with history_path.open("a") as fh:
                fh.write(json.dumps(event) + "\n")

        report["rolled_back_projects"][project_id] = {
            "prior_stage": prior_stage,
            "new_stage": new_stage,
        }

    # Log to run-log per FR-023.
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    run_log_path = repo_root / "state" / "run-log" / month / f"{report['run_id']}.jsonl"
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    with run_log_path.open("w") as fh:
        for project_id, rollback in report["rolled_back_projects"].items():
            row = {
                "ts": _now_iso(),
                "run_id": report["run_id"],
                "action": "template_artifact_purge",
                "project_id": project_id,
                "agent": "speckit_prune",
                "display_name": "Speckit prune",
                "summary": (
                    f"Purged {len([p for p in report['deleted_paths'] if project_id in p])} "
                    f"template artifact(s); stage {rollback['prior_stage']} -> {rollback['new_stage']}"
                ),
            }
            fh.write(json.dumps(row) + "\n")

    return report


__all__ = ["audit_artifacts", "prune_templates", "_walk_back_to_real_stage"]
