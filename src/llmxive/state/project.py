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
from llmxive.state._io import (
    StaleWriteError,
    atomic_write_text,
    atomic_write_text_cas,
    read_mtime_ns,
)
from llmxive.types import Project


class _Unset:
    """Sentinel type: ``expected_mtime_ns`` was not supplied (``None`` is a
    valid token meaning "the file did not exist when read")."""


_UNSET = _Unset()


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


def save(
    project: Project,
    *,
    repo_root: Path | None = None,
    expected_mtime_ns: int | None | _Unset = _UNSET,
) -> Path:
    """Persist the canonical project state to ``state/projects/<id>.yaml``.

    The write is ATOMIC (temp file + ``os.replace`` via the shared
    :func:`llmxive.state._io.atomic_write_text`), so a crash mid-write can
    never leave a truncated YAML that the next ``load()`` reads as ``{}``.

    ``expected_mtime_ns`` opts into a best-effort compare-and-swap: when the
    caller passes the file's mtime captured *before* its read-modify-write
    (as :func:`update` does), the write is rejected with
    :class:`~llmxive.state._io.StaleWriteError` if another writer landed in
    between — guarding against two overlapping pipeline ticks silently losing
    each other's update. The default (unset) keeps the plain atomic write for
    the many callers that supply a fully-formed ``Project``.
    """
    payload = project.model_dump(mode="json", exclude_none=False)
    validate("project-state", payload)
    path = _project_state_path(project.id, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Audit trail: capture the prior stage BEFORE the write so a transition
    # can be appended to state/projects/<PROJ-ID>.history.jsonl. Appending
    # only AFTER a successful write keeps the trail free of phantom
    # transitions when a compare-and-swap write is rejected + retried (see
    # `update`). This makes manual override detectable post-hoc — a stage
    # transition without a corresponding runlog entry is suspicious.
    try:
        prev: Project | None = load(project.id, repo_root=repo_root)
    except FileNotFoundError:
        prev = None  # First save for a new project — no history yet.
    content = yaml.safe_dump(payload, sort_keys=True)
    if isinstance(expected_mtime_ns, _Unset):
        atomic_write_text(path, content)
    else:
        atomic_write_text_cas(path, content, expected_mtime_ns=expected_mtime_ns)
    if prev is not None and prev.current_stage != project.current_stage:
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
    return path


def update(
    project_id: str, fields: dict[str, object], *, repo_root: Path | None = None,
) -> Project:
    """Load a project, apply `fields` as a partial update, save, return
    the new Project. Pydantic re-validates the merged document; any
    field whose value doesn't satisfy the schema raises.

    Used by the spec-013 implementer + publisher to advance stages.

    This is a genuine read-modify-write, so it uses a best-effort
    compare-and-swap: the file's mtime is captured BEFORE the read, and the
    save is rejected if another writer landed in between. On such a
    :class:`~llmxive.state._io.StaleWriteError` the project is re-read and the
    partial ``fields`` re-applied ONCE onto the newer state, so two
    overlapping pipeline ticks cannot silently clobber each other's update.
    """
    path = _project_state_path(project_id, repo_root=repo_root)
    last_error: StaleWriteError | None = None
    for _attempt in range(2):
        # Capture mtime BEFORE the read: if a concurrent writer lands between
        # here and the save, the token is stale and the CAS write is rejected
        # (never the reverse ordering, which could pass CAS on stale content).
        mtime = read_mtime_ns(path)
        proj = load(project_id, repo_root=repo_root)
        data = proj.model_dump(mode="json")
        data.update(fields)
        new_proj = Project.model_validate(data)
        try:
            save(new_proj, repo_root=repo_root, expected_mtime_ns=mtime)
        except StaleWriteError as exc:
            last_error = exc
            continue
        return new_proj
    assert last_error is not None
    raise last_error


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
