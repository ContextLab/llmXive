"""Attribution-invariant tests (T026 + T028 + T030 + T031 + T033, US3).

Covers FR-010 / FR-011 / FR-012:
  - The `_resolve_alias` suffix-guard rejects simulated names
  - `display_name_for_render` always appends ' (simulated)' once
  - Run-log entries carry the right `model_kind`, `model_name`, `display_name`
  - Disclaimer footer appears in every committed artifact
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents import personality as p

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "personality"


# -- T026: _resolve_alias suffix guard -------------------------------------


class TestAliasResolverSuffixGuard:
    def test_simulated_suffix_never_mapped(self, tmp_path: Path) -> None:
        """A name ending in ' (simulated)' returns unchanged even when an
        alias entry maps the real name. (FR-011)"""
        from llmxive.web_data import _ALIAS_CACHE, _resolve_alias

        # Build an alias file that DOES map both names — the guard must
        # prevent the simulated form from collapsing.
        (tmp_path / "state").mkdir()
        (tmp_path / "state" / "contributor_aliases.yaml").write_text(
            yaml.safe_dump({
                "aliases": [
                    {
                        "canonical": "Daniel Kahneman",
                        "kind": "human",
                        "github": "kahneman",
                        "aliases": ["Daniel Kahneman", "Daniel Kahneman (simulated)", "kahneman"],
                    }
                ]
            }),
            encoding="utf-8",
        )
        # Clear cache so the test repo's file is read fresh.
        _ALIAS_CACHE.clear()
        try:
            # Simulated form is NOT merged into the canonical even though the
            # alias table tries to.
            canon, kind = _resolve_alias("Daniel Kahneman (simulated)", "llm", tmp_path)
            assert canon == "Daniel Kahneman (simulated)"
            assert kind == "llm"
            # Real form IS merged (no regression).
            canon, kind = _resolve_alias("kahneman", "human", tmp_path)
            assert canon == "Daniel Kahneman"
            assert kind == "human"
        finally:
            _ALIAS_CACHE.clear()

    def test_unrelated_simulated_name_returns_unchanged(self, tmp_path: Path) -> None:
        from llmxive.web_data import _ALIAS_CACHE, _resolve_alias
        _ALIAS_CACHE.clear()
        # No alias file at all.
        canon, kind = _resolve_alias("Marie Curie (simulated)", "llm", tmp_path)
        assert canon == "Marie Curie (simulated)"
        assert kind == "llm"


# -- T028: display_name_for_render ------------------------------------------


class TestDisplayNameForRender:
    def _persona(self, name: str) -> p.Personality:
        return p.Personality(
            slug=name.lower().replace(" ", "-"),
            display_name=name,
            summary="x",
            sources=["a-source", "b-source", "c-source"],
            prompt_body="body",
        )

    def test_appends_suffix(self) -> None:
        assert p.display_name_for_render(self._persona("Daniel Kahneman")) == "Daniel Kahneman (simulated)"

    def test_does_not_double_suffix(self) -> None:
        # If somehow a persona was constructed with a baked-in suffix
        # (loader rejects this, but be defensive), the renderer doesn't
        # append a second one.
        persona = self._persona("Daniel Kahneman (simulated)")
        assert p.display_name_for_render(persona) == "Daniel Kahneman (simulated)"

    def test_loader_rejects_baked_in_suffix(self, tmp_path: Path) -> None:
        """Cross-check with the loader: a persona file whose display_name
        ends in ' (simulated)' is rejected at load time, so the
        double-suffix case above is unreachable in practice."""
        bad = tmp_path / "pool" / "bad.md"
        bad.parent.mkdir(parents=True)
        bad.write_text(
            '---\n'
            'display_name: "Daniel Kahneman (simulated)"\n'
            'summary: "Bad — suffix in name."\n'
            'sources: ["one-source", "two-source", "three-source"]\n'
            '---\nbody\n',
            encoding="utf-8",
        )
        res = p.load_pool(bad.parent)
        assert res.error_count == 1
        assert "(simulated)" in res.errors[0]["reason"]


# -- T030: run-log entry shape (FR-010) ------------------------------------


class TestRunLogEntryShape:
    def test_entry_has_all_required_attribution_fields(self) -> None:
        # _build_log_entry is the function that constructs the JSONL entry.
        entry = p._build_log_entry(
            started=__import__("datetime").datetime(2026, 5, 14, 8, 30, tzinfo=__import__("datetime").timezone.utc),
            ended=__import__("datetime").datetime(2026, 5, 14, 8, 30, 11, tzinfo=__import__("datetime").timezone.utc),
            slug="daniel-kahneman",
            display_name="Daniel Kahneman (simulated)",
            action="comment",
            outcome=p.OUTCOME_COMMITTED,
            project_id="PROJ-001-mechanistic-interpretability-of-ctcf-bin",
            committed_paths=["projects/.../reviews/research/kahneman-simulated__05-14-2026__research.md"],
        )
        assert entry["agent_name"] == "personality"
        assert entry["model_name"] == "qwen.qwen3.5-122b"
        assert entry["model_kind"] == "personality_simulator"
        assert entry["personality_slug"] == "daniel-kahneman"
        assert entry["display_name"].endswith(" (simulated)")
        assert entry["outcome"] == "committed"
        assert "committed_paths" in entry


# -- T033: disclaimer footer in every committed artifact (FR-012) ----------


class TestDisclaimerFooterContent:
    def test_disclaimer_template_names_persona_and_model(self) -> None:
        persona = p.Personality(
            slug="kahneman", display_name="Daniel Kahneman",
            summary="x", sources=["a-source", "b-source", "c-source"], prompt_body="body",
        )
        footer = p._make_disclaimer(persona)
        # Persona name (with suffix) AND real-figure name AND model id
        # AND the platform name — all four strings present, per F8.
        assert "Daniel Kahneman (simulated)" in footer
        # Note: the template uses the bare "Daniel Kahneman" for real_name.
        assert "Daniel Kahneman" in footer
        assert "qwen-3.5-122b" in footer
        assert "Dartmouth Chat" in footer
        assert "simulated AI persona" in footer
        # Placement: starts with a horizontal-rule separator (F8).
        assert footer.lstrip("\n").startswith("---")


# -- T031: web-data integration — simulated and real entries stay distinct -


class TestWebDataSimulatedDistinct:
    def test_real_and_simulated_kahneman_are_separate_entries(self, tmp_path: Path) -> None:
        """Build a fixture run-log with both a real-person submitter AND
        a simulated-Kahneman contribution; verify the contributor list
        materialization keeps them distinct. End-to-end FR-011 check."""
        # We test the resolver layer (the contributor materialization in
        # web_data goes through `_resolve_alias`, which we just guarded).
        from llmxive.web_data import _ALIAS_CACHE, _resolve_alias

        (tmp_path / "state").mkdir()
        (tmp_path / "state" / "contributor_aliases.yaml").write_text(
            yaml.safe_dump({
                "aliases": [
                    {
                        "canonical": "Daniel Kahneman",
                        "kind": "human",
                        "aliases": ["dkahneman", "Daniel Kahneman", "DanielKahneman"],
                    }
                ]
            }),
            encoding="utf-8",
        )
        _ALIAS_CACHE.clear()
        try:
            # The real person, in any of his alias forms, collapses to canonical.
            real_canon, _real_kind = _resolve_alias("dkahneman", "human", tmp_path)
            assert real_canon == "Daniel Kahneman"
            # The simulated persona stays separate.
            sim_canon, _sim_kind = _resolve_alias("Daniel Kahneman (simulated)", "llm", tmp_path)
            assert sim_canon == "Daniel Kahneman (simulated)"
            # They are NOT equal — the website's contributor list will show
            # two distinct rows (FR-011).
            assert real_canon != sim_canon
        finally:
            _ALIAS_CACHE.clear()
