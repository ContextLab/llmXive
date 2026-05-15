"""T013: new spec-010 rubric axes (position, adjacent_work, interest_signal)."""

from __future__ import annotations

import unittest

from llmxive.audit.personality_rubric import (
    RubricScores,
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
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
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
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
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
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual(is_, 0)

    def test_abstain_with_no_adjacent_work_passes(self) -> None:
        fm = {"position": "abstain", "interest_signal": "Lovelace objection"}
        pp, aw, is_ = score_spec010_axes(fm, PERSONA_SIGNALS)
        self.assertEqual((pp, aw, is_), (1, 1, 1))

    def test_passes_requires_all_three_new_plus_three_of_four_legacy(self) -> None:
        # A contribution that passes legacy but doesn't have the new fields fails.
        body = "I disagree with this approach because Arxiv:2202.01933 is more compelling."
        contribution = {"action": "comment", "content": body}
        s = score_full(contribution, frontmatter={}, persona_interest_signals=PERSONA_SIGNALS)
        # Legacy axes can pass, but new axes fail → overall fail
        self.assertFalse(s.passes())
        # Now provide the missing frontmatter → should pass
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


class TestLegacyCompat(unittest.TestCase):
    def test_passes_legacy_only_still_works(self) -> None:
        body = "However, I doubt this conclusion. See arxiv:2202.01933 and the Babbage method."
        contribution = {"action": "comment", "content": body}
        s = score_full(contribution)
        # Without spec-010 frontmatter, the new pass() returns False...
        self.assertFalse(s.passes())
        # ...but the legacy pass rule still confirms the 4 axes are good.
        self.assertTrue(s.passes_legacy_only())


if __name__ == "__main__":
    unittest.main()
