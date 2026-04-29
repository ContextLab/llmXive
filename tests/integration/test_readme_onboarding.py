"""Integration test (T143): SC-008 README onboarding validation.

A new contributor must be able to find any agent's prompt within 5
minutes by reading the top-level README. This test asserts the README
mentions the three onramp components:

  1. A link to agents/registry.yaml.
  2. A link to agents/prompts/ (the prompt directory).
  3. A one-paragraph "how to find the agent for stage X" recipe.

Pure file-fixture-driven; no LLM calls.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def test_readme_links_to_agent_registry() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert "agents/registry.yaml" in text, (
        "README must link to agents/registry.yaml so new contributors can "
        "find every agent in one place (SC-008)"
    )


def test_readme_links_to_prompts_dir() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert "agents/prompts" in text, (
        "README must reference agents/prompts/ so contributors know where "
        "prompt templates live (SC-008)"
    )


def test_readme_documents_lookup_recipe() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8").lower()
    # The README should contain a one-paragraph recipe for finding the
    # agent that owns a stage. Check for representative phrasing.
    has_recipe = any(
        phrase in text
        for phrase in (
            "follow the agent's `prompt_path:`",
            "follow the agent's prompt_path",
            "find the agent for",
            "stage you want to understand",
        )
    )
    assert has_recipe, (
        "README must contain a one-paragraph recipe for locating a stage's "
        "agent (per SC-008's 5-minute onboarding criterion)"
    )
