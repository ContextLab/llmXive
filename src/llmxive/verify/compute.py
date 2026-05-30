"""T017 — Safe computational evaluator (spec 018, FR-014/015).

evaluate()           — restricted sympy evaluation, NO Python eval/exec builtins
extract_expression() — deterministic parser (backend=None) or LLM locator
verify_computational() — full ComputeVerdict from claim text
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from llmxive.claims.models import Claim


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class ComputeStatus(str, Enum):  # noqa: UP042 - str+Enum mixin kept; StrEnum changes str() repr
    VERIFIED = "verified"
    REFUTED = "refuted"
    NOT_EVALUABLE = "not_evaluable"


@dataclass(frozen=True)
class ComputeVerdict:
    evaluable: bool
    status: ComputeStatus
    asserted: str
    computed: str
    expression: str


# ---------------------------------------------------------------------------
# Safe sympy evaluation — no Python built-in eval or exec builtins used
# ---------------------------------------------------------------------------

def _make_sympy_locals():
    """Build a safe symbol/function mapping for parse_expr."""
    import sympy
    import sympy.physics.units as _units

    safe = {}
    # Common math functions
    for name in ("sqrt", "log", "exp", "sin", "cos", "tan",
                 "asin", "acos", "atan", "atan2",
                 "Abs", "sign", "floor", "ceiling",
                 "factorial", "binomial",
                 "simplify", "expand", "factor", "cancel",
                 "Rational", "Integer", "pi", "E", "I", "oo",
                 "And", "Or", "Not", "Xor",
                 "Union", "Intersection", "FiniteSet",
                 "Symbol", "symbols"):
        obj = getattr(sympy, name, None)
        if obj is not None:
            safe[name] = obj

    # Unit symbols
    for unit_name in ("meter", "meters", "m",
                      "kilometer", "kilometers", "km",
                      "centimeter", "centimeters", "cm",
                      "millimeter", "millimeters", "mm",
                      "kilogram", "kilograms", "kg",
                      "gram", "grams", "g",
                      "second", "seconds", "s",
                      "minute", "minutes",
                      "hour", "hours",
                      "liter", "liters", "L",
                      "milliliter", "milliliters", "mL",
                      "newton", "newtons", "N",
                      "joule", "joules", "J",
                      "watt", "watts", "W",
                      "pascal", "pascals", "Pa",
                      "kelvin", "kelvins", "K",
                      "celsius", "fahrenheit"):
        obj = getattr(_units, unit_name, None)
        if obj is not None:
            safe[unit_name] = obj

    return safe


_SYMPY_LOCALS = None  # Populated lazily


def _get_locals():
    global _SYMPY_LOCALS
    if _SYMPY_LOCALS is None:
        _SYMPY_LOCALS = _make_sympy_locals()
    return _SYMPY_LOCALS


# Percentage pattern: "30% of 200"
_PCT_RE = re.compile(
    r"""
    (?P<pct>-?\d+(?:\.\d+)?)\s*%\s*of\s*(?P<base>-?\d+(?:\.\d+)?)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Unit conversion patterns like "5 km → m" or "5 km to m" or "5 km in m"
_UNIT_CONV_RE = re.compile(
    r"""
    (?P<val>-?\d+(?:\.\d+)?)\s+
    (?P<from_unit>[a-zA-Z]+)\s+
    (?:→|->|to|in)\s+
    (?P<to_unit>[a-zA-Z]+)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Inequality / comparison: "A > B", "A < B", "A >= B", "A <= B", "A == B", "A != B"
_CMP_EXPR_RE = re.compile(r"[<>]=?|!=|==")


def evaluate(expression: str) -> str | None:
    """Evaluate *expression* using sympy. Returns a string result or None.

    Safety: uses sympy.parsing.sympy_parser.parse_expr with restricted locals.
    NEVER uses Python built-in eval or exec.

    Supports:
    - Arithmetic: +, -, *, /, **, parentheses
    - Comparisons/inequalities (returns "True"/"False")
    - Percentages: "30% of 200" → "60"
    - Unit conversions: "5 km → m" → "5000"
    - Algebraic identities: "(x+1)**2 - (x**2+2*x+1)" → "0"
    - Logic: "And(True, False)" etc.
    - Returns None on any parse/evaluation failure (never raises)
    """
    try:
        import sympy
        from sympy.parsing.sympy_parser import (
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
        from sympy.physics.units.util import convert_to

        expr = expression.strip()

        # --- Percentage: "30% of 200" ---
        m = _PCT_RE.fullmatch(expr)
        if m:
            pct = sympy.Rational(m.group("pct"))
            base = sympy.Rational(m.group("base"))
            result = (pct / 100) * base
            return str(result)

        # --- Unit conversion: "5 km → m" ---
        m = _UNIT_CONV_RE.fullmatch(expr)
        if m:
            val_str = m.group("val")
            from_name = m.group("from_unit")
            to_name = m.group("to_unit")
            locs = _get_locals()
            from_unit = locs.get(from_name) or locs.get(from_name.lower())
            to_unit = locs.get(to_name) or locs.get(to_name.lower())
            if from_unit is None or to_unit is None:
                return None
            quantity = sympy.Rational(val_str) * from_unit
            converted = convert_to(quantity, to_unit)
            # extract the numeric coefficient
            coeff = converted / to_unit
            simplified = sympy.simplify(coeff)
            return str(simplified)

        # --- Sympy parse_expr for everything else ---
        transformations = (*standard_transformations, implicit_multiplication_application)
        locs = _get_locals()

        parsed = parse_expr(expr, local_dict=locs, transformations=transformations,
                            evaluate=True)
        simplified = sympy.simplify(parsed)

        # Booleans
        if simplified is sympy.true:
            return "True"
        if simplified is sympy.false:
            return "False"

        return str(simplified)

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Expression extractor — deterministic parser (backend=None) + LLM fallback
# ---------------------------------------------------------------------------

# Patterns for deterministic extraction (backend=None)

# "A plus B is C" / "A plus B equals C"
_ARITH_WORDS_RE = re.compile(
    r"""
    (?P<lhs>-?\d+(?:\.\d+)?)\s+
    (?P<op>plus|minus|times|divided\s+by|multiplied\s+by)\s+
    (?P<rhs>-?\d+(?:\.\d+)?)\s+
    (?:is|equals?|=)\s+
    (?P<result>-?\d+(?:\.\d+)?)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# "X is larger/greater than Y" / "X is smaller/less than Y"
_CMP_WORDS_RE = re.compile(
    r"""
    (?P<lhs>-?\d+(?:\.\d+)?)\s+
    is\s+
    (?P<rel>larger\s+than|greater\s+than|bigger\s+than|
            smaller\s+than|less\s+than|fewer\s+than|
            equal\s+to|the\s+same\s+as)
    \s+(?P<rhs>-?\d+(?:\.\d+)?)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# "X% of Y is Z"
_PCT_CLAIM_RE = re.compile(
    r"""
    (?P<pct>-?\d+(?:\.\d+)?)\s*%\s*of\s*(?P<base>-?\d+(?:\.\d+)?)\s+
    (?:is|equals?|=)\s+
    (?P<result>-?\d+(?:\.\d+)?)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# "A unit is B unit"  e.g. "5 km is 5200 m" / "5 km is 5000 m"
_UNIT_CLAIM_RE = re.compile(
    r"""
    (?P<val>-?\d+(?:[,\s]\d+)*(?:\.\d+)?)\s+
    (?P<from_unit>[a-zA-Z]+)\s+
    (?:is|equals?|=|are)\s+
    (?P<result_val>-?\d+(?:[,\s]\d+)*(?:\.\d+)?)\s+
    (?P<to_unit>[a-zA-Z]+)
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _op_word_to_symbol(op: str) -> str:
    op = op.lower().strip()
    if op == "plus":
        return "+"
    if op == "minus":
        return "-"
    if op in ("times", "multiplied by"):
        return "*"
    if op in ("divided by",):
        return "/"
    return "+"


def _rel_word_to_op(rel: str) -> str:
    rel = rel.lower().strip()
    if any(w in rel for w in ("larger", "greater", "bigger")):
        return ">"
    if any(w in rel for w in ("smaller", "less", "fewer")):
        return "<"
    if any(w in rel for w in ("equal", "same")):
        return "=="
    return ">"


def _strip_commas(s: str) -> str:
    """Remove commas and spaces used as thousands separators."""
    return re.sub(r"[,\s]+", "", s)


def extract_expression(
    claim: Claim,
    *,
    backend,
    model: str | None,
    repo_root: str | None,
) -> tuple[str, str] | None:
    """Locate (expression, asserted_result) from claim text.

    With backend=None: deterministic regex parser for common forms:
      - "A op B is C"  (arithmetic word form)
      - "A is larger/smaller than B" (comparison)
      - "X% of Y is Z" (percentage)
      - "A unit is B unit" (unit conversion)

    With a backend: LLM is used only to LOCATE the expression; it never
    computes the result.

    Returns (expression_str, asserted_str) or None.
    """
    text = (claim.raw_text or claim.canonical or "").strip()
    if not text:
        return None

    # --- Deterministic patterns ---

    # 1. Percentage claim
    m = _PCT_CLAIM_RE.search(text)
    if m:
        pct = m.group("pct")
        base = m.group("base")
        result = m.group("result")
        expr = f"{pct}% of {base}"
        return (expr, result)

    # 2. Arithmetic word form
    m = _ARITH_WORDS_RE.search(text)
    if m:
        lhs = m.group("lhs")
        op = _op_word_to_symbol(m.group("op"))
        rhs = m.group("rhs")
        result = m.group("result")
        expr = f"{lhs}{op}{rhs}"
        return (expr, result)

    # 3. Comparison word form
    m = _CMP_WORDS_RE.search(text)
    if m:
        lhs = m.group("lhs")
        rel = _rel_word_to_op(m.group("rel"))
        rhs = m.group("rhs")
        # The assertion is that the relation holds (True)
        expr = f"{lhs}{rel}{rhs}"
        return (expr, "True")

    # 4. Unit conversion claim
    m = _UNIT_CLAIM_RE.search(text)
    if m:
        val = _strip_commas(m.group("val"))
        from_unit = m.group("from_unit")
        result_val = _strip_commas(m.group("result_val"))
        to_unit = m.group("to_unit")
        expr = f"{val} {from_unit} → {to_unit}"
        return (expr, result_val)

    # --- LLM locator (backend provided) ---
    if backend is not None:
        return _llm_extract(text, backend=backend, model=model, repo_root=repo_root)

    return None


def _llm_extract(
    text: str,
    *,
    backend,
    model: str | None,
    repo_root: str | None,
) -> tuple[str, str] | None:
    """Ask an LLM to locate (expression, asserted_result) from claim text.

    The LLM ONLY identifies the expression and the claimed result — it NEVER
    computes. Computation is always done by sympy.
    """
    try:
        prompt = (
            "Extract the mathematical expression and the asserted result from "
            "this claim. Return ONLY two lines:\n"
            "EXPRESSION: <expression in standard math notation>\n"
            "ASSERTED: <the claimed result>\n\n"
            f"Claim: {text}"
        )
        response = backend.complete(
            prompt,
            model=model,
            max_tokens=256,
            temperature=0.0,
        )
        raw = response.strip() if isinstance(response, str) else ""
        expr_line = None
        asserted_line = None
        for line in raw.splitlines():
            if line.upper().startswith("EXPRESSION:"):
                expr_line = line.split(":", 1)[1].strip()
            elif line.upper().startswith("ASSERTED:"):
                asserted_line = line.split(":", 1)[1].strip()
        if expr_line and asserted_line:
            return (expr_line, asserted_line)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Main verifier
# ---------------------------------------------------------------------------

def verify_computational(
    claim: Claim,
    *,
    backend=None,
    model: str | None = None,
    repo_root: str | None = None,
) -> ComputeVerdict:
    """Verify a self-contained claim by sympy evaluation.

    Steps:
    1. extract_expression → (expression, asserted)
    2. evaluate(expression) → computed
    3. Compare asserted vs computed (exact str, numeric, or approximate)

    Returns ComputeVerdict. Status not_evaluable when extraction or evaluation
    fails.
    """
    _NOT_EVALUABLE = ComputeVerdict(
        evaluable=False,
        status=ComputeStatus.NOT_EVALUABLE,
        asserted="",
        computed="",
        expression="",
    )

    # Step 1: extract
    extracted = extract_expression(
        claim, backend=backend, model=model, repo_root=repo_root
    )
    if extracted is None:
        return _NOT_EVALUABLE

    expression, asserted = extracted

    # Step 2: evaluate
    computed = evaluate(expression)
    if computed is None:
        return ComputeVerdict(
            evaluable=False,
            status=ComputeStatus.NOT_EVALUABLE,
            asserted=asserted,
            computed="",
            expression=expression,
        )

    # Step 3: compare
    verified = _compare(asserted, computed)

    return ComputeVerdict(
        evaluable=True,
        status=ComputeStatus.VERIFIED if verified else ComputeStatus.REFUTED,
        asserted=asserted,
        computed=computed,
        expression=expression,
    )


def _compare(asserted: str, computed: str) -> bool:
    """Compare asserted vs computed, trying multiple strategies.

    1. String equality (case-insensitive for True/False)
    2. Numeric equality (float parse)
    3. Approximate rounding (is_valid_rounding) for real-valued results
    4. Sympy symbolic equality (simplify(a - b) == 0)
    """
    # Normalise
    a_norm = asserted.strip()
    c_norm = computed.strip()

    # 1. Exact string (case-insensitive)
    if a_norm.lower() == c_norm.lower():
        return True

    # 2. Numeric
    try:
        a_f = float(a_norm.replace(",", "").replace(" ", ""))
        c_f = float(c_norm.replace(",", "").replace(" ", ""))
        if abs(a_f - c_f) < 1e-9 * max(1.0, abs(c_f)):
            return True
        # 3. Approximate rounding
        from llmxive.verify.approximate import is_valid_rounding, parse_precision
        try:
            spec = parse_precision(a_norm)
            if is_valid_rounding(spec.claimed, c_f, decimals=spec.decimals, hedge=False):
                return True
        except Exception:
            pass
        return False
    except (ValueError, TypeError):
        pass

    # 4. Sympy symbolic equality
    try:
        import sympy
        from sympy.parsing.sympy_parser import (
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
        transformations = (*standard_transformations, implicit_multiplication_application)
        locs = _get_locals()
        a_sym = parse_expr(a_norm, local_dict=locs, transformations=transformations)
        c_sym = parse_expr(c_norm, local_dict=locs, transformations=transformations)
        diff = sympy.simplify(a_sym - c_sym)
        return diff == 0
    except Exception:
        pass

    return False


__all__ = [
    "ComputeStatus",
    "ComputeVerdict",
    "evaluate",
    "extract_expression",
    "verify_computational",
]
