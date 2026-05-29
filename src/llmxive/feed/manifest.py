"""Comments-considered manifest parser + validator (FR-027, FR-028).

The manifest is a JSON object embedded at the END of an agent's output,
fenced as ```json comments-considered ... ```.  This module:
    - parses the trailing block out of free-form agent output
    - validates against contracts/comments-considered-manifest.schema.json
    - resolves every feed_item_id against the project's activity.jsonl at snapshot

Constitution V (fail fast): every validation error names the rule.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

# Trailing fenced JSON block — accepts ```json comments-considered ... ``` and
# ```comments-considered ... ``` (info-string variants).
_FENCE_RE = re.compile(
    r"```(?:json\s+)?comments-considered\s*\n(?P<body>.*?)\n```\s*$",
    re.DOTALL | re.IGNORECASE,
)

VALID_RESPONSES = {"addressed", "acknowledged", "rebutted", "deferred"}
NON_TRIVIAL_KINDS = {"personality_tick", "review", "human_comment", "revision"}


def parse_manifest_block(output: str) -> dict | None:
    """Extract the trailing ```json comments-considered``` block, if any."""
    m = _FENCE_RE.search(output.rstrip())
    if not m:
        return None
    try:
        return json.loads(m.group("body"))
    except json.JSONDecodeError:
        return None


@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""
    bogus_ids: list[str] | None = None


class ManifestValidator:
    """Validates a comments-considered manifest produced by an agent."""

    def __init__(self, feed_items: list[dict]):
        # Map by ID for O(1) existence checks
        self._feed_by_id = {it["id"]: it for it in feed_items if "id" in it}

    def validate_block(self, output: str, *, dispatch_id: str, truncation_in_context: bool) -> ValidationResult:
        manifest = parse_manifest_block(output)
        if manifest is None:
            return ValidationResult(ok=False, reason="manifest_block_missing_or_unparseable")
        return self.validate(manifest, dispatch_id=dispatch_id, truncation_in_context=truncation_in_context)

    def validate(self, manifest: dict, *, dispatch_id: str, truncation_in_context: bool) -> ValidationResult:
        # Required top-level fields
        required = {"dispatch_id", "agent", "feed_snapshot_at", "items", "truncation_acknowledged"}
        missing = required - set(manifest)
        if missing:
            return ValidationResult(ok=False, reason=f"missing_fields:{sorted(missing)}")

        # dispatch_id match
        if manifest["dispatch_id"] != dispatch_id:
            return ValidationResult(
                ok=False,
                reason=f"dispatch_id_mismatch:expected={dispatch_id},got={manifest['dispatch_id']}",
            )

        # truncation acknowledgement
        ack = bool(manifest["truncation_acknowledged"])
        if truncation_in_context and not ack:
            return ValidationResult(ok=False, reason="truncation_not_acknowledged")
        if (not truncation_in_context) and ack:
            # not strictly an error but worth flagging
            pass

        # items validity
        if not isinstance(manifest["items"], list):
            return ValidationResult(ok=False, reason="items_not_array")
        bogus: list[str] = []
        for entry in manifest["items"]:
            if not isinstance(entry, dict):
                return ValidationResult(ok=False, reason="item_not_object")
            fid = entry.get("feed_item_id")
            resp = entry.get("response")
            if not fid:
                return ValidationResult(ok=False, reason="item_missing_feed_item_id")
            if resp not in VALID_RESPONSES:
                return ValidationResult(ok=False, reason=f"item_invalid_response:{resp}")
            if fid not in self._feed_by_id:
                bogus.append(fid)
            if resp in {"rebutted", "deferred"} and not entry.get("reason"):
                return ValidationResult(
                    ok=False, reason=f"reason_required_for_{resp}:{fid}",
                )
        if bogus:
            return ValidationResult(ok=False, reason="bogus_feed_item_ids", bogus_ids=bogus)

        return ValidationResult(ok=True, reason="valid")

    # ----- Helpers -----

    def non_trivial_feed_ids(self) -> set[str]:
        """Return IDs the agent SHOULD have considered (FR-027 'non-trivial item')."""
        return {
            fid
            for fid, it in self._feed_by_id.items()
            if it.get("kind") in NON_TRIVIAL_KINDS and it.get("audit_status", "live") == "live"
        }


def emit_empty_manifest(*, dispatch_id: str, agent: str, feed_snapshot_at: str, truncation: bool) -> str:
    """Convenience for agents that have nothing to say about prior feed items."""
    payload = {
        "dispatch_id": dispatch_id,
        "agent": agent,
        "feed_snapshot_at": feed_snapshot_at,
        "items": [],
        "truncation_acknowledged": truncation,
    }
    return "```json comments-considered\n" + json.dumps(payload, indent=2) + "\n```"
