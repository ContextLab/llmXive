"""Persona prompt-file schema validation (T049, US4, FR-013).

Validates every file under ``agents/prompts/personalities/`` against
``contracts/personality-prompt-frontmatter.schema.yaml``. The
front-matter rules — required fields, slug pattern, summary word
count, sources length 3-6 -- are enforced by the loader. This test is
the structural integrity check that runs on every commit.

PER F4 NOTE: this test also serves as the HOOK for the human-review of
each persona's grounding sources. Maintainers should spot-check 3
random sources per persona by web-searching the title before
considering the persona "ratified" for production rotation. The
unit-test layer can only check WELL-FORMEDNESS — not whether the
citations are real (that's the human review).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.agents import personality as p

REPO = Path(__file__).resolve().parents[2]
POOL_DIR = REPO / p.POOL_PATH


@pytest.mark.skipif(not POOL_DIR.is_dir(), reason="personalities pool dir not present")
class TestPoolValidates:
    def test_pool_loads_with_no_errors(self) -> None:
        result = p.load_pool(POOL_DIR)
        # 0 errors — every well-formed file in the pool passes the loader's
        # schema validation (front-matter, slug pattern, summary length,
        # sources length, non-empty body).
        assert result.error_count == 0, (
            f"persona prompt files failed schema validation: {result.errors}"
        )
        # We expect AT LEAST the 10 v1 personalities (the user may add more
        # later — Story 2 / FR-020 — and they'll pick up here automatically).
        assert len(result.personalities) >= 10, (
            f"expected ≥ 10 personalities in pool, got {len(result.personalities)}"
        )

    def test_every_personality_has_real_sources(self) -> None:
        """Belt-and-suspenders: every persona has at least 3 sources, all
        non-empty strings. The schema enforces this — this test just makes
        it explicit + easy to diff in CI."""
        result = p.load_pool(POOL_DIR)
        for persona in result.personalities:
            assert 3 <= len(persona.sources) <= 6, (
                f"{persona.slug}: sources count {len(persona.sources)} not in [3..6]"
            )
            for s in persona.sources:
                assert isinstance(s, str) and len(s.strip()) >= 5, (
                    f"{persona.slug}: bogus source {s!r}"
                )

    def test_no_display_name_has_baked_in_suffix(self) -> None:
        """FR-010 invariant — display_name MUST NOT end with ' (simulated)'.
        Loader already rejects, but make the assertion explicit."""
        result = p.load_pool(POOL_DIR)
        for persona in result.personalities:
            assert not persona.display_name.endswith(" (simulated)"), persona.slug

    def test_canonical_pool_present(self) -> None:
        """The intended canonical roster must all be present — adding
        more is fine (extensibility), but these are the baseline.

        Roster as of 2026-05-16: 8 v1 personas (Aristotle and Socrates
        were rotated out in favor of 7 modern scientific figures whose
        intellectual moves more directly engage the kind of work
        llmXive produces; the v1 philosophers' framings tended to
        produce critique that read more like commentary than review)."""
        result = p.load_pool(POOL_DIR)
        slugs = {p.slug for p in result.personalities}
        canonical = {
            # v1 retained
            "ada-lovelace", "dan-rockmore", "daniel-kahneman",
            "david-krakauer", "geoffrey-west", "john-von-neumann",
            "marie-curie", "rosalind-franklin",
            # 2026-05-16 additions — replacing aristotle/socrates
            "alan-turing", "albert-einstein", "eric-kandel",
            "freeman-dyson", "linus-pauling", "richard-feynman",
            "stephen-wolfram",
        }
        missing = canonical - slugs
        assert not missing, f"canonical personas missing from pool: {sorted(missing)}"
