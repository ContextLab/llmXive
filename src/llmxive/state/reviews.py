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

from llmxive.config import repo_root as _repo_root
from llmxive.contract_validate import validate
from llmxive.state._io import atomic_write_text
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
    repo = repo_root or _repo_root()
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
    frontmatter = yaml.safe_dump(payload, sort_keys=True).rstrip("\n")
    atomic_write_text(path, f"---\n{frontmatter}\n---\n\n{body.strip()}\n")
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
    repo = repo_root or _repo_root()
    base = repo / "projects" / project_id
    sub = "reviews/research" if stage == "research" else "paper/reviews"
    review_dir = base / sub
    if not review_dir.is_dir():
        return []
    return [read(p) for p in sorted(review_dir.glob("*.md"))]


def delete_for_specialists(
    project_id: str,
    specialist_names: set[str],
    *,
    stage: str,
    repo_root: Path | None = None,
) -> int:
    """Remove all review records authored by ``specialist_names`` for a stage.

    Used after a successful revision round to force re-review of the blocking
    specialists: research-review staleness is keyed on the feature ``tasks.md``
    hash, but a research revision edits code/data/docs — NOT ``tasks.md`` — so a
    blocker's verdict can never go stale on its own, and the panel would loop to
    ``MAX_REVISION_ROUNDS`` without the fixed concern ever being re-judged.
    Deleting the record makes the coverage gate see the specialist as *missing*
    → it is re-dispatched → it re-reviews the revised artifacts. The deleted
    record remains in git history (audit trail); the re-review writes a fresh,
    current record. Returns the number of files removed.
    """
    repo = repo_root or _repo_root()
    sub = "reviews/research" if stage == "research" else "paper/reviews"
    review_dir = repo / "projects" / project_id / sub
    if not review_dir.is_dir():
        return 0
    removed = 0
    for p in sorted(review_dir.glob("*.md")):
        try:
            rec = read(p)
        except Exception:
            continue
        if rec.reviewer_name in specialist_names:
            p.unlink(missing_ok=True)
            removed += 1
    return removed


def prior_reviews_for_specialist(
    project_id: str,
    specialist_name: str,
    *,
    stage: str = "paper",
    repo_root: Path | None = None,
) -> list[ReviewRecord]:
    """Spec 012 / FR-014: return all prior review records for THIS project
    AND THIS specialist, sorted by ``reviewed_at`` ascending. Returns an
    empty list if the specialist has no prior reviews — in which case the
    re-review protocol does NOT activate for this specialist (FR-017).
    """
    records = list_for(project_id, stage=stage, repo_root=repo_root)
    matching = [r for r in records if r.reviewer_name == specialist_name]
    matching.sort(key=lambda r: r.reviewed_at)
    return matching


__all__ = ["SelfReviewRefused", "list_for", "prior_reviews_for_specialist", "read", "write"]
