"""Slice 1A (spec 026) — the shared conservative token estimator + CallBudget
construction used on BOTH sides of the pure boundary (caller pre-select, execute
re-check). Offline; deterministic.
"""

from __future__ import annotations

from llmxive.backends.base import ChatMessage
from llmxive.model_selection.tokens import (
    call_budget_for,
    estimate_message_tokens,
    estimate_tokens,
    fits_budget,
)
from llmxive.model_selection.types import CallBudget
from llmxive.tools.summarize import estimate_tokens as summarize_estimate_tokens


def test_estimate_tokens_is_the_summarize_char4_estimator() -> None:
    # SSoT: tokens.py re-exports tools/summarize's single char/4 estimator.
    assert estimate_tokens is summarize_estimate_tokens
    assert estimate_tokens("abcd") == 1  # 4 chars / 4
    assert estimate_tokens("abcde") == 2  # rounds up


def test_estimate_message_tokens_over_estimates_content() -> None:
    msgs = [
        ChatMessage(role="system", content="You are a careful reviewer."),
        ChatMessage(role="user", content="x" * 400),
    ]
    est = estimate_message_tokens(msgs)
    # strictly greater than the bare content estimate (per-message + per-request
    # overhead is added) — the estimate is a deliberate UPPER bound.
    content_only = sum(estimate_tokens(m.content) for m in msgs)
    assert est > content_only


def test_call_budget_for_bounds_input_and_carries_output() -> None:
    msgs = [ChatMessage(role="user", content="hello world " * 50)]
    budget = call_budget_for(msgs, max_output_tokens=512)
    assert isinstance(budget, CallBudget)
    assert budget.max_output_tokens == 512
    # max_input_tokens is an upper bound on the actual estimated input.
    assert budget.max_input_tokens >= estimate_tokens(msgs[0].content)
    assert budget.max_input_tokens == estimate_message_tokens(msgs)


def test_fits_budget_accepts_within_bounds() -> None:
    msgs = [ChatMessage(role="user", content="short")]
    budget = call_budget_for(msgs, max_output_tokens=100)
    ok, reason = fits_budget(msgs, 100, budget)
    assert ok and reason is None


def test_fits_budget_rejects_input_overflow() -> None:
    msgs = [ChatMessage(role="user", content="y" * 4000)]
    tiny = CallBudget(max_input_tokens=5, max_output_tokens=100)
    ok, reason = fits_budget(msgs, 100, tiny)
    assert not ok and "input" in reason


def test_fits_budget_rejects_output_overflow() -> None:
    msgs = [ChatMessage(role="user", content="short")]
    budget = call_budget_for(msgs, max_output_tokens=100)
    ok, reason = fits_budget(msgs, 9999, budget)
    assert not ok and "max_tokens" in reason


def test_estimator_handles_dict_and_str_messages() -> None:
    # robustness: dict-shaped and raw-str messages, not only ChatMessage objects.
    dict_msgs = [{"role": "user", "content": "hello there"}]
    str_msgs = ["hello there"]
    assert estimate_message_tokens(dict_msgs) > 0
    assert estimate_message_tokens(str_msgs) > 0
