"""Guard the reasoning-safe (but bounded) max_tokens defaults for review/reviser.

qwen3.5-122b is a reasoning model: a measured full-spec review used ~9.7K
completion tokens. The old 131_072 default gave the model so much budget it
could keep reasoning well past the wall-clock deadline (→ hang). 32_768 is ~3x
the measured headroom — enough for any real verdict, small enough that reasoning
finishes inside the (reasoning) deadline.

The router/generation default (131072, for spec/plan/tasks GENERATION agents that
legitimately emit huge outputs) is deliberately NOT bounded here — see
``src/llmxive/backends/router.py``.
"""

from __future__ import annotations

import inspect

from llmxive.backends import router
from llmxive.convergence import llm_reviewer


def test_llm_reviewer_default_max_tokens_is_32768():
    sig = inspect.signature(llm_reviewer.LLMReviewer.__init__)
    assert sig.parameters["max_tokens"].default == 32_768


def test_central_reasoning_budget_is_32768():
    """The reviser (and every other analysis/reasoning caller) now routes through
    router.reasoning_chat, which defaults to the SINGLE-source-of-truth
    REASONING_MAX_TOKENS (was duplicated per-module)."""
    assert router.REASONING_MAX_TOKENS == 32_768


def test_router_generation_default_unchanged():
    """The generation budget (131072, for large-output GENERATION agents) must
    stay put — only the analysis/reasoning budget is the smaller 32K. Both are now
    single named constants in the router."""
    assert router.GENERATION_MAX_TOKENS == 131_072
    # chat_with_fallback applies the generation budget when the caller omits one.
    src = inspect.getsource(router.chat_with_fallback)
    assert "GENERATION_MAX_TOKENS" in src


def test_specialist_reviewers_use_the_reasoning_budget():
    """The SPECIALIST reviewers (base-Agent path) must carry the SAME reasoning-safe
    bound as the convergence LLMReviewer. The base Agent omitted max_tokens, so they
    used the 131072 GENERATION default → a reasoning model hangs past the deadline,
    worst for the large-prompt artifact reviewers (code/data/filesystem), leaving
    review coverage perpetually incomplete (3/7) so no project ever advanced."""
    from llmxive.agents.paper_reviewer import PaperReviewerAgent
    from llmxive.agents.research_reviewer import ResearchReviewerAgent

    assert ResearchReviewerAgent.chat_max_tokens == router.REASONING_MAX_TOKENS
    assert PaperReviewerAgent.chat_max_tokens == router.REASONING_MAX_TOKENS


def test_base_agent_threads_chat_max_tokens_into_the_call():
    """base.Agent.run must pass its chat_max_tokens to chat_with_fallback (else the
    reviewer bound is silently ignored and the router applies the 131072 default)."""
    import inspect

    from llmxive.agents import base

    src = inspect.getsource(base.Agent.run)
    assert "max_tokens=self.chat_max_tokens" in src


def test_generative_agents_keep_the_generation_budget():
    """The base default is None (→ router GENERATION budget): generative agents
    (brainstorm/flesh_out) legitimately emit large documents and must NOT be capped
    to the reasoning budget — only the short-verdict reasoning reviewers are."""
    from llmxive.agents.base import Agent

    assert Agent.chat_max_tokens is None
