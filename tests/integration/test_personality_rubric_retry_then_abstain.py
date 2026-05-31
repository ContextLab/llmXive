"""T018: integration test for FR-004 + Clarification Q3 rubric gate.

Seeds a persona that produces deliberately rubric-failing output twice.
Asserts:
  (a) one retry happened (rubric hint passed to second LLM call)
  (b) `abstain` recorded with reason "rubric_failure_after_retry"
  (c) rejected contribution body persisted to .audit/rejected-contributions.jsonl
  (d) rotation pointer advanced (Q3 — quality failure, not infra)

Constitution III: real filesystem, no mocks of the rubric logic itself; the
LLM call is replaced by a deterministic fixture-returning stub so we can
control the rubric outcome.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llmxive.agents import personality as p
from llmxive.agents.personality import (
    ACTION_ABSTAIN,
    ACTION_COMMENT,
    OUTCOME_RUBRIC_REJECTED,
    Action,
    CatalogEntry,
    Personality,
    _rubric_gate_or_convert_to_abstain,
)


def _persona(slug: str = "test-persona") -> Personality:
    return Personality(
        slug=slug, display_name="Test Persona", summary="for tests",
        sources=["Test source"], prompt_body="test body",
    )


def _action_manufactured() -> Action:
    """An action that the rubric will reject: pure generic praise, no markers."""
    return Action(
        action=ACTION_COMMENT,
        reason="this is great",
        target_project_id="PROJ-TEST-001",
        target_artifact_kind="spec",
        target_artifact_path="projects/PROJ-TEST-001/specs/001-x/spec.md",
        content="Great work! Excellent article! Amazing idea!",
    )


def _action_strong() -> Action:
    """An action that passes the rubric."""
    return Action(
        action=ACTION_COMMENT,
        reason="objection + adjacent work",
        target_project_id="PROJ-TEST-001",
        target_artifact_kind="spec",
        target_artifact_path="projects/PROJ-TEST-001/specs/001-x/spec.md",
        content=(
            "I disagree with section 3's framing — the bound in lemma 2 only holds "
            "when the noise is sub-Gaussian. See Cover & Thomas (1991) for the "
            "general case. Could the authors clarify whether their experiments "
            "satisfy that assumption?"
        ),
    )


class TestRubricGateConvertsToAbstainOnDoubleFail(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="rubric_gate_test_"))
        (self.root / "projects" / "PROJ-TEST-001").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_double_failure_converts_to_abstain_and_persists(self):
        original = _action_manufactured()
        # Stub _call_llm_for_persona so retry returns another manufactured response.
        retry_payload = json.dumps({
            "action": "comment",
            "reason": "still nothing specific",
            "target": {
                "project_id": "PROJ-TEST-001",
                "artifact_kind": "spec",
                "artifact_path": "projects/PROJ-TEST-001/specs/001-x/spec.md",
            },
            "content": "Wonderful paper! Fantastic work!",  # still manufactured
        })

        with patch.object(p, "_call_llm_for_persona", return_value=retry_payload):
            new_action, note = _rubric_gate_or_convert_to_abstain(
                original, "raw original body", _persona(),
                [CatalogEntry(id="PROJ-TEST-001", title="t", field="f",
                              current_stage="s", description="d",
                              recent_artifacts=[])],
                self.root,
            )

        # (b) abstain recorded with rubric_failure_after_retry reason
        self.assertEqual(new_action.action, ACTION_ABSTAIN)
        self.assertIn("rubric_failure_after_retry", new_action.reason)
        self.assertIn("rubric_failure_after_retry", note)

        # (c) rejected body persisted (the RETRY's body — the second failure)
        rejected_path = self.root / "projects" / "PROJ-TEST-001" / ".audit" / "rejected-contributions.jsonl"
        self.assertTrue(rejected_path.exists())
        record = json.loads(rejected_path.read_text().splitlines()[0])
        self.assertEqual(record["persona"], "test-persona")
        self.assertIn("Wonderful paper", record["rejected_body"])

    def test_retry_succeeds_returns_strong_action(self):
        original = _action_manufactured()
        # Retry produces a strong response this time
        retry_payload = json.dumps({
            "action": "comment",
            "reason": "found objection + pointer",
            "target": {
                "project_id": "PROJ-TEST-001",
                "artifact_kind": "spec",
                "artifact_path": "projects/PROJ-TEST-001/specs/001-x/spec.md",
            },
            "content": (
                "I disagree with section 3 — the bound in lemma 2 fails when "
                "the noise is sub-Gaussian; see Cover & Thomas (1991). Why did "
                "the authors not address this?"
            ),
        })

        with patch.object(p, "_call_llm_for_persona", return_value=retry_payload):
            new_action, note = _rubric_gate_or_convert_to_abstain(
                original, "raw original body", _persona(),
                [CatalogEntry(id="PROJ-TEST-001", title="t", field="f",
                              current_stage="s", description="d",
                              recent_artifacts=[])],
                self.root,
            )

        self.assertEqual(new_action.action, ACTION_COMMENT)
        self.assertIsNone(note)

    def test_strong_action_passes_first_time(self):
        # No retry — strong action passes immediately
        original = _action_strong()
        with patch.object(p, "_call_llm_for_persona", side_effect=Exception("should not be called")):
            new_action, note = _rubric_gate_or_convert_to_abstain(
                original, "raw original body", _persona(),
                [],
                self.root,
            )
        self.assertEqual(new_action.action, ACTION_COMMENT)
        self.assertIsNone(note)


class TestAdvancingOutcomes(unittest.TestCase):
    def test_rubric_rejected_is_advancing(self):
        # Quality failures advance the rotation (Q3); infra failures hold.
        self.assertIn(OUTCOME_RUBRIC_REJECTED, p.ADVANCING_OUTCOMES)
        self.assertIn(p.OUTCOME_COMMITTED, p.ADVANCING_OUTCOMES)
        self.assertIn(p.OUTCOME_ABSTAINED, p.ADVANCING_OUTCOMES)
        # Infrastructure failures NOT in the advancing set
        self.assertNotIn(p.OUTCOME_RATE_LIMITED, p.ADVANCING_OUTCOMES)
        self.assertNotIn(p.OUTCOME_MODEL_ERROR, p.ADVANCING_OUTCOMES)
        self.assertNotIn(p.OUTCOME_MALFORMED, p.ADVANCING_OUTCOMES)
        self.assertNotIn(p.OUTCOME_TIMEOUT, p.ADVANCING_OUTCOMES)


if __name__ == "__main__":
    unittest.main()
