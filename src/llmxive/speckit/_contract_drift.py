"""Deterministic cross-document scientific-contract drift scanner.

The convergence panel lenses review ONE document at a time and do that well,
but they reliably MISS a defect that only exists BETWEEN the documents of a
single feature: ``spec.md``, ``plan.md`` and ``tasks.md`` each define the same
named quantity, and the definitions disagree about the actual arithmetic.

Observed (PROJ-9999 totient canary, 2026-10-09 — the frozen trial captured in
``notes/session-2026-10-10-recovery-resume.md``): the spec's FR-005 and the
tasks both define the exported CSV column

    stratum_TV = 0.5 * abs(f_i - 1/(p-1))

while the plan defines the same column, in three places, as

    stratum_TV = abs(f_i - 1/(p-1))

a factor of two apart. Each document is internally coherent, so a per-document
lens sees nothing wrong; the exported numbers simply depend on which document
the implementer happened to follow. No reviewer caught it, and the project
replanned twice with the conflict intact.

This module is a PURE scanner (no IO, no model call):
:func:`scan_contract_drift` takes ``{artifact path: markdown text}`` and returns
:class:`ContractDriftFinding` per named quantity whose definitions disagree.

A finding requires ALL THREE of:

1. the SAME name is defined in at least two different documents;
2. BOTH definitions parse under the restricted sympy evaluator
   (:func:`llmxive.verify.compute.evaluate` — never Python ``eval``/``exec``);
3. their difference does NOT simplify to zero.

So an equivalent restatement (``0.5*x`` vs ``x/2``, ``count * stratum_TV`` vs
``count times stratum_TV`` with a multiplication-sign times) is NOT a finding, and prose that merely looks like a
formula is dropped at step 2. Only names that read as contract names — a
snake_case/underscored identifier, or one at least eight characters long — are
considered, so a context-dependent single symbol (``k`` is "p for
unconditional, p-1 for conditional") cannot produce a finding.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

# --- normalization -------------------------------------------------------

#: Unicode a model reliably emits in generated markdown, mapped to the ASCII
#: math the sympy parser accepts. ``\u2011`` (non-breaking hyphen) and the
#: minus sign are what made ``p-1`` (written with a non-breaking hyphen) unparseable in the observed documents.
_UNICODE_MATH = {
    "\u00bd": "0.5", "\u00bc": "0.25", "\u00be": "0.75",
    "\u00b7": "*", "\u00d7": "*", "\u2219": "*", "\u22c5": "*",
    "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2264": "<=", "\u2265": ">=", "\u2260": "!=",
    "\u00a0": " ", "\u2007": " ", "\u202f": " ", "\u2009": " ",
    "\u2032": "'", "\u2019": "'",
}

#: LaTeX wrappers that carry no arithmetic.
_LATEX_NOISE_RE = re.compile(
    r"\\(?:bigl|bigr|left|right|quad|qquad|displaystyle|text|mathrm)\b|\\[,;!]"
)
_LATEX_FRAC_RE = re.compile(r"\\[dt]?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
#: Markdown bold around a bare identifier (``**stratum_TV**``). Deliberately
#: identifier-only: a general ``**…**`` strip would eat the exponents in
#: ``a**2 * b**3``.
_BOLD_IDENT_RE = re.compile(r"\*\*([A-Za-z][A-Za-z0-9_]*)\*\*")
#: Single-asterisk italics. Requires non-space content with no inner ``*``, so
#: a product (``a*b``) and an exponent (``a**2``) are untouched. Without this,
#: ``*conditionally* used`` reads as the "formula" ``conditionally*used``.
_ITALIC_RE = re.compile(r"(?<![*\w])\*([^*\n]{1,60}?)\*(?![*\w])")
#: Requirement/task identifiers. ``(see FR-002)`` is a cross-reference, never
#: arithmetic, but its digits would otherwise make the prose look numeric.
_REQ_ID_RE = re.compile(r"\b(?:FR|SC|US|NFR|T)[-\u2011]?\d+[a-z]?\b")
#: ``|f_i - 1/(p-1)|`` → ``Abs(f_i - 1/(p-1))``. Requires real arithmetic
#: between the bars and forbids a nested bar, so a markdown table's cell
#: separators (``| stratum_TV | float (float64) |``) are left alone.
_ABS_BARS_RE = re.compile(r"\|([^|\n]{1,80}?)\|")
_ARITHMETIC_RE = re.compile(r"[*/^+]|(?<=[\d)])\s*-|-\s*(?=[\d(])")
#: Prose joined by slashes or asterisks (``samples/draws``,
#: ``original/refactored/baseline``, ``pylint/radon``, ``conditionally*used``)
#: parses as arithmetic and would otherwise be compared as such. A real formula
#: carries a number, a math function, or at least one SYMBOL-LIKE operand: a
#: single letter (``p``, ``s``), an underscored name (``f_i``, ``stratum_TV``),
#: a non-ASCII symbol (``\u0394KE``), or inner capitals (``KE``, ``TV``). A run of
#: plain lowercase English words is none of those. Requirement ids are stripped
#: before this, so ``(see FR-002)`` cannot qualify on its digits.
_NUMERIC_CONTENT_RE = re.compile(r"\d|\b(?:Abs|sqrt|log|exp|sum)\s*\(")
_WORD_RE = re.compile(r"\w+")


def _has_formula_content(formula: str) -> bool:
    if _NUMERIC_CONTENT_RE.search(formula):
        return True
    return any(
        len(word) == 1
        or "_" in word
        or any(ord(ch) > 127 for ch in word)
        or any(ch.isupper() for ch in word[1:])
        for word in _WORD_RE.findall(formula)
    )
#: A capture that begins mid-expression (``(*6371)``) is a parse artifact.
_MALFORMED_HEAD_RE = re.compile(r"^\(\s*[*/^+]")


def _normalize(text: str) -> str:
    """Rewrite generated markdown into ASCII the sympy parser can read."""
    for bad, good in _UNICODE_MATH.items():
        text = text.replace(bad, good)
    text = _LATEX_FRAC_RE.sub(r"((\1)/(\2))", text)
    text = _LATEX_NOISE_RE.sub(" ", text)
    text = _BOLD_IDENT_RE.sub(r"\1", text)
    text = _ITALIC_RE.sub(r"\1", text)
    text = _REQ_ID_RE.sub(" ", text)

    def _bars(match: re.Match[str]) -> str:
        inner = match.group(1)
        if not _ARITHMETIC_RE.search(inner):
            return match.group(0)  # a table separator, not an absolute value
        return f"Abs({inner.strip()})"

    text = _ABS_BARS_RE.sub(_bars, text)
    text = text.replace("`", " ").replace("$", " ")
    text = re.sub(r"\babs\s*\(", "Abs(", text)
    return text


# --- definition extraction ----------------------------------------------

#: ``stratum_TV = <formula>`` / ``stratum_TV defined as <formula>``. Up to ~60
#: characters of prose may sit between the keyword and the formula: the plan
#: wrote "compute stratum_TV defined as the absolute deviation Abs(...)". A
#: sentence boundary or newline ends the window, so a name never binds to a
#: formula in the next sentence.
_DEF_SITE_RE = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9_]*)"
    r"\s*(?:=|:=|\bdefined as\b|\bdenotes\b|\bis\b)"
    r"(?P<window>[^.;:\n]{0,60}?)"
    # ``[ \t]`` never ``\s``: a formula lives on ONE line. With ``\s`` the
    # trailing-operator branch crossed a line break and swallowed the next
    # line's first word (``total_listens`` + ``*Note`` from the line below).
    r"(?P<formula>(?:[0-9]+(?:\.[0-9]+)?[ \t]*\*[ \t]*)?"
    r"(?:Abs|sqrt|log|exp|sum)?\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*\)"
    r"|(?:[0-9]+(?:\.[0-9]+)?[ \t]*\*[ \t]*)?[A-Za-z_][A-Za-z0-9_]*"
    r"(?:[ \t]*[*/+^][ \t]*[A-Za-z0-9_.]+)+)"
)

#: A name that reads as a contract name rather than a context-dependent symbol.
_CONTRACT_NAME_RE = re.compile(r"^(?=.*_)[A-Za-z][A-Za-z0-9_]{2,}$|^[A-Za-z][A-Za-z0-9_]{7,}$")
#: Words the definition grammar can capture as a "name" that never denote a
#: measured quantity.
_NAME_STOPWORDS = frozenset({
    "it", "this", "that", "there", "which", "what", "value", "result",
    "output", "column", "formula", "definition", "note", "where",
})


def _definitions(text: str) -> dict[str, set[str]]:
    """``{contract name: {normalized definition expression}}`` for one document."""
    out: dict[str, set[str]] = {}
    for match in _DEF_SITE_RE.finditer(_normalize(text)):
        name = match.group("name")
        if name.lower() in _NAME_STOPWORDS or not _CONTRACT_NAME_RE.match(name):
            continue
        formula = re.sub(r"\s+", "", match.group("formula"))
        if not _ARITHMETIC_RE.search(formula):
            continue
        if not _has_formula_content(formula):
            continue
        if _MALFORMED_HEAD_RE.match(formula):
            continue
        out.setdefault(name, set()).add(formula)
    return out


# --- comparison ----------------------------------------------------------

#: Every number and every symbol, so two definitions can be compared by
#: arithmetic STRUCTURE. A function name (the token before an opening paren) is
#: preserved: ``Abs(x)`` and ``sqrt(x)`` are structurally different.
_ATOM_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|\w+")


def _skeleton(expr: str) -> str:
    """``expr`` with every atom replaced by ``A``, function names kept.

    ``0.5*Abs(f_i-1/(p-1))`` -> ``A*Abs(A-A/(A-A))``, which differs from
    ``Abs(A-A/(A-A))``: a factor was dropped. But ``60*6371`` and
    ``scale_factor*6371`` both -> ``A*A``, and ``E_base+s*E_D3`` and
    ``E_base+s*E_D3_term`` both -> ``A+A*A``.

    Only a STRUCTURAL difference is reported. Two definitions that differ by one
    atom may well be the same quantity written with a symbol in one document and
    its bound value (or a renamed symbol) in the other — a binding this scanner
    cannot see — whereas a changed coefficient, a dropped absolute value or a
    different operator changes the computed number no matter the bindings.
    """
    def _replace(match: re.Match[str]) -> str:
        end = match.end()
        if end < len(expr) and expr[end] == "(":
            return match.group(0)
        return "A"

    return _ATOM_TOKEN_RE.sub(_replace, expr)


def _equivalent(left: str, right: str) -> bool | None:
    """``True``/``False`` when the restricted evaluator can decide, else ``None``.

    ``None`` means "not comparable" (either side is prose that merely looked
    like a formula, or sympy could not simplify the difference), and never
    produces a finding.
    """
    from llmxive.verify.compute import evaluate

    if left == right:
        return True
    if _skeleton(left) == _skeleton(right):
        return True  # same arithmetic, differing atoms — not decidable here
    difference = evaluate(f"({left}) - ({right})")
    if difference is None:
        return None
    collapsed = difference.replace(" ", "")
    if collapsed in {"0", "0.0", "-0", "+0"}:
        return True
    # A residual that still contains a symbol is a genuine disagreement; a
    # bare non-zero number is too (0.5 vs 1 on the same core).
    return False


@dataclass(frozen=True)
class ContractDriftFinding:
    """One named quantity whose definitions disagree across documents."""

    name: str
    #: ``((artifact, expression), …)`` sorted for a deterministic message.
    definitions: tuple[tuple[str, str], ...]
    reason: str


def scan_contract_drift(docs: Mapping[str, str]) -> list[ContractDriftFinding]:
    """Named quantities defined incompatibly across ``docs``.

    ``docs`` maps an artifact path to its markdown text; at least two documents
    are needed for any finding. Deterministic and order-independent.
    """
    if len(docs) < 2:
        return []
    per_doc = {path: _definitions(text) for path, text in docs.items()}
    names: set[str] = set()
    for defs in per_doc.values():
        names |= set(defs)

    findings: list[ContractDriftFinding] = []
    for name in sorted(names):
        sites: list[tuple[str, str]] = sorted(
            (path, expr)
            for path, defs in per_doc.items()
            for expr in defs.get(name, ())
        )
        if len({path for path, _ in sites}) < 2:
            continue  # a single document may restate its own definition freely
        conflict: tuple[tuple[str, str], tuple[str, str]] | None = None
        for i, first in enumerate(sites):
            for second in sites[i + 1:]:
                if first[0] == second[0]:
                    continue
                if _equivalent(first[1], second[1]) is False:
                    conflict = (first, second)
                    break
            if conflict:
                break
        if conflict is None:
            continue
        (left_path, left_expr), (right_path, right_expr) = conflict
        findings.append(
            ContractDriftFinding(
                name=name,
                definitions=tuple(sites),
                reason=(
                    f"'{name}' is defined as {left_expr!r} in {left_path} but "
                    f"{right_expr!r} in {right_path}; the two are not "
                    f"algebraically equal, so the computed value depends on "
                    f"which document the implementer follows"
                ),
            )
        )
    return findings


__all__ = ["ContractDriftFinding", "scan_contract_drift"]
