"""Project activity feed (spec 009, FR-025 through FR-033).

Per-project append-only JSON Lines file at
    projects/<project_id>/activity.jsonl
with audit log at
    projects/<project_id>/.audit/edit-history.jsonl
    projects/<project_id>/.audit/rejected-contributions.jsonl
    projects/<project_id>/.audit/dispatches/*.jsonl

Single source of truth (Constitution I): all reads/writes go through FeedStore.
"""

from .store import FeedStore, PackedFeed  # noqa: F401
from .manifest import ManifestValidator, parse_manifest_block  # noqa: F401

__all__ = ["FeedStore", "PackedFeed", "ManifestValidator", "parse_manifest_block"]
