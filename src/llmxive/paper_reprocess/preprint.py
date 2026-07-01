"""Reviewed-Preprint manifest (2026-07-01 ethics change).

A `paper/preprint.json` marks an ingested project as a **Reviewed Preprint**: a
third-party paper llmXive has REVIEWED but never MODIFIED. It drives three things:

- attribution (`web_data._project_authors` credits ONLY the original authors, the
  submitter, and the underlying review models — never a modifier);
- the dashboard "Reviewed Preprints" tab (source link + ingestion provenance);
- the migration + routing (marks the project terminal at `REVIEWED_PREPRINT`).

The manifest is deliberately small + declarative — the canonical author list still
lives in `paper/metadata.json::authors` (we never duplicate it here). We only
record what the UI + attribution need that isn't already in metadata.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MANIFEST_NAME = "preprint.json"


def _manifest_path(project_dir: Path) -> Path:
    return project_dir / "paper" / _MANIFEST_NAME


def write_preprint_manifest(
    project_dir: Path,
    *,
    source_url: str,
    ingested_via: str,
    submitter: str,
    ingested_at: str,
    followup_project_id: str | None = None,
) -> Path:
    """Write `paper/preprint.json` marking this project a Reviewed Preprint.

    Parameters are the provenance the UI shows + the follow-up link. The original
    title/authors/abstract are NOT copied here — they stay canonical in
    `paper/metadata.json`. Returns the manifest path.
    """
    path = _manifest_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "is_reviewed_preprint": True,
        "source_url": source_url,
        "ingested_via": ingested_via,
        "submitter": submitter,
        "ingested_at": ingested_at,
        "followup_project_id": followup_project_id,
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def load_preprint_manifest(project_dir: Path) -> dict[str, Any] | None:
    """Return the parsed `paper/preprint.json`, or None if absent/unreadable."""
    path = _manifest_path(project_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def is_reviewed_preprint(project_dir: Path) -> bool:
    """True iff this project is a Reviewed Preprint (has a manifest with the flag)."""
    manifest = load_preprint_manifest(project_dir)
    return bool(manifest and manifest.get("is_reviewed_preprint") is True)


def ingestion_statement(manifest: dict[str, Any]) -> str:
    """Human-readable provenance line for the card + cover page + modal.

    e.g. "Ingested by llmXive on 2026-07-01 — scraped from arXiv; submitted via
    llmXive dashboard, GitHub issue #208 by github-actions[bot]."
    """
    src = str(manifest.get("source_url") or "").strip()
    via = str(manifest.get("ingested_via") or "").strip()
    who = str(manifest.get("submitter") or "").strip()
    when = str(manifest.get("ingested_at") or "").strip()
    # Classify the source for a friendlier phrase.
    low = src.lower()
    if "arxiv.org" in low:
        origin = "scraped from arXiv"
    elif "huggingface.co" in low or "hf.co" in low:
        origin = "scraped from HuggingFace papers"
    elif via:
        origin = via
    else:
        origin = "ingested from an external source"
    parts = [f"Ingested by llmXive"]
    if when:
        parts[0] += f" on {when[:10]}"
    parts[0] += f" — {origin}"
    if via and origin != via:
        parts.append(f"via {via}")
    if who:
        parts.append(f"submitted by {who}")
    return "; ".join(parts) + "."
