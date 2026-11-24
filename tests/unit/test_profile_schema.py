"""Registry entries express a capability PROFILE, never a model id (spec 026 US5)."""
from __future__ import annotations

from typing import get_args

import pytest
import yaml

from llmxive.agents.registry import load as load_registry
from llmxive.config import repo_root
from llmxive.model_selection.profiles import PROFILES
from llmxive.types import AgentRegistryEntry, ProfileName

NO_LLM = "deterministic-no-llm"


def test_profile_name_literal_matches_the_canonical_profiles():
    """The schema layer declares the names WITHOUT importing model_selection
    (that would cycle). This test is what prevents the two drifting apart."""
    assert set(get_args(ProfileName)) - {NO_LLM} == set(PROFILES)


def test_registry_has_no_model_ids_at_all():
    raw = yaml.safe_load((repo_root() / "agents" / "registry.yaml").read_text())
    for agent in raw["agents"]:
        assert "default_model" not in agent, agent["name"]
        assert "default_backend" not in agent, agent["name"]
        assert "fallback_backends" not in agent, agent["name"]
        assert agent["profile"] in get_args(ProfileName), agent["name"]


def test_every_agent_loads_with_a_canonical_profile():
    agents = load_registry().agents
    assert len(agents) == 54
    assert sum(a.profile == NO_LLM for a in agents) == 1


def test_unknown_profile_is_a_load_time_failure():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="profile"):
        AgentRegistryEntry(
            name="bogus_agent", purpose="x" * 20, prompt_path="agents/prompts/x.md",
            prompt_version="1.0.0", profile="not_a_real_profile",
            wall_clock_budget_seconds=60,
        )


def test_no_llm_agent_is_bypassed_by_registry_dispatch():
    """US5 AC3 layer 1 (deferred here from Task 2, where entry.profile did not
    yet exist): the no-LLM agent is identified by its PROFILE, so dispatch can
    bypass it before any routing."""
    entries = {a.name: a for a in load_registry().agents}
    assert entries["paper_publisher"].profile == NO_LLM
    assert [n for n, e in entries.items() if e.profile == NO_LLM] == ["paper_publisher"]


def test_paid_opt_in_is_retained_and_defaults_false():
    """D7: the field stays (permission to configure a paid-PREFERRING default);
    it is NOT threaded into routing and does NOT gate the guarded paid tail."""
    assert all(a.paid_opt_in is False for a in load_registry().agents)
