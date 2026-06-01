"""Deterministic spec-quality scanner (spec 015 review-panel hardening).

The convergence panel lenses (``panel_spec_*.md``) catch consistency, coverage,
testability and scope issues well, but they reliably MISS a class of mechanical
quality regressions that should never survive into a "converged" spec:

- an unresolved ``[NEEDS CLARIFICATION: …]`` marker (the ``/speckit-clarify``
  step is supposed to remove every one of these before the spec advances);
- a template placeholder that was never filled in — ``[DATE]``, ``[link]``, a
  ``[NNN-feature-name]`` branch-name placeholder, or a literal
  "filled in by the ``/speckit-…`` command" instruction line left in the body;
- a duplicate functional requirement — two ``**FR-0NN**`` bullets whose
  requirement text is (near-)identical after normalization.

This module is a PURE scanner (no IO): :func:`scan_spec_quality` takes the
spec's markdown text and returns a structured list of
:class:`SpecQualityFinding`. A clean spec (no placeholders, distinct FRs, no
NEEDS-CLARIFICATION) yields an EMPTY list — the scanner must not false-positive.

The convergence engine wires these findings so they BLOCK spec convergence the
same way an ``[UNRESOLVED-CLAIM: …]`` marker does — see
``llmxive.convergence.engine._spec_quality_concerns``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --- marker / placeholder patterns ---------------------------------------

# A surviving clarification marker. The opening token is enough to flag — the
# body (and even a missing close bracket) should still block.
_NEEDS_CLARIFICATION_RE = re.compile(r"\[NEEDS CLARIFICATION\b[^\]]*\]?", re.IGNORECASE)

# Template placeholders that the /speckit-specify scaffolding leaves for the
# author to fill. Each entry is (compiled-regex, human reason).
_PLACEHOLDER_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\[DATE\]"), "unfilled [DATE] template placeholder"),
    (re.compile(r"\[link\]", re.IGNORECASE), "unfilled [link] template placeholder"),
    # A literal branch-name placeholder like ``[NNN-feature-name]`` or
    # ``[###-short-name]`` — the scaffolding's branch slug that was never
    # replaced with the real feature directory name.
    (
        re.compile(r"\[(?:NNN|###)[-\w]*\]"),
        "unfilled [NNN-...] branch-name template placeholder",
    ),
)

# A leftover scaffolding instruction line, e.g.
#   "*(filled in by the `/speckit-specify` command)*"
# We match the distinctive instruction phrase anywhere on a line.
_FILL_INSTRUCTION_RE = re.compile(
    r"filled in by the\s*`?/speckit[-\w]*`?\s*command", re.IGNORECASE
)

# --- functional-requirement extraction -----------------------------------

# A functional-requirement bullet: ``- **FR-007**: <text>`` (the leading
# bullet marker is optional; some specs use a table row or bare bold tag).
# Captures the FR id and the requirement text that follows the bold tag.
_FR_BULLET_RE = re.compile(
    r"\*\*(?P<id>FR-\d{2,})\*\*\s*[:\-—]?\s*(?P<text>.+?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SpecQualityFinding:
    """One deterministic spec-quality defect.

    ``kind`` is a stable machine tag (``needs_clarification`` /
    ``template_placeholder`` / ``duplicate_requirement``); ``reason`` is a short
    human-readable explanation; ``text`` is the offending verbatim span (the
    marker, the placeholder, or the two FR ids + shared text) so the synthesized
    concern can quote exactly what the reviser must fix.
    """

    kind: str
    reason: str
    text: str


def _normalize_requirement(text: str) -> str:
    """Normalize an FR's requirement text for near-duplicate comparison.

    Lower-cases, strips markdown emphasis, collapses all runs of
    whitespace/punctuation to a single space, and drops surrounding
    whitespace — so two FRs that differ only in casing, trailing period, or
    spacing compare equal.
    """
    t = text.lower()
    # Drop markdown emphasis markers that don't change meaning.
    t = t.replace("*", "").replace("`", "").replace("_", " ")
    # Collapse any run of non-alphanumeric chars to a single space.
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def _scan_needs_clarification(text: str) -> list[SpecQualityFinding]:
    findings: list[SpecQualityFinding] = []
    for m in _NEEDS_CLARIFICATION_RE.finditer(text):
        findings.append(
            SpecQualityFinding(
                kind="needs_clarification",
                reason=(
                    "a converged spec must have NO surviving "
                    "[NEEDS CLARIFICATION: …] marker"
                ),
                text=m.group(0).strip(),
            )
        )
    return findings


def _scan_placeholders(text: str) -> list[SpecQualityFinding]:
    findings: list[SpecQualityFinding] = []
    for pattern, reason in _PLACEHOLDER_PATTERNS:
        for m in pattern.finditer(text):
            findings.append(
                SpecQualityFinding(
                    kind="template_placeholder",
                    reason=reason,
                    text=m.group(0).strip(),
                )
            )
    for line in text.splitlines():
        if _FILL_INSTRUCTION_RE.search(line):
            findings.append(
                SpecQualityFinding(
                    kind="template_placeholder",
                    reason="leftover '/speckit-… command' scaffolding instruction line",
                    text=line.strip(),
                )
            )
    return findings


def _scan_duplicate_requirements(text: str) -> list[SpecQualityFinding]:
    """Flag two FR bullets whose normalized requirement text is identical."""
    seen: dict[str, str] = {}  # normalized text -> first FR id
    findings: list[SpecQualityFinding] = []
    for m in _FR_BULLET_RE.finditer(text):
        fr_id = m.group("id")
        norm = _normalize_requirement(m.group("text"))
        if not norm:
            continue
        prior = seen.get(norm)
        if prior is not None and prior != fr_id:
            findings.append(
                SpecQualityFinding(
                    kind="duplicate_requirement",
                    reason=(
                        f"{prior} and {fr_id} state the same requirement "
                        f"(near-identical text) — collapse or differentiate them"
                    ),
                    text=f"{prior} ≈ {fr_id}: {m.group('text').strip()}",
                )
            )
        else:
            seen.setdefault(norm, fr_id)
    return findings


def scan_spec_quality(text: str) -> list[SpecQualityFinding]:
    """Scan a spec's markdown and return every deterministic quality defect.

    PURE — no IO. Returns an empty list for a clean spec (no NEEDS-CLARIFICATION
    markers, no unfilled template placeholders, no duplicate FRs).
    """
    if not text:
        return []
    findings: list[SpecQualityFinding] = []
    findings.extend(_scan_needs_clarification(text))
    findings.extend(_scan_placeholders(text))
    findings.extend(_scan_duplicate_requirements(text))
    return findings


__all__ = ["SpecQualityFinding", "scan_spec_quality"]
