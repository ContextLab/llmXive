"""T013: new spec-010 rubric axes (position, adjacent_work, interest_signal)."""

from __future__ import annotations

import unittest

from llmxive.audit.personality_rubric import (
    score_full,
    score_spec010_axes,
)

PERSONA_SIGNALS = ["Lovelace objection", "symbolic computation", "Bernoulli algorithm"]


class TestSpec010Axes(unittest.TestCase):
    def test_all_three_axes_pass(self) -> None:
        fm = {
            "position": "lean_against",
            "adjacent_work": [
                {
                    "kind": "arxiv",
                    "pointer": "2202.01933",
                    "title": "x",
                    "verified_at": "2026-05-15T00:00:00Z",
                }
            ],
            "interest_signal": "Lovelace objection",
        }
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual((pp, aw, is_), (1, 1, 1))

    def test_missing_position(self) -> None:
        fm = {
            "adjacent_work": [
                {
                    "kind": "arxiv",
                    "pointer": "2202.01933",
                    "title": "x",
                    "verified_at": "2026-05-15T00:00:00Z",
                }
            ],
            "interest_signal": "Lovelace objection",
        }
        pp, _aw, _is = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual(pp, 0)

    def test_unverified_adjacent_work_fails_axis(self) -> None:
        fm = {
            "position": "lean_toward",
            "adjacent_work": [
                {"kind": "arxiv", "pointer": "2202.01933", "title": "x"}
                # no verified_at
            ],
            "interest_signal": "Lovelace objection",
        }
        _pp, aw, _is = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual(aw, 0)

    def test_interest_signal_not_in_persona_signals(self) -> None:
        fm = {
            "position": "lean_toward",
            "adjacent_work": [
                {
                    "kind": "arxiv",
                    "pointer": "2202.01933",
                    "title": "x",
                    "verified_at": "2026-05-15T00:00:00Z",
                }
            ],
            "interest_signal": "Some Other Signal Not In The List",
        }
        _pp, _aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual(is_, 0)

    def test_abstain_with_no_adjacent_work_passes(self) -> None:
        fm = {"position": "abstain", "interest_signal": "Lovelace objection"}
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual((pp, aw, is_), (1, 1, 1))

    def test_passes_requires_all_three_new_when_partially_scored(self) -> None:
        # A contribution that has PARTIAL spec-010 frontmatter (e.g. only
        # position) fails the spec-010 strict check, because at least one axis
        # is >0 so backward-compat fallback is bypassed.
        body = "I disagree with this approach because Arxiv:2202.01933 is more compelling."
        contribution = {"action": "comment", "content": body}
        partial_fm = {"position": "lean_against"}  # only position; missing adjacent + signal
        s = score_full(
            contribution, frontmatter=partial_fm, persona_interest_signals=PERSONA_SIGNALS
        )
        # position_present=1, but adjacent_work_verified=0 and signal=0 → strict fail
        self.assertFalse(s.passes(), f"expected partial frontmatter to fail; scores={s}")

        # Full frontmatter → all three new axes pass → overall pass
        good_fm = {
            "position": "lean_against",
            "adjacent_work": [
                {
                    "kind": "arxiv",
                    "pointer": "2202.01933",
                    "title": "x",
                    "verified_at": "2026-05-15T00:00:00Z",
                }
            ],
            "interest_signal": "Lovelace objection",
        }
        s2 = score_full(
            contribution, frontmatter=good_fm, persona_interest_signals=PERSONA_SIGNALS
        )
        self.assertTrue(s2.passes(), f"expected pass; scores={s2}")

    def test_empty_frontmatter_falls_back_to_legacy_rule(self) -> None:
        # Backward-compat: when NONE of the spec-010 axes are scored (e.g.
        # legacy callers without frontmatter), passes() must defer to the
        # 4-axis legacy rule. This preserves prior integration-test behaviour
        # (e.g. tests/integration/test_personality_librarian_gate.py).
        body = "I disagree with this approach because Arxiv:2202.01933 is more compelling."
        contribution = {"action": "comment", "content": body}
        s = score_full(contribution, frontmatter={}, persona_interest_signals=PERSONA_SIGNALS)
        self.assertTrue(s.passes(), f"expected legacy fallback to pass; scores={s}")


class TestLegacyCompat(unittest.TestCase):
    def test_passes_legacy_only_still_works(self) -> None:
        # With strong legacy axes and no spec-010 axes scored, both passes()
        # (via backward-compat fallback) AND passes_legacy_only() return True.
        body = "However, I doubt this conclusion. See arxiv:2202.01933 and the Babbage method."
        contribution = {"action": "comment", "content": body}
        s = score_full(contribution)
        self.assertTrue(s.passes(), f"expected legacy fallback to pass; scores={s}")
        self.assertTrue(s.passes_legacy_only())

    def test_legacy_only_rule_unaffected_by_new_axes(self) -> None:
        # passes_legacy_only() always uses the original 4-axis rule regardless
        # of the new axes being set.
        body = "Compelling work. arxiv:2202.01933 is highly relevant."
        contribution = {"action": "comment", "content": body}
        s = score_full(contribution)
        # Manually set the new axes to 0; legacy rule still depends on 4 axes only.
        self.assertTrue(s.passes_legacy_only())


if __name__ == "__main__":
    unittest.main()
