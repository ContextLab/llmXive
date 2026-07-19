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
    "MAX_IMAGE_BYTES",
    "MAX_IMAGE_DIMENSION_PX",
    "MAX_IMAGE_PIXELS",
    "TOKENS_PER_IMAGE",
    "call_budget_for",
    "estimate_message_tokens",
    "estimate_tokens",
    "fits_budget",
    "max_input_tokens_upper_bound",
]

#: Images are bounded BEFORE selection so the per-image charge below is a true
#: upper bound. Callers downscale to fit; an oversize ImagePart is REJECTED.
MAX_IMAGE_DIMENSION_PX = 1536
MAX_IMAGE_BYTES = 8 * 1024 * 1024

#: Independent pixel-COUNT ceiling — defense in depth alongside the per-side
#: MAX_IMAGE_DIMENSION_PX check above. Two images can each individually
#: satisfy the per-side bound (<=1536px on both axes) yet differ enormously in
#: decode/memory cost by aspect ratio; the per-side check alone bounds neither
#: the total pixel count nor the eventual decoded-bitmap footprint. Derivation:
#: 2**21 (2,097,152 px, ~2.1 megapixels) is an ~8 MiB budget for the decoded
#: RGBA bitmap at 4 bytes/px — deliberately BELOW the 1536x1536 = 2,359,296 px
#: literal worst case the per-side check alone would admit, so this is a
#: genuine additional bound (a maximal 1536x1536 square is pixel-capped even
#: though it satisfies the per-side check). Downstream producers that
#: downscale to fit MAX_IMAGE_DIMENSION_PX (e.g.
#: paper_reprocess.preprint_figures._render_png) must apply BOTH bounds.
MAX_IMAGE_PIXELS = 2**21

#: Documented worst case for ONE image at MAX_IMAGE_DIMENSION_PX in high-detail
#: mode. Derivation (OpenAI-compatible vision tiling, which Dartmouth serves):
#: 1536x1536 = 3x3 = 9 tiles of 512px; cost = 85 base + 9 * 170 per tile = 1615
#: tokens. Rounded UP to 2048 for provider-serialization overhead and future
#: tiling changes — deliberately over-estimating, matching this module's stated
#: conservative philosophy. NEVER lower this without re-deriving it: selection
#: prices worst_case_credits against it (FR-003).
TOKENS_PER_IMAGE = 2048

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


def _role_content_raw(message: Any) -> tuple[str, Any]:
    """Extract ``(role, content)`` from a ``ChatMessage`` object, a mapping, or —
    as a last resort — the object's ``str``. Unlike :func:`_role_content`,
    ``content`` is returned UNCOERCED (``str``, a ``ContentPart`` tuple, or
    whatever the message carries) so a content-aware caller (the hard upper
    bound) can account for multimodal parts instead of a stringified blob."""
    role = getattr(message, "role", None)
    content = getattr(message, "content", None)
    if role is None and content is None and isinstance(message, dict):
        role = message.get("role")
        content = message.get("content")
    if content is None:
        content = message if isinstance(message, str) else str(message)
    return str(role or ""), content


def _role_content(message: Any) -> tuple[str, str]:
    """Extract ``(role, content)`` from a ``ChatMessage`` object, a mapping, or —
    as a last resort — the object's ``str``. Non-str content (e.g. a vision
    parts list) is coerced to ``str`` so the char estimate stays conservative."""
    role, content = _role_content_raw(message)
    return role, content if isinstance(content, str) else str(content)


def _content_upper_bound_tokens(content: Any) -> int:
    """Bounded token contribution for one message's ``content``: the UTF-8 byte
    length for ``str`` (the existing hard-bound basis, UNCHANGED), or — for a
    parts tuple — the sum of each part's contribution: UTF-8 bytes for a
    :class:`~llmxive.backends.base.TextPart`'s text, and the fixed, DEMONSTRABLY
    conservative :data:`TOKENS_PER_IMAGE` charge for each
    :class:`~llmxive.backends.base.ImagePart` (bounded at construction by
    :data:`MAX_IMAGE_DIMENSION_PX` / :data:`MAX_IMAGE_BYTES`, which is what makes
    a fixed per-image charge a true upper bound rather than a guess)."""
    if isinstance(content, str):
        return len(content.encode("utf-8"))
    if isinstance(content, tuple):
        # Local import: backends.base must stay import-cycle-free of
        # model_selection at module scope; this module already sits inside the
        # model_selection package that backends.base's ImagePart itself
        # function-locally imports from, so keep the dependency lazy here too.
        from llmxive.backends.base import ImagePart, TextPart

        total = 0
        for part in content:
            if isinstance(part, TextPart):
                total += len(part.text.encode("utf-8"))
            elif isinstance(part, ImagePart):
                total += TOKENS_PER_IMAGE
            else:  # pragma: no cover - the ContentPart union is closed
                total += len(str(part).encode("utf-8"))
        return total
    return len(str(content).encode("utf-8"))


def estimate_message_tokens(messages: Iterable[Any]) -> int:
    """TELEMETRY-ONLY average estimate (char/÷4 x margin) — NOT authoritative and NOT
    a hard bound. Do NOT size budgets or reservations with this (R3-3): char/4 is the
    average ratio, and token-dense/multi-byte text tokenizes to MORE. Budgeting and
    the fail-fast use :func:`max_input_tokens_upper_bound` instead; this stays for
    logging / rough displays only."""
    total = _REQUEST_OVERHEAD_TOKENS
    for m in messages:
        role, content = _role_content(m)
        total += _PER_MESSAGE_OVERHEAD_TOKENS + estimate_tokens(role) + estimate_tokens(content)
    return math.ceil(total * _SAFETY_MARGIN)


def max_input_tokens_upper_bound(messages: Iterable[Any]) -> int:
    """The SINGLE authoritative input-size estimator (FR-010, R3-3) — a HARD,
    tokenizer-independent upper bound used by BOTH :func:`call_budget_for` (which
    prices the reservation) and :func:`fits_budget` (execute's fail-fast), so
    selection and execution agree on the same ceiling and a paid call can NEVER be
    charged for more input than it reserved.

    Basis: a token is at least one UTF-8 BYTE (byte-level BPE tokenizes the byte
    stream, and multi-byte Unicode can fall back to one token PER byte), so the
    UTF-8 byte length is a true ceiling on the token count — ``len(text)`` in Python
    CHARACTERS is NOT (one char can be several bytes/tokens). Deliberately
    over-conservative (~4x the average); acceptable because paid calls are opt-in
    and rare, and oversized inputs are reduced by the summarize primitive upstream.

    Content-aware (spec 026 slice 7): ``str`` content keeps this exact byte-based
    accounting unchanged; a parts tuple (:class:`~llmxive.backends.base.TextPart` /
    :class:`~llmxive.backends.base.ImagePart`) is priced part-by-part via
    :func:`_content_upper_bound_tokens` so an image contributes the DEMONSTRABLE
    :data:`TOKENS_PER_IMAGE` upper bound instead of vanishing from the estimate."""
    total = _REQUEST_OVERHEAD_TOKENS
    for m in messages:
        role, content = _role_content_raw(m)
        total += (
            _PER_MESSAGE_OVERHEAD_TOKENS
            + len(role.encode("utf-8"))
            + _content_upper_bound_tokens(content)
        )
    return total


def call_budget_for(messages: Iterable[Any], max_output_tokens: int) -> CallBudget:
    """Build the :class:`CallBudget` to price a call, from its ACTUAL messages.

    ``max_input_tokens`` is the HARD upper bound (:func:`max_input_tokens_upper_bound`)
    so a selected candidate is guaranteed to fit and the reservation is never
    under-sized. Called by the selection caller BEFORE ``select`` (which only reads
    the resulting budget)."""
    return CallBudget(
        max_input_tokens=max_input_tokens_upper_bound(messages),
        max_output_tokens=max_output_tokens,
    )


def fits_budget(
    messages: Iterable[Any], requested_output_tokens: int, budget: CallBudget
) -> tuple[bool, str | None]:
    """``execute``'s fail-fast re-check against the priced budget, using the SAME
    hard upper bound as :func:`call_budget_for`: the actual messages' bounded input
    must not exceed ``budget.max_input_tokens`` AND the requested output must not
    exceed ``budget.max_output_tokens``. Returns ``(ok, reason)``."""
    estimated_input = max_input_tokens_upper_bound(messages)
    if estimated_input > budget.max_input_tokens:
        return False, (
            f"bounded input {estimated_input} exceeds "
            f"call_budget.max_input_tokens {budget.max_input_tokens}"
        )
    if requested_output_tokens > budget.max_output_tokens:
        return False, (
            f"requested max_tokens {requested_output_tokens} exceeds "
            f"call_budget.max_output_tokens {budget.max_output_tokens}"
        )
    return True, None
