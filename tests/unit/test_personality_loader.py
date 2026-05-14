"""Personality pool loader tests (spec 008 Phase 2 / FR-001 / Story 2 scenario 2).

Pure-Python — no LLM, no network. Drives :func:`personality.load_pool` against
tmp-dir fixtures covering valid loads, every malformed-file rejection rule, and
the empty-pool case.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


def _make_pool(tmp_path: Path, *names: str) -> Path:
    """Copy named fixture files into a tmp pool dir and return its path."""
    pool = tmp_path / "personalities"
    pool.mkdir()
    for n in names:
        shutil.copy(FIXTURES / n, pool / n)
    return pool


class TestLoadPool:
    def test_loads_well_formed_personality(self, tmp_path: Path) -> None:
        pool = _make_pool(tmp_path, "kahneman.md")
        res = p.load_pool(pool)
        assert len(res.personalities) == 1
        kahneman = res.personalities[0]
        assert kahneman.slug == "kahneman"
        assert kahneman.display_name == "Daniel Kahneman"
        assert "Princeton" in kahneman.summary
        assert len(kahneman.sources) == 4
        assert kahneman.version == "1.0.0"
        assert "Quiet, precise, deliberate" in kahneman.prompt_body
        assert res.error_count == 0
        assert res.errors == []

    def test_malformed_file_skipped_with_warning(self, tmp_path: Path, caplog) -> None:
        pool = _make_pool(tmp_path, "kahneman.md", "malformed-no-name.md")
        res = p.load_pool(pool)
        # kahneman survives; the malformed one is dropped.
        assert {p.slug for p in res.personalities} == {"kahneman"}
        assert res.error_count == 1
        assert "display_name" in res.errors[0]["reason"]

    def test_empty_pool_returns_empty_list(self, tmp_path: Path) -> None:
        pool = tmp_path / "personalities"
        pool.mkdir()
        res = p.load_pool(pool)
        assert res.personalities == []
        assert res.error_count == 0

    def test_missing_pool_directory_returns_empty(self, tmp_path: Path) -> None:
        # Pool dir doesn't exist — recover gracefully.
        res = p.load_pool(tmp_path / "does-not-exist")
        assert res.personalities == []
        assert res.error_count == 0

    def test_baked_in_simulated_suffix_rejected(self, tmp_path: Path) -> None:
        # FR-010 invariant: display_name must NOT bake in the suffix.
        bad = tmp_path / "personalities" / "bad.md"
        bad.parent.mkdir()
        bad.write_text(
            '---\n'
            'display_name: "Daniel Kahneman (simulated)"\n'
            'summary: "Bad — suffix in display_name."\n'
            'sources: ["a", "b", "c"]\n'
            '---\nbody\n', encoding="utf-8")
        res = p.load_pool(bad.parent)
        assert res.personalities == []
        assert res.error_count == 1
        assert "(simulated)" in res.errors[0]["reason"]

    def test_summary_over_14_words_rejected(self, tmp_path: Path) -> None:
        bad = tmp_path / "personalities" / "wordy.md"
        bad.parent.mkdir()
        bad.write_text(
            '---\n'
            'display_name: "Test Persona"\n'
            'summary: "' + " ".join("word"+str(i) for i in range(20)) + '"\n'
            'sources: ["a-source", "b-source", "c-source"]\n'
            '---\nbody\n', encoding="utf-8")
        res = p.load_pool(bad.parent)
        assert res.error_count == 1
        assert "summary > 14 words" in res.errors[0]["reason"]

    def test_sources_must_be_3_to_6(self, tmp_path: Path) -> None:
        bad = tmp_path / "personalities" / "few-sources.md"
        bad.parent.mkdir()
        bad.write_text(
            '---\n'
            'display_name: "Test Persona"\n'
            'summary: "Has only two sources, fails."\n'
            'sources: ["a-source", "b-source"]\n'
            '---\nbody\n', encoding="utf-8")
        res = p.load_pool(bad.parent)
        assert res.error_count == 1
        assert "3-6 strings" in res.errors[0]["reason"]

    def test_slug_pattern_enforced(self, tmp_path: Path) -> None:
        # Uppercase filename → invalid slug.
        bad = tmp_path / "personalities" / "BadSlug.md"
        bad.parent.mkdir()
        bad.write_text(
            '---\n'
            'display_name: "Test Persona"\n'
            'summary: "OK summary."\n'
            'sources: ["a-source", "b-source", "c-source"]\n'
            '---\nbody\n', encoding="utf-8")
        res = p.load_pool(bad.parent)
        assert res.personalities == []
        assert "slug" in res.errors[0]["reason"]

    def test_pool_returned_sorted_by_slug(self, tmp_path: Path) -> None:
        # Add a second valid personality after kahneman to verify ordering.
        pool = _make_pool(tmp_path, "kahneman.md")
        (pool / "aristotle.md").write_text(
            '---\n'
            'display_name: "Aristotle"\n'
            'summary: "Classical Greek philosopher; systematic taxonomist."\n'
            'sources: ["Nicomachean Ethics", "Metaphysics", "Categories"]\n'
            '---\nbody\n', encoding="utf-8")
        res = p.load_pool(pool)
        slugs = [p.slug for p in res.personalities]
        assert slugs == sorted(slugs)
        assert slugs[0] == "aristotle"
        assert slugs[1] == "kahneman"
