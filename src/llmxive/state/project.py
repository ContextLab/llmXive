"""Per-project state (state/projects/<PROJ-ID>.yaml) read/write (T015).

Contracts: project-state.schema.yaml. Validates on every read and write.
Computes content hashes for every artifact under the project's canonical
paths (FR-007 anti-tamper).
"""

from __future__ import annotations

import hashlib
from datetime import UTC
from pathlib import Path

import yaml

from llmxive.config import repo_root as _repo_root
from llmxive.contract_validate import validate
from llmxive.types import Project


def _state_root() -> Path:
    return _repo_root() / "state"


def _project_state_path(project_id: str, *, repo_root: Path | None = None) -> Path:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    return state_dir / "projects" / f"{project_id}.yaml"


def load(project_id: str, *, repo_root: Path | None = None) -> Project:
    path = _project_state_path(project_id, repo_root=repo_root)
    if not path.exists():
        raise FileNotFoundError(f"no project state file: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate("project-state", raw)
    return Project.model_validate(raw)


def save(project: Project, *, repo_root: Path | None = None) -> Path:
    payload = project.model_dump(mode="json", exclude_none=False)
    validate("project-state", payload)
    path = _project_state_path(project.id, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Audit trail: append every stage transition (with timestamp + last_run_id)
    # to state/projects/<PROJ-ID>.history.jsonl. This makes manual override
    # detectable post-hoc — a stage transition without a corresponding
    # runlog entry from the previous agent is suspicious.
    try:
        prev = load(project.id, repo_root=repo_root)
        if prev.current_stage != project.current_stage:
            import json as _json
            from datetime import datetime as _dt
            history = path.with_suffix(".history.jsonl")
            history.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "at": _dt.now(UTC).isoformat(),
                "from_stage": prev.current_stage.value,
                "to_stage": project.current_stage.value,
                "last_run_id": project.last_run_id,
            }
            with history.open("a", encoding="utf-8") as fh:
                fh.write(_json.dumps(entry, sort_keys=True) + "\n")
    except FileNotFoundError:
        # First save for a new project — no history yet.
        pass
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def update(
    project_id: str, fields: dict[str, object], *, repo_root: Path | None = None,
) -> Project:
    """Load a project, apply `fields` as a partial update, save, return
    the new Project. Pydantic re-validates the merged document; any
    field whose value doesn't satisfy the schema raises.

    Used by the spec-013 implementer + publisher to advance stages.
    """
    proj = load(project_id, repo_root=repo_root)
    data = proj.model_dump(mode="json")
    data.update(fields)
    new_proj = Project.model_validate(data)
    save(new_proj, repo_root=repo_root)
    return new_proj


def list_all(*, repo_root: Path | None = None) -> list[Project]:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    proj_dir = state_dir / "projects"
    if not proj_dir.is_dir():
        return []
    out: list[Project] = []
    for path in sorted(proj_dir.glob("PROJ-*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        validate("project-state", raw)
        out.append(Project.model_validate(raw))
    return out


def hash_file(path: Path) -> str:
    """SHA-256 of a file's bytes."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def feature_dir_for(project_dir: Path, *, track: str) -> Path | None:
    """The speckit feature dir whose ``tasks.md`` is the track's governing
    review artifact (canonical home — spec 023 / FR-004).

    ``track="research"`` looks under ``projects/<id>/specs/*/``;
    ``track="paper"`` under ``projects/<id>/paper/specs/*/``. Preference
    order: a dir with ``tasks.md``, then one with ``spec.md``, then the
    alphabetically-first candidate — pure alphabetical sort alone can pick
    a ghost dir created when an earlier LLM run wrote to an invented slug.
    Both reviewers and the advancement evaluator's verdict-coverage check
    MUST resolve the artifact through here so "current vs stale" means the
    same file everywhere.
    """
    # Spec 023 defect #17: a project that cycles through an idea-root
    # kickback accumulates feature dirs (001-..N); the old heuristic
    # (first dir with tasks.md, ascending) resolved the STALE prior cycle
    # while the agents worked the new one — reviewers would hash the old
    # tasks.md. The project state's speckit_*_dir pointer is the SSoT:
    # honor it first; the content heuristic is the fallback for projects
    # without a pointer (e.g. arXiv intake).
    project_id = project_dir.name
    repo_root = project_dir.parent.parent
    state_path = repo_root / "state" / "projects" / f"{project_id}.yaml"
    if state_path.is_file():
        try:
            raw = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
            key = "speckit_paper_dir" if track == "paper" else "speckit_research_dir"
            pointer = raw.get(key)
            if pointer:
                pointed = repo_root / pointer
                if pointed.is_dir():
                    return pointed
        except yaml.YAMLError:
            pass
    base = project_dir / "paper" if track == "paper" else project_dir
    candidates = sorted(base.glob("specs/*/"))
    if not candidates:
        return None
    for c in candidates:
        if (c / "tasks.md").exists():
            return c
    for c in candidates:
        if (c / "spec.md").exists():
            return c
    return candidates[0]


def refresh_artifact_hashes(project: Project, *, repo_root: Path | None = None) -> Project:
    """Recompute artifact_hashes for every file under projects/<PROJ-ID>/.

    Returns a new Project with updated_at bumped and artifact_hashes refreshed.
    The caller is responsible for calling save().
    """
    repo = repo_root or _state_root().parent
    project_dir = repo / "projects" / project.id
    new_hashes: dict[str, str] = {}
    if project_dir.is_dir():
        for fp in project_dir.rglob("*"):
            if fp.is_file() and ".specify" not in fp.parts:
                rel = fp.relative_to(repo).as_posix()
                new_hashes[rel] = hash_file(fp)
    return project.model_copy(update={"artifact_hashes": new_hashes})


__all__ = [
    "feature_dir_for",
    "hash_file",
    "list_all",
    "load",
    "refresh_artifact_hashes",
    "save",
]
