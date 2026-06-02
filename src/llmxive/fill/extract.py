"""Value extraction + present-in-source gate (spec 017, fill-layer contract).

present_in_source — deterministic gate: is *value* actually in *source.text*?
extract_value     — LLM locator → proposes a candidate from source.text; only
                    returns it when present_in_source passes (the trust boundary).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llmxive.backends.router import reasoning_chat
from llmxive.claims.models import Claim, ClaimKind
from llmxive.fill.models import FetchedSource
from llmxive.grounding.service import number_substantiated


def present_in_source(value: str, source: FetchedSource, kind: ClaimKind) -> bool:
    """Deterministic gate: is *value* actually present in *source.text*?

    NUMERIC      → delegates to ``grounding.service.number_substantiated`` which
                   handles comma/space thousand-separator variants and other
                   obviously-equivalent numeric representations.
                   Exception (approximate mode): when the source comes from the
                   constants channel, also accept a valid rounding of the constant
                   value (FR-002).  This is conservative: ONLY applied when
                   source.channel=="constants" (a recognized-constant source with
                   a decimal value), never for bare integer counts (FR-003).
    ENTITY_FACT  → normalized located-in-text check (case/whitespace-insensitive
                   substring search).
    All others   → delegates to ``number_substantiated`` (conservative: treats
                   the value as a literal number string).

    This is the non-negotiable trust boundary (FR-003 / SC-002): a value that is
    NOT in the fetched source text is NEVER used for a fill, regardless of what
    the LLM locator returned.
    """
    if kind == ClaimKind.NUMERIC:
        # Fast path: exact match
        if number_substantiated(value, source.text):
            return True

        # Approximate path: only for the constants channel (zero-network, high
        # authority) and ONLY when the value contains a decimal point (FR-003:
        # never loosen bare integer counts).
        if source.channel == "constants" and "." in value:
            return _approximate_in_constants_source(value, source.text)

        return False

    if kind == ClaimKind.ENTITY_FACT:
        return _entity_present(value, source.text)

    if kind in (ClaimKind.MAGNITUDE, ClaimKind.RELATIONAL):
        # These claim types have entity-name values (e.g. "Jupiter", "Canberra"),
        # not bare numbers — use the same entity-presence check as ENTITY_FACT
        # (spec 018, T020/T023).
        return _entity_present(value, source.text)

    # For any other kind, fall back to the numeric gate (conservative).
    return number_substantiated(value, source.text)


def _approximate_in_constants_source(value: str, source_text: str) -> bool:
    """Return True if *value* is a valid rounding of the constant in *source_text*.

    The constants channel stores text like "3.141592653589793 (math.pi ...)".
    We parse the true value from source_text and use is_valid_rounding.
    Conservative: requires a decimal point in *value* (no bare integers).
    """
    import re as _re
    # Extract the leading float from source text (the actual constant value)
    m = _re.search(r"-?\d+\.\d+(?:[eE][+-]?\d+)?", source_text)
    if not m:
        return False
    try:
        true_val = float(m.group(0))
    except ValueError:
        return False

    try:
        from llmxive.verify.approximate import is_valid_rounding, parse_precision
        spec = parse_precision(value)
        # For the gate check, use hedge=False (conservative — no surrounding context here)
        return is_valid_rounding(spec.claimed, true_val, decimals=spec.decimals, hedge=False)
    except Exception:
        return False


def _entity_present(value: str, text: str) -> bool:
    """Normalized case/whitespace-insensitive substring check for entity values."""
    # Normalize whitespace in both strings (collapse runs of spaces/tabs)
    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    return _norm(value) in _norm(text)


def extract_value(
    source: FetchedSource,
    claim: Claim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path | None,
) -> str | None:
    """Extract a candidate value from *source.text* using an LLM locator.

    The LLM is a *locator* — it proposes where in the source text the answer
    lies — never a source of truth itself.  The proposed value is accepted ONLY
    if it passes :func:`present_in_source`; otherwise ``None`` is returned.

    Phase-2 note: the LLM call path requires a real backend (Phase 3+).  When
    *backend* is ``None`` the function attempts a direct lookup in the source
    text (for NUMERIC claims: look for the sequence-index value; for ENTITY
    claims: not attempted — returns ``None`` without a backend).  This keeps
    Phase-2 purely offline-testable while the gate logic is exercised by the
    test suite via :func:`present_in_source` directly.
    """
    if backend is None:
        # Offline fallback: for NUMERIC try to find a number adjacent to the
        # claim's resolved_value context in the source text (crude; real use
        # always supplies a backend).
        candidate = _offline_numeric_lookup(source, claim)
        if candidate is None:
            return None
        if present_in_source(candidate, source, claim.kind):
            return candidate
        return None

    # --- LLM locator path (Phase 3+) ----------------------------------------
    candidate = _call_llm_locator(source, claim, backend=backend, model=model,
                                  repo_root=repo_root)
    if candidate is None:
        return None
    # Apply the trust-boundary gate before returning anything to the caller.
    if present_in_source(candidate, source, claim.kind):
        return candidate
    return None


def _offline_numeric_lookup(source: FetchedSource, claim: Claim) -> str | None:
    """Attempt a direct numeric lookup without an LLM (best-effort, offline).

    For OEIS b-file-style text ("n value\\n…"), searches for a row whose
    *value* column is substantiated in the source AND is NOT the claim's
    asserted (wrong) value.  Returns the first such value, else ``None``.

    When the source is an OEIS b-file AND the claim text contains an explicit
    small integer index (e.g. "at 13 crossings"), that index is used to look up
    the exact row first.
    """
    import re as _re

    if claim.kind != ClaimKind.NUMERIC:
        return None

    lines = source.text.splitlines()

    # Try to find the target index from the claim text (for OEIS b-files)
    if source.channel == "oeis":
        m = _re.search(
            r"\b(\d{1,3})\s*(?:crossings?|crossing number|strands?|-crossing)\b"
            r"|(?:crossing(?:s)? number|at crossing)\s*(\d{1,3})\b",
            claim.raw_text or "", _re.IGNORECASE,
        )
        target_idx: int | None = None
        if m:
            raw_idx = m.group(1) or m.group(2)
            try:
                target_idx = int(raw_idx)
            except (TypeError, ValueError):
                pass

        if target_idx is not None:
            for line in lines:
                parts = line.split()
                if len(parts) == 2:
                    try:
                        idx, val = int(parts[0]), parts[1]
                    except ValueError:
                        continue
                    if idx == target_idx:
                        if number_substantiated(val, source.text):
                            return val

    # Fallback: first b-file row whose value is an integer, is present in text,
    # and is NOT the claim's asserted (wrong) value.
    # We only accept integer values here — non-numeric tokens from non-b-file
    # sources (e.g. Wikipedia) are silently skipped.
    asserted = _re.sub(r"[\s,]", "", claim.resolved_value or "") if claim.resolved_value else None
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            idx_str, val_str = parts
            # Both parts must be integers (b-file format: "<index> <value>")
            try:
                int(idx_str)
                int(val_str)
            except ValueError:
                continue
            bare_val = _re.sub(r"[\s,]", "", val_str)
            if asserted and bare_val == asserted:
                continue  # skip the wrong value
            if number_substantiated(val_str, source.text):
                return val_str
    return None


_DEFAULT_MODEL = "qwen.qwen3.5-122b"


def _call_llm_locator(
    source: FetchedSource,
    claim: Claim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path | None,
) -> str | None:
    """Invoke the LLM to locate the answer value in *source.text*.

    Returns the proposed candidate string, or ``None`` if the LLM cannot
    locate a value.  The caller MUST gate the result through
    :func:`present_in_source` before using it.

    Uses ``backend.chat()`` (the standard llmxive backend API) with a
    single-turn user message.  ``backend.complete()`` is NOT used because
    it does not exist on real backends (DartmouthBackend, etc.).
    """
    from llmxive.backends.base import ChatMessage

    prompt = (
        f"Source text:\n{source.text}\n\n"
        f"Claim: {claim.raw_text}\n\n"
        "Extract the exact value from the source text that answers the claim. "
        "Return ONLY the value (a number or entity name), no other text. "
        "If the value is not present in the source text, respond with 'NOT_FOUND'."
    )
    try:
        messages = [ChatMessage(role="user", content=prompt)]
        # Reasoning models (e.g. qwen.qwen3.5-122b) spend hidden chain-of-thought
        # against the response budget; a small max_tokens yields empty content
        # (finish_reason=length). Mirror grounding/entailment's reasoning-safe
        # budget, degrading gracefully for backends/fakes that omit the kwarg.
        response = reasoning_chat(backend, messages, model=model or _DEFAULT_MODEL)
        text = getattr(response, "text", None) or ""
    except Exception:
        return None

    candidate = text.strip()
    if not candidate or candidate.upper() == "NOT_FOUND":
        return None
    return candidate


__all__ = ["extract_value", "present_in_source"]
