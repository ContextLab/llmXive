"""Rotation `select_next` tests (T012, US1, FR-002 + FR-004).

Pure-Python. Verifies the deterministic lex-next-after-stem rule from
research.md § R1 against fixture pools of varying sizes and pointer
states.
"""

from __future__ import annotations

from llmxive.agents import personality as p


def _pool(slugs: list[str]) -> list[p.Personality]:
    """Build a list of Personality objects (only `slug` matters for the test)."""
    return [
        p.Personality(
            slug=s, display_name=s.replace("-", " ").title(),
            summary="summary", sources=["a", "b", "c"], prompt_body="body",
        )
        for s in sorted(slugs)
    ]


class TestSelectNext:
    def test_first_run_with_null_pointer(self) -> None:
        pool = _pool(["ada-lovelace", "daniel-kahneman", "socrates"])
        nxt = p.select_next(pool, last_used=None)
        assert nxt is not None
        assert nxt.slug == "ada-lovelace"

    def test_lex_next_after_each_slot(self) -> None:
        pool = _pool(["a", "b", "c", "d", "e"])
        # Walk the rotation through every slot.
        slugs = [pp.slug for pp in pool]
        assert p.select_next(pool, "a").slug == "b"
        assert p.select_next(pool, "b").slug == "c"
        assert p.select_next(pool, "c").slug == "d"
        assert p.select_next(pool, "d").slug == "e"

    def test_wraps_at_end(self) -> None:
        pool = _pool(["a", "b", "c", "d", "e"])
        # last_used is the LAST entry → wrap to first.
        assert p.select_next(pool, "e").slug == "a"

    def test_deleted_slug_as_pointer_advances_to_next_lex(self) -> None:
        # last_used is a slug NO LONGER in the pool (deleted between
        # ticks). The next persona is the lex-first slug > deleted_slug.
        pool = _pool(["ada-lovelace", "daniel-kahneman", "socrates"])
        # 'aristotle' is between ada and daniel lexicographically.
        nxt = p.select_next(pool, "aristotle")
        assert nxt.slug == "daniel-kahneman"

    def test_deleted_slug_past_end_wraps_to_first(self) -> None:
        # Deleted slug sorts AFTER every pool entry → wrap.
        pool = _pool(["a", "b", "c"])
        assert p.select_next(pool, "z").slug == "a"

    def test_empty_pool_returns_none(self) -> None:
        assert p.select_next([], None) is None
        assert p.select_next([], "anything") is None
