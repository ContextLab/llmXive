"""Per-project citation store (T017).

state/citations/<PROJ-ID>.yaml is a top-level list of Citation records.
The token-overlap matcher exposed here is the canonical primitive used by
the Reference-Validator Agent to decide whether a fetched primary source
matches the cited title (Constitution Principle II).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from llmxive.contract_validate import validate
from llmxive.types import Citation


def _state_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "state"


def _citations_path(project_id: str, *, repo_root: Path | None = None) -> Path:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    return state_dir / "citations" / f"{project_id}.yaml"


def load(project_id: str, *, repo_root: Path | None = None) -> list[Citation]:
    path = _citations_path(project_id, repo_root=repo_root)
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    out: list[Citation] = []
    for item in raw:
        validate("citation", item)
        out.append(Citation.model_validate(item))
    return out


def save(project_id: str, citations: list[Citation], *, repo_root: Path | None = None) -> Path:
    payload = [c.model_dump(mode="json", exclude_none=False) for c in citations]
    for item in payload:
        validate("citation", item)
    path = _citations_path(project_id, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


_TOKEN_RE: re.Pattern[str] = re.compile(r"[a-z0-9]+")


def tokenize_title(title: str) -> set[str]:
    return set(_TOKEN_RE.findall(title.lower()))


def title_overlap(cited_title: str, fetched_title: str) -> float:
    """Fraction of cited-title tokens present in fetched-title tokens.

    Returns 1.0 when cited is empty (no constraint to violate); 0.0 when
    fetched is empty.
    """
    cited = tokenize_title(cited_title)
    fetched = tokenize_title(fetched_title)
    if not cited:
        return 1.0
    if not fetched:
        return 0.0
    return len(cited & fetched) / len(cited)


__all__ = ["load", "save", "tokenize_title", "title_overlap"]
