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

from llmxive.convergence import llm_reviewer
from llmxive.convergence.revisers import _self_consistency


def test_llm_reviewer_default_max_tokens_is_32768():
    sig = inspect.signature(llm_reviewer.LLMReviewer.__init__)
    assert sig.parameters["max_tokens"].default == 32_768


def test_self_consistency_reasoning_max_tokens_is_32768():
    assert _self_consistency._REASONING_MAX_TOKENS == 32_768


def test_router_generation_default_unchanged():
    """The generation default (131072) is for large-output GENERATION agents and
    must stay put — only the review/reviser budgets are bounded."""
    from llmxive.backends import router

    src = inspect.getsource(router.chat_with_fallback)
    assert "131_072" in src
