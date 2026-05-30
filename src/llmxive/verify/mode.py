"""T004 — Hybrid mode selector (spec 018, FR-001/D4).

Deterministic heuristics decide the verification mode when confident.
An LLM tie-break is called ONLY when heuristics are ambiguous AND a
backend is supplied.  With ``backend=None`` the heuristic result is
always returned.

Modes: ``"exact"`` | ``"approximate"`` | ``"computational"`` | ``"source"``
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from llmxive.claims.models import Claim

# ---------------------------------------------------------------------------
# Recognised mathematical/physical constant names (must match constants.py)
# ---------------------------------------------------------------------------

_CONSTANT_NAMES = frozenset({
    "pi", "π",
    "e", "euler's number", "eulers number", "napier's constant",
    "tau", "τ",
    "golden ratio", "golden mean", "phi", "φ",
    "c", "speed of light",
    "h", "planck constant", "planck's constant",
    "g", "gravitational constant",
    "k", "boltzmann constant",
    "n_a", "avogadro number", "avogadro's number",
})

# Standalone single-letter constants need word-boundary protection
_SINGLE_LETTER_CONSTANTS = frozenset({"c", "h", "g", "k", "e"})

# ---------------------------------------------------------------------------
# Operator / relation keywords that signal a self-contained expression
# ---------------------------------------------------------------------------

_OPERATOR_RE = re.compile(
    r"""
    \b(?:
        plus | minus | times | divided\s+by | multiplied\s+by |
        equals? | is\s+equal\s+to | is\s+larger\s+than | is\s+greater\s+than |
        is\s+less\s+than | is\s+smaller\s+than |
        is\s+approximately | is\s+about | is\s+roughly | is\s+around |
        factorial | mod | modulo |
        percent\s+of | %\s+of
    )\b
    | [+\-\*/^]          # arithmetic symbols
    | \bof\b             # "30% of 200"
    | \d+\s*%            # percentage pattern "30%"
    | \b(?:km|m|kg|s|mol|K|J|N|Pa|Hz|W|V|A|cd|rad|sr)
      \s+(?:is|equals?|=)\s+  # unit conversion pattern "5 km is"
    """,
    re.VERBOSE | re.IGNORECASE,
)

# External-entity indicators: named proper-noun subjects that cannot be
# computed from the claim text alone.
_EXTERNAL_ENTITY_RE = re.compile(
    r"""
    \b(?:
        knot | knots | prime\s+knot | prime\s+knots |
        capital\s+of | population\s+of |
        planet | galaxy | country | city | element |
        species | gene | protein | compound |
        crossing | crossings
    )\b
    | \b[A-Z][a-z]{2,}\b   # Proper noun (capitalised, length ≥ 3)
    """,
    re.VERBOSE,
)

# Hedge / approximation markers
_HEDGE_RE = re.compile(
    r"\babout\b|\bapproximately\b|\broughly\b|\baround\b|~|≈",
    re.IGNORECASE,
)

# Decimal / scientific-notation number (real-valued)
_REAL_NUMBER_RE = re.compile(
    r"""
    -?\d+\.\d+           # decimal: 3.14, 2.718
    | -?\d+[eE][+-]?\d+  # pure integer scientific: 3e8
    | -?\d+\.\d*[eE][+-]?\d+  # decimal scientific: 3.0e8
    """,
    re.VERBOSE,
)

# Bare integer (no decimal point, no scientific notation)
_BARE_INTEGER_RE = re.compile(r"(?<!\d)-?\d+(?!\d)(?!\.)(?![eE])")

# Unit-conversion pattern: "<number> <unit> is/= <number> <unit>"
_UNIT_CONV_RE = re.compile(
    r"-?\d[\d,.]*\s*(?:km|m|kg|s|mol|K|J|N|Pa|Hz|W|V|A|cd|rad|sr)\b"
    r".*?\b(?:is|=|equals?)\b"
    r".*?-?\d[\d,.]*\s*(?:km|m|kg|s|mol|K|J|N|Pa|Hz|W|V|A|cd|rad|sr)\b",
    re.IGNORECASE,
)


def _has_constant_subject(text: str) -> bool:
    """Return True if the text mentions a recognised constant name."""
    lower = text.lower()
    for name in _CONSTANT_NAMES:
        if name in _SINGLE_LETTER_CONSTANTS:
            # Word-boundary match to avoid "c" matching "capital"
            if re.search(r"\b" + re.escape(name) + r"\b", lower):
                return True
        else:
            if name in lower:
                return True
    return False


def _has_operator(text: str) -> bool:
    return bool(_OPERATOR_RE.search(text))


def _has_external_entity(text: str) -> bool:
    """Return True if text contains an external named entity.

    Exempts recognised mathematical/physical constants so that claims like
    "pi is approximately 3.14" are NOT flagged as external-entity references.
    """
    m = _EXTERNAL_ENTITY_RE.search(text)
    if not m:
        return False
    matched = m.group(0).strip().lower()
    # If the entire match is a recognised constant name, it is NOT an external entity
    if matched in _CONSTANT_NAMES:
        return False
    # Check if the whole text (after lowering) is dominated by constant subjects
    # by stripping constant names and re-testing
    scrubbed = text
    for name in sorted(_CONSTANT_NAMES, key=len, reverse=True):
        scrubbed = re.sub(r"\b" + re.escape(name) + r"\b", " ", scrubbed, flags=re.IGNORECASE)
    return bool(_EXTERNAL_ENTITY_RE.search(scrubbed))


def _has_hedge(text: str) -> bool:
    return bool(_HEDGE_RE.search(text))


def _has_real_number(text: str) -> bool:
    return bool(_REAL_NUMBER_RE.search(text))


def _has_bare_integer(text: str) -> bool:
    """True when the ONLY numeric token(s) are bare integers (no decimal point)."""
    return bool(_BARE_INTEGER_RE.search(text)) and not _has_real_number(text)


def _is_unit_conversion(text: str) -> bool:
    return bool(_UNIT_CONV_RE.search(text))


# ---------------------------------------------------------------------------
# Public pure heuristics
# ---------------------------------------------------------------------------

def looks_self_contained(text: str) -> bool:
    """Return True if *text* describes an evaluable self-contained relation.

    A claim is self-contained when it contains an operator or relation
    keyword AND does NOT reference an external named entity or domain subject
    (FR-017: a mixed arithmetic+fact claim must NOT be self-contained).

    Named mathematical constants (pi, e, tau, …) are NOT external entities —
    they are defined values, so "pi is approximately 3.14" is self-contained.
    """
    # Must have some operator/relation to be evaluable
    has_op = _has_operator(text) or _is_unit_conversion(text)
    if not has_op:
        return False

    # If the text references an external entity, it is NOT self-contained
    # (even if it also contains an operator).
    if _has_external_entity(text):
        return False

    return True


def looks_approximate(text: str) -> bool:
    """Return True if *text* looks like an approximate / real-valued claim.

    Triggers:
    - Contains a hedge word or symbol (about/~/≈/approximately/roughly/around)
    - Contains a decimal or scientific-notation real number
    - Mentions a recognised constant (pi, e, speed of light, …)

    Returns False for a bare integer discrete count.
    """
    if _has_hedge(text):
        return True
    if _has_real_number(text):
        return True
    if _has_constant_subject(text):
        return True
    return False


# ---------------------------------------------------------------------------
# Mode selector
# ---------------------------------------------------------------------------

from llmxive.claims.models import ClaimKind  # noqa: E402 — after TYPE_CHECKING block


def select_mode(
    claim: "Claim",
    *,
    backend=None,
    model: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> str:
    """Return the verification mode for *claim*.

    Priority (D4 heuristics — deterministic):

    1. ``computational``: claim is self-contained (has operator, no external entity).
       Exception: RESULT-kind claims are never computational.
    2. ``approximate``: has a hedge word, decimal/real number, or constant subject.
       Exception: bare integer count NEVER returns approximate (default-safe, FR-003).
    3. ``exact``: bare integer discrete count.
    4. ``source``: everything else (entity facts, relational, external subjects, …).

    An LLM tie-break is invoked ONLY when the heuristics yield a genuinely
    ambiguous result AND ``backend`` is not None.  With ``backend=None`` the
    heuristic result is always returned.
    """
    text = claim.raw_text or claim.canonical or ""

    # --- Hard overrides by claim kind ---
    # RESULT claims must not go to computational (they assert empirical results)
    if claim.kind == ClaimKind.RESULT:
        # Still allow approximate/exact/source
        if looks_approximate(text) and not _has_bare_integer(text):
            return "approximate"
        return "source"

    # ENTITY_FACT and RELATIONAL are always sourced (they reference external subjects)
    if claim.kind in (ClaimKind.ENTITY_FACT, ClaimKind.RELATIONAL):
        return "source"

    # --- Heuristic cascade ---

    # 1. Approximate overrides computational when the subject is a recognized
    #    constant (e.g. "pi is about 3"): these are precision comparisons, not
    #    arithmetic evaluations, and the constants table is the authority.
    if _has_constant_subject(text) and (
        _has_hedge(text) or _has_real_number(text)
    ):
        return "approximate"

    # 2. Self-contained → computational
    if looks_self_contained(text):
        return "computational"

    # 3. Approximate indicators, but ONLY when NOT a bare integer count
    if looks_approximate(text):
        # Default-safe: integer-valued discrete count NEVER goes to approximate
        if _has_bare_integer(text) and not _has_real_number(text) and not _has_hedge(text):
            return "exact"
        return "approximate"

    # 3. Bare integer count → exact
    if _has_bare_integer(text):
        return "exact"

    # 4. Fall through to source
    return "source"
