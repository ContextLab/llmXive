"""Review-record reader/writer (T016).

Review files live at:
  projects/<PROJ-ID>/reviews/research/<author>__<YYYY-MM-DD>__<type>.md
  projects/<PROJ-ID>/paper/reviews/<author>__<YYYY-MM-DD>__<type>.md

Each file has YAML frontmatter validated against
contracts/review-record.schema.yaml plus a free-form markdown body that
is mirrored into the ReviewRecord.feedback field.

Self-review (reviewer_name == produced_by_agent of the artifact) is
refused at write-time; the Advancement-Evaluator additionally skips any
self-review records it finds at read-time.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from llmxive.contract_validate import validate
from llmxive.types import ReviewRecord


_FRONTMATTER_RE: re.Pattern[str] = re.compile(
    r"^---\s*\n(?P<frontmatter>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)


class SelfReviewRefused(RuntimeError):
    """Raised when a reviewer attempts to review its own contribution."""


def _path_for(
    project_id: str,
    *,
    stage: str,
    reviewer_name: str,
    date_iso: str,
    review_type: str,
    repo_root: Path | None = None,
) -> Path:
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    base = repo / "projects" / project_id
    sub = "reviews/research" if stage == "research" else "paper/reviews"
    return base / sub / f"{reviewer_name}__{date_iso}__{review_type}.md"


def write(
    record: ReviewRecord,
    *,
    body: str,
    stage: str,
    review_type: str,
    produced_by_agent: str | None,
    repo_root: Path | None = None,
) -> Path:
    if produced_by_agent and produced_by_agent == record.reviewer_name:
        raise SelfReviewRefused(
            f"reviewer {record.reviewer_name!r} authored the artifact and may not review it"
        )

    payload = record.model_dump(mode="json", exclude_none=False)
    validate("review-record", payload)

    project_id = record.artifact_path.split("/")[1]
    path = _path_for(
        project_id,
        stage=stage,
        reviewer_name=record.reviewer_name,
        date_iso=record.reviewed_at.date().isoformat(),
        review_type=review_type,
        repo_root=repo_root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(payload, sort_keys=True).rstrip("\n")
    path.write_text(f"---\n{frontmatter}\n---\n\n{body.strip()}\n", encoding="utf-8")
    return path


def read(path: Path) -> ReviewRecord:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"no YAML frontmatter in review file: {path}")
    payload = yaml.safe_load(match.group("frontmatter"))
    validate("review-record", payload)
    record = ReviewRecord.model_validate(payload)
    body = match.group("body").strip()
    if body:
        record = record.model_copy(update={"feedback": body})
    return record


def list_for(
    project_id: str,
    *,
    stage: str,
    repo_root: Path | None = None,
) -> list[ReviewRecord]:
    repo = repo_root or Path(__file__).resolve().parent.parent.parent.parent
    base = repo / "projects" / project_id
    sub = "reviews/research" if stage == "research" else "paper/reviews"
    review_dir = base / sub
    if not review_dir.is_dir():
        return []
    return [read(p) for p in sorted(review_dir.glob("*.md"))]


__all__ = ["write", "read", "list_for", "SelfReviewRefused"]
