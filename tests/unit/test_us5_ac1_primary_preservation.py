"""US5 AC1 (BINDING): under the fixed migration snapshot every LLM agent's chain
leader equals its pre-migration default.

This is the acceptance test spec 026 US5/AC1 deferred to Slice 7 (see the
"Concern for a follow-up task" note on commit 3a6dd49a0d): every one of the 53
LLM-calling agents in ``agents/registry.yaml`` must still resolve to
``qwen.qwen3.5-122b`` — its pre-migration ``default_model`` — as the LEADER of
its resolved chain. This holds by construction today (the capability policy
ranks the ``qwen3.5`` family quality_tier 3 across cheap/standard/deep/vision,
see ``model_selection/policy.py``), but asserting it for ALL 53 agents (not a
sample) keeps this a real regression guard if the policy ever reranks a
family above qwen3.5 for some capability. ``paper_publisher`` is the one
agent exempt (deterministic, no LLM call — never reaches selection at all).
"""

from __future__ import annotations

import pytest

from llmxive.agents.registry import load as load_registry
from llmxive.model_selection.profiles import build_requirement
from llmxive.model_selection.select import select
from llmxive.model_selection.types import CallBudget
from tests.unit.test_model_selection_select import _snapshot

LEGACY_DEFAULT = "qwen.qwen3.5-122b"
NO_LLM = "deterministic-no-llm"
_CB = CallBudget(max_input_tokens=1000, max_output_tokens=500)

_LLM_AGENTS = [a for a in load_registry().agents if a.profile != NO_LLM]


def test_there_are_53_llm_agents_and_one_exempt():
    assert len(_LLM_AGENTS) == 53
    assert [a.name for a in load_registry().agents if a.profile == NO_LLM] == ["paper_publisher"]


@pytest.mark.parametrize("agent", _LLM_AGENTS, ids=lambda a: a.name)
def test_every_llm_agent_preserves_its_primary(agent):
    chain = select(build_requirement(agent.profile, _CB), _snapshot())
    assert chain.candidates[0].model_ref.model_id == LEGACY_DEFAULT


def test_no_llm_agent_never_reaches_selection():
    from llmxive.backends.base import ChatMessage
    from llmxive.model_selection.route import DETERMINISTIC_NO_LLM, route_chat

    with pytest.raises(ValueError):
        route_chat([ChatMessage(role="user", content="x")],
                   profile=DETERMINISTIC_NO_LLM, max_tokens=10)
