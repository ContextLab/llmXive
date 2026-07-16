"""Conservative token estimation for model selection (spec 026, slice 1A).

ONE shared, deliberately-over-estimating token estimator, used at BOTH ends of
the boundary so a real call never exceeds a budget the selector approved:

- the **selection caller** builds/validates a :class:`CallBudget` from the actual
  messages via :func:`call_budget_for` BEFORE calling the pure ``select`` (so
  ``max_input_tokens`` is an UPPER bound on the real input); and
- ``execute`` re-checks the actual messages against the ``CallBudget`` via
  :func:`fits_budget` (fail-fast) — ``select`` has no messages, only the budget.

The char/÷4 primitive is REUSED from ``tools/summarize.estimate_tokens`` (the
single char-count estimator, Constitution I); this module adds the chat-message
serialization + fixed per-message / per-request overhead. ``select`` itself never
imports this — it only reads the ``CallBudget`` and stays pure.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from llmxive.model_selection.types import CallBudget
from llmxive.tools.summarize import estimate_tokens

__all__ = [
    "call_budget_for",
    "estimate_message_tokens",
    "estimate_tokens",
    "fits_budget",
]

#: Fixed overhead ADDED to the char/÷4 content estimate. Chat APIs wrap each
#: message with role tags + delimiters and each request with system/tool framing.
_PER_MESSAGE_OVERHEAD_TOKENS = 8
_REQUEST_OVERHEAD_TOKENS = 16

#: Multiplicative safety margin applied to the char/÷4 estimate (C2). char/4 is the
#: AVERAGE English ratio, not an upper bound — token-dense inputs (code, punctuation,
#: CJK, whitespace) tokenize to MORE than len/4. Since this estimate sizes
#: ``worst_case_credits`` (which the reservation ledger holds), under-estimating would
#: UNDER-reserve and re-open an overspend window. This margin makes the estimate
#: conservative for realistic prose/code; it is NOT a hard bound for adversarial
#: single-char text (whose true ceiling is len(content)) — acceptable because llmXive
#: inputs are prose/code and the fresh-spend re-check backstops residual under-count.
_SAFETY_MARGIN = 1.5


def _role_content(message: Any) -> tuple[str, str]:
    """Extract ``(role, content)`` from a ``ChatMessage`` object, a mapping, or —
    as a last resort — the object's ``str``. Non-str content (e.g. a vision
    parts list) is coerced to ``str`` so the char estimate stays conservative."""
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    if role is None and content is None and isinstance(message, dict):
        role = message.get("role")
        content = message.get("content")
    if content is None:
        content = message if isinstance(message, str) else str(message)
    return str(role or ""), str(content)


def estimate_message_tokens(messages: Iterable[Any]) -> int:
    """Conservative UPPER-bound token estimate for a chat request: the char/÷4
    estimate of every message's role + content, plus fixed per-message and
    per-request overhead."""
    total = _REQUEST_OVERHEAD_TOKENS
    for m in messages:
        role, content = _role_content(m)
        total += _PER_MESSAGE_OVERHEAD_TOKENS + estimate_tokens(role) + estimate_tokens(content)
    return math.ceil(total * _SAFETY_MARGIN)  # conservative headroom (C2) — over-, not under-count


def call_budget_for(messages: Iterable[Any], max_output_tokens: int) -> CallBudget:
    """Build the :class:`CallBudget` to price a call, from its ACTUAL messages.

    ``max_input_tokens`` is the conservative over-estimate of the input (so a
    selected candidate is guaranteed to fit), paired with the caller's requested
    ``max_output_tokens``. Called by the selection caller BEFORE ``select`` (which
    only reads the resulting budget)."""
    return CallBudget(
        max_input_tokens=estimate_message_tokens(messages),
        max_output_tokens=max_output_tokens,
    )


def fits_budget(
    messages: Iterable[Any], requested_output_tokens: int, budget: CallBudget
) -> tuple[bool, str | None]:
    """``execute``'s fail-fast re-check against the priced budget: the actual
    messages' estimated input must not exceed ``budget.max_input_tokens`` AND the
    requested output must not exceed ``budget.max_output_tokens``. Returns
    ``(ok, reason)`` — ``reason`` is a human-readable breach description or
    ``None`` when it fits."""
    estimated_input = estimate_message_tokens(messages)
    if estimated_input > budget.max_input_tokens:
        return False, (
            f"estimated input {estimated_input} exceeds "
            f"call_budget.max_input_tokens {budget.max_input_tokens}"
        )
    if requested_output_tokens > budget.max_output_tokens:
        return False, (
            f"requested max_tokens {requested_output_tokens} exceeds "
            f"call_budget.max_output_tokens {budget.max_output_tokens}"
        )
    return True, None
