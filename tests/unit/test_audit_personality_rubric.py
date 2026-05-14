"""T016: personality rubric unit tests.

Positive fixtures (real contributions with markers) + negative fixtures
(one marker missing each, manufactured-praise example). Per research.md §4.
"""

from __future__ import annotations

import unittest

from llmxive.audit.personality_rubric import (
    audit_contribution,
    is_manufactured,
    score,
)


def _tick(content: str, action: str = "comment", **extra):
    item = {
        "id": "01ARZ3NDEKTSV4RRFFQ69G5FAA",
        "kind": "personality_tick",
        "action": action,
        "content": content,
        **extra,
    }
    return item


class TestRubricCriticalJudgement(unittest.TestCase):
    def test_objection_marker_scores(self):
        s = score(_tick("This is interesting, but I disagree with the claim that X."))
        self.assertGreaterEqual(s.critical_judgement, 1)

    def test_no_objection_zero(self):
        s = score(_tick("This is a great paper that I enjoyed reading."))
        self.assertEqual(s.critical_judgement, 0)


class TestRubricCuratorialPointer(unittest.TestCase):
    def test_arxiv_pointer(self):
        s = score(_tick("Compare to arxiv:2301.01234 which addresses this directly."))
        self.assertGreaterEqual(s.curatorial_pointer, 1)

    def test_quoted_title_pointer(self):
        s = score(_tick(
            'See "Quantum Theory and Measurement" for the historical antecedent of this approach.'
        ))
        self.assertGreaterEqual(s.curatorial_pointer, 1)

    def test_url_pointer(self):
        s = score(_tick("Background: https://example.org/paper.pdf"))
        self.assertGreaterEqual(s.curatorial_pointer, 1)

    def test_named_technique_pointer(self):
        s = score(_tick("This is essentially the Metropolis-Hastings algorithm applied to..."))
        self.assertGreaterEqual(s.curatorial_pointer, 1)

    def test_curatorial_pointer_field_dominates(self):
        s = score(_tick("Plain prose.", curatorial_pointer={"kind": "paper", "ref": "X"}))
        self.assertEqual(s.curatorial_pointer, 3)

    def test_no_pointer_zero(self):
        s = score(_tick("This makes sense and I like it."))
        self.assertEqual(s.curatorial_pointer, 0)


class TestRubricHonesty(unittest.TestCase):
    def test_generic_praise_alone_is_manufactured(self):
        s = score(_tick("Great work! Excellent article! Amazing idea!"))
        self.assertEqual(s.honesty, 0)

    def test_generic_praise_with_specific_rescue(self):
        s = score(_tick("Great work, but the bound in lemma 2 looks tight."))
        # generic + specific objection -> honesty 1 (or maybe higher)
        self.assertGreaterEqual(s.honesty, 1)

    def test_no_generic_praise_honest(self):
        s = score(_tick("The author's claim about X seems wrong; see Cover & Thomas (1991)."))
        self.assertEqual(s.honesty, 3)


class TestIsManufactured(unittest.TestCase):
    def test_manufactured_when_all_four_axes_missing(self):
        # No objection, no question, no pointer, no specific praise -> manufactured
        m, missing = is_manufactured(_tick("Great work! Excellent article!"))
        self.assertTrue(m)
        self.assertIn("specific_objection", missing)
        self.assertIn("specific_question", missing)
        self.assertIn("adjacent_work_pointer", missing)

    def test_not_manufactured_with_question(self):
        m, missing = is_manufactured(_tick("Have you considered the alternative encoding?"))
        self.assertFalse(m)
        self.assertNotIn("specific_question", missing)

    def test_not_manufactured_with_pointer(self):
        m, missing = is_manufactured(_tick(
            "Reminiscent of arxiv:2301.01234 — same construction, different domain."
        ))
        self.assertFalse(m)


class TestAuditContribution(unittest.TestCase):
    def test_passes_strong_contribution(self):
        item = audit_contribution(_tick(
            "I disagree with section 3's framing — the bound in lemma 2 only holds when "
            "the noise is sub-Gaussian. See Cover & Thomas (1991) for the general case. "
            "Could the authors clarify whether their experiments satisfy that assumption?",
        ))
        self.assertEqual(item.classification, "passes")
        self.assertGreaterEqual(item.rubric_scores["critical_judgement"], 1)
        self.assertGreaterEqual(item.rubric_scores["curatorial_pointer"], 1)

    def test_fails_weak_manufactured(self):
        item = audit_contribution(_tick("Great work! Excellent article!"))
        self.assertEqual(item.classification, "fails")
        # rules_fired is a list of RuleFired dataclass instances
        rule_ids = [r.rule_id for r in item.rules_fired]
        self.assertIn("manufactured", rule_ids)

    def test_abstain_passes(self):
        item = audit_contribution(_tick("", action="abstain"))
        # abstain scored as honesty=3 elsewhere; this passes
        self.assertEqual(item.classification, "passes")


if __name__ == "__main__":
    unittest.main()
