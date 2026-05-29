"""Upstream feedback annotations for arxiv-intake papers (spec 012 / US7).

arXiv-submitted papers are third-party: the source tarball is frozen and
the llmXive pipeline must NOT mutate ``paper/source/``. When such a paper
attracts a non-accept verdict, the consolidated action items are recorded
as an annotation file (``projects/<PROJ-ID>/upstream_feedback.yaml``)
rather than triggering the auto-planned revision pipeline. The project's
final outcome is restricted to ``paper_accepted`` (with caveats noted) or
``brainstormed`` (rejection).

See specs/012-paper-review-convergence/contracts/upstream_feedback.md
for the canonical schema.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import yaml

from llmxive.config import repo_root as _config_repo_root

SCHEMA_VERSION = 1


def is_arxiv_intake(project_dir: Path) -> bool:
    """A project is arxiv-intake iff it has ``paper/metadata.json`` AND no
    ``paper/specs/`` feature directory (we can't generate a revision spec
    for source we don't own).
    """
    project_dir = Path(project_dir)
    return (project_dir / "paper" / "metadata.json").is_file() and not (
        project_dir / "paper" / "specs"
    ).is_dir()


def _repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root)
    return _config_repo_root()


def _arxiv_id_for(project_id: str, *, repo_root: Path) -> str:
    """Read arxiv_id from ``paper/metadata.json`` (best-effort)."""
    meta_path = repo_root / "projects" / project_id / "paper" / "metadata.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return str(meta.get("arxiv_id", ""))
    except (OSError, json.JSONDecodeError):
        return ""


def _atomic_write_yaml(path: Path, payload: dict) -> None:
    """Atomic write via .tmp + os.replace; preserves YAML formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    os.replace(tmp, path)


def record_round(
    project_id: str,
    *,
    verdict_class: str,
    action_items: Iterable,
    note: str = "",
    repo_root: Path | None = None,
) -> Path:
    """Append a new Round to ``upstream_feedback.yaml`` for an arxiv-intake
    project. Creates the file with ``schema_version: 1`` on first write.

    Parameters
    ----------
    project_id : str
        e.g. ``"PROJ-564-qwen-image-vae-2-0-technical-report"``.
    verdict_class : str
        One of ``writing``, ``science``, ``fatal`` — the max severity in
        this review round.
    action_items : Iterable[ActionItem | dict]
        Consolidated (deduplicated) action items for this round.
    note : str
        Free-text human-readable summary of the round.
    repo_root : Path | None
        Repo root override (test fixtures); defaults to the package root.

    Returns
    -------
    Path
        Absolute path to the written YAML file.
    """
    repo = _repo_root(repo_root)
    path = repo / "projects" / project_id / "upstream_feedback.yaml"
    if path.is_file():
        existing = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        existing = {
            "project_id": project_id,
            "arxiv_id": _arxiv_id_for(project_id, repo_root=repo),
            "schema_version": SCHEMA_VERSION,
            "rounds": [],
        }

    items_yaml = []
    for it in action_items:
        if hasattr(it, "model_dump"):
            items_yaml.append(it.model_dump())
        elif isinstance(it, dict):
            items_yaml.append({"id": it.get("id"), "text": it.get("text"),
                                "severity": it.get("severity")})
        # else: skip unknown shapes — better to under-record than corrupt the file.

    rounds = existing.setdefault("rounds", [])
    rounds.append({
        "round_number": len(rounds) + 1,
        "triggered_at": datetime.now(UTC).isoformat(),
        "verdict_class": verdict_class,
        "note": note,
        "action_items": items_yaml,
    })
    _atomic_write_yaml(path, existing)
    return path


def append_rejection_rationale(
    project_id: str,
    fatal_action_items: Iterable,
    *,
    repo_root: Path | None = None,
) -> Path | None:
    """Spec 012 / FR-008: when a paper is rejected to BRAINSTORMED, append
    a rejection-rationale block to the project's idea record so the
    backlog reflects WHY it was rejected.

    The rationale lists each fatal action item by id + text, prepended by
    a short timestamped header. We pick the FIRST ``.md`` file under
    ``projects/<PROJ-ID>/idea/`` as the canonical idea file (most projects
    have exactly one). If no idea file exists, returns None and the
    caller proceeds with the transition anyway (defensive — the spec's
    primary requirement is the stage transition; the rationale annotation
    is best-effort).
    """
    repo = _repo_root(repo_root)
    idea_dir = repo / "projects" / project_id / "idea"
    if not idea_dir.is_dir():
        return None
    candidates = sorted(idea_dir.glob("*.md"))
    if not candidates:
        return None
    idea_file = candidates[0]

    rationale_lines = [
        "",
        "",
        f"## Rejection rationale ({datetime.now(UTC).date().isoformat()})",
        "",
        "Paper-stage review found one or more `fatal`-severity action items. "
        "The underlying research question is returned to the backlog so a "
        "fresh approach can be considered:",
        "",
    ]
    for it in fatal_action_items:
        text = getattr(it, "text", None) or (it.get("text") if isinstance(it, dict) else "")
        id_ = getattr(it, "id", None) or (it.get("id") if isinstance(it, dict) else "")
        if text:
            rationale_lines.append(f"- **[{id_}]** {text}")
    rationale_lines.append("")

    existing = idea_file.read_text(encoding="utf-8")
    idea_file.write_text(existing.rstrip() + "\n".join(rationale_lines), encoding="utf-8")
    return idea_file


__all__ = [
    "SCHEMA_VERSION",
    "append_rejection_rationale",
    "is_arxiv_intake",
    "record_round",
]
