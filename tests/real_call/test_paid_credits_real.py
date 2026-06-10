"""Real-call: Dartmouth daily-credit balance + the paid-model guard (issue #295).

Fast (PR-gate) parts: fetch the real balance endpoint; confirm the backend
refuses a paid model without opt-in (no spend incurred).

Slow (nightly) part: one deliberately tiny opted-in claude-haiku call
(~0.03 credits =~ $0.00003 list-price) verifying the full path: guard
approves -> call succeeds -> real cost estimate logged -> server-side
spend increases.
"""

from __future__ import annotations

import os

import pytest

requires_key = pytest.mark.skipif(
    not (
        os.environ.get("DARTMOUTH_CHAT_API_KEY")
        or os.path.exists(
            os.path.expanduser("~/.config/llmxive/credentials.toml")
        )
    ),
    reason="No Dartmouth credentials configured",
)


@requires_key
def test_fetch_credit_balance_real() -> None:
    from llmxive.backends.credits import fetch_credit_balance

    balance = fetch_credit_balance()
    assert balance.max_budget > 0
    assert 0 <= balance.spend
    assert balance.budget_duration  # e.g. "1d"
    assert balance.budget_reset_at  # ISO timestamp
    # The measured account shape (2026-06-10): 2000 credits/day. Don't pin
    # the exact number (policy may change); sanity-bound it instead.
    assert balance.max_budget >= 1.0


@requires_key
def test_paid_model_refused_without_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """The backend must refuse a paid model when LLMXIVE_PAID_OPT_IN is unset
    — this is the live free-first guard (no credits are spent)."""
    from llmxive.backends.base import ChatMessage, PermanentBackendError
    from llmxive.backends.dartmouth import DartmouthBackend

    monkeypatch.delenv("LLMXIVE_PAID_OPT_IN", raising=False)
    backend = DartmouthBackend()
    with pytest.raises(PermanentBackendError, match="LLMXIVE_PAID_OPT_IN"):
        backend.chat(
            [ChatMessage(role="user", content="Reply with exactly: ok")],
            model="anthropic.claude-haiku-4-5-20251001",
            max_tokens=8,
        )


@pytest.mark.slow
@requires_key
def test_tiny_paid_call_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opted-in tiny paid call: guard approves, call succeeds, the real cost
    estimate is non-zero, and the server-side daily spend advances."""
    from llmxive.backends import credits
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.dartmouth import DartmouthBackend

    monkeypatch.setenv("LLMXIVE_PAID_OPT_IN", "1")
    credits.reset_balance_cache()
    before = credits.fetch_credit_balance()
    if before.spend >= credits.budget_fraction() * before.max_budget:
        pytest.skip("daily credit cap already reached; not spending past it")

    backend = DartmouthBackend()
    response = backend.chat(
        [ChatMessage(role="user", content="Reply with exactly: ok")],
        model="anthropic.claude-haiku-4-5-20251001",
        max_tokens=8,
    )
    assert response.text.strip()
    assert response.cost_estimate_usd > 0  # honest paid accounting

    # Server-side metering is asynchronous (observed lag: a few seconds to
    # tens of seconds) — poll briefly rather than asserting instantly.
    import time

    after = before
    for wait in (3, 5, 10, 15, 30):
        time.sleep(wait)
        credits.reset_balance_cache()
        after = credits.fetch_credit_balance()
        if after.spend > before.spend:
            break
    assert after.spend > before.spend  # the server metered the call
    # 1 credit == $0.001: the spend delta (credits) should be ~1000x the
    # USD estimate. Allow generous tolerance for token-count variance.
    delta = after.spend - before.spend
    assert delta == pytest.approx(response.cost_estimate_usd * 1000.0, rel=0.5)
