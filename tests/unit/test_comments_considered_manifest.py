"""T013: ManifestValidator unit tests.

Positive + negative cases per FR-028: bogus IDs rejected, missing truncation
acknowledged when truncation marker was present is rejected.
"""

from __future__ import annotations

import json
import unittest

from llmxive.feed.manifest import (
    ManifestValidator,
    emit_empty_manifest,
    parse_manifest_block,
)

VALID_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAA"
OTHER_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FBB"
BOGUS_ULID = "01XXXXXXXXXXXXXXXXXXXXXXXX"


def _feed():
    return [
        {"id": VALID_ULID, "kind": "personality_tick", "author": {"type": "agent", "name": "x"}, "summary": "a", "audit_status": "live"},
        {"id": OTHER_ULID, "kind": "review", "author": {"type": "agent", "name": "y"}, "summary": "b", "audit_status": "live"},
    ]


def _manifest(items=None, dispatch_id=VALID_ULID, ack=False):
    return {
        "dispatch_id": dispatch_id,
        "agent": "test-agent",
        "feed_snapshot_at": "2026-05-14T09:00:00.000000Z",
        "items": items or [],
        "truncation_acknowledged": ack,
    }


class TestManifestParse(unittest.TestCase):
    def test_parses_fenced_block(self):
        m = _manifest()
        output = "Some prose.\n\n```json comments-considered\n" + json.dumps(m) + "\n```"
        parsed = parse_manifest_block(output)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["dispatch_id"], VALID_ULID)

    def test_parses_without_json_info_string(self):
        m = _manifest()
        output = "Some prose.\n\n```comments-considered\n" + json.dumps(m) + "\n```"
        parsed = parse_manifest_block(output)
        self.assertIsNotNone(parsed)

    def test_no_block_returns_none(self):
        self.assertIsNone(parse_manifest_block("just prose with no manifest"))

    def test_malformed_json_returns_none(self):
        output = "prose\n\n```json comments-considered\n{not valid json\n```"
        self.assertIsNone(parse_manifest_block(output))


class TestManifestValidate(unittest.TestCase):
    def setUp(self):
        self.v = ManifestValidator(_feed())

    def test_valid_manifest_passes(self):
        m = _manifest(items=[{"feed_item_id": VALID_ULID, "response": "addressed"}])
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertTrue(r.ok, msg=r.reason)

    def test_bogus_feed_id_rejected(self):
        m = _manifest(items=[{"feed_item_id": BOGUS_ULID, "response": "addressed"}])
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertFalse(r.ok)
        self.assertIn("bogus", r.reason)

    def test_missing_truncation_ack_rejected_when_truncated(self):
        m = _manifest(items=[{"feed_item_id": VALID_ULID, "response": "addressed"}], ack=False)
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=True)
        self.assertFalse(r.ok)
        self.assertIn("truncation", r.reason)

    def test_dispatch_id_mismatch_rejected(self):
        m = _manifest(items=[], dispatch_id="01XXX_OTHER_DISPATCH_XXXXXX")
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertFalse(r.ok)
        self.assertIn("dispatch_id_mismatch", r.reason)

    def test_invalid_response_rejected(self):
        m = _manifest(items=[{"feed_item_id": VALID_ULID, "response": "ignored"}])
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertFalse(r.ok)
        self.assertIn("invalid_response", r.reason)

    def test_rebutted_without_reason_rejected(self):
        m = _manifest(items=[{"feed_item_id": VALID_ULID, "response": "rebutted"}])
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertFalse(r.ok)
        self.assertIn("reason_required", r.reason)

    def test_deferred_with_reason_accepted(self):
        m = _manifest(items=[{
            "feed_item_id": VALID_ULID, "response": "deferred",
            "reason": "outside my expertise",
        }])
        r = self.v.validate(m, dispatch_id=VALID_ULID, truncation_in_context=False)
        self.assertTrue(r.ok, msg=r.reason)

    def test_non_trivial_feed_ids_helper(self):
        ids = self.v.non_trivial_feed_ids()
        self.assertEqual(ids, {VALID_ULID, OTHER_ULID})


class TestEmitEmptyManifest(unittest.TestCase):
    def test_emit_and_roundtrip(self):
        block = emit_empty_manifest(
            dispatch_id=VALID_ULID, agent="x",
            feed_snapshot_at="2026-05-14T09:00:00.000000Z", truncation=False,
        )
        parsed = parse_manifest_block(block)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["dispatch_id"], VALID_ULID)
        self.assertEqual(parsed["items"], [])


if __name__ == "__main__":
    unittest.main()
