"""Tests for `_is_bot_submitter` and the contributor-leaderboard exclusion.

The HF daily-papers cron files paper-submission issues as
``github-actions[bot]``. Per user request that bot identity must not appear
on the top-contributors ranking board, but it must remain visible on each
project's submitter line (so users can see how the paper got in) and the
paper's *authors* must still get credited via the paper-author rollup.
"""

from __future__ import annotations

from llmxive.web_data import _is_bot_submitter


class TestIsBotSubmitter:
    def test_github_actions_bot_literal(self) -> None:
        assert _is_bot_submitter("github-actions[bot]") is True

    def test_at_prefix_stripped(self) -> None:
        assert _is_bot_submitter("@github-actions[bot]") is True

    def test_case_insensitive(self) -> None:
        assert _is_bot_submitter("GitHub-Actions[bot]") is True
        assert _is_bot_submitter("GITHUB-ACTIONS") is True

    def test_known_bots_in_set(self) -> None:
        assert _is_bot_submitter("dependabot[bot]") is True
        assert _is_bot_submitter("renovate[bot]") is True

    def test_any_bracketed_bot_suffix(self) -> None:
        # belt-and-suspenders rule: anything ending in `[bot]`
        assert _is_bot_submitter("some-new-bot[bot]") is True

    def test_humans_are_not_bots(self) -> None:
        assert _is_bot_submitter("jeremyrmanning") is False
        assert _is_bot_submitter("ContextLab") is False

    def test_models_are_not_bots(self) -> None:
        assert _is_bot_submitter("qwen.qwen3.5-122b") is False
        assert _is_bot_submitter("Qwen/Qwen2.5-3B-Instruct") is False

    def test_empty_or_whitespace(self) -> None:
        assert _is_bot_submitter("") is False
        assert _is_bot_submitter("   ") is False
