"""Per-project state (state/projects/<PROJ-ID>.yaml) read/write (T015).

Contracts: project-state.schema.yaml. Validates on every read and write.
Computes content hashes for every artifact under the project's canonical
paths (FR-007 anti-tamper).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from llmxive.contract_validate import validate
from llmxive.types import Project


def _state_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "state"


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
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


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


__all__ = ["load", "save", "list_all", "hash_file", "refresh_artifact_hashes"]
