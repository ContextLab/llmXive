"""T012 — Deterministic rule-based claim classifier (spec 016).

classify(raw_text, canonical) -> ClaimKind

Priority order (first match wins):
  1. CAUSAL     — "causes", "leads to", "results in"
  2. MAGNITUDE  — superlatives/comparatives
  3. RELATIONAL — SPO wording ("is the capital of", "wrote", "author of")
  4. RESULT     — produced-metric phrasing ("accuracy was", "we observed", "our model achieved")
  5. CITATION   — bare DOI / arXiv id in canonical or raw text
  6. NUMERIC    — a number/statistic
  7. ENTITY_FACT — fallback definition/is-a
"""

from __future__ import annotations

import re

from llmxive.claims.models import ClaimKind

# --- compiled patterns -------------------------------------------------------

# CAUSAL: explicit causal connectives
_CAUSAL_RE = re.compile(
    r"\b(causes?|leads?\s+to|results?\s+in)\b",
    re.IGNORECASE,
)

# MAGNITUDE: superlatives and comparative phrases
_MAGNITUDE_RE = re.compile(
    r"\b(most\b|largest?|smallest?|highest?|lowest?|fastest?|slowest?|"
    r"greatest?|fewest?|earliest?|latest?|best|worst|"
    r"more\s+than|less\s+than|fewer\s+than|greater\s+than|"
    r"at\s+least|at\s+most)\b",
    re.IGNORECASE,
)

# RELATIONAL: subject–relation–object patterns
_RELATIONAL_RE = re.compile(
    r"\b(is\s+the\s+capital\s+of|capital\s+of|wrote\b|author\s+of|"
    r"invented\s+by|founded\s+by|located\s+in|part\s+of|member\s+of|"
    r"belongs?\s+to|published\s+in|discovered\s+by)\b",
    re.IGNORECASE,
)
# Also match canonical triple separator "subject | relation | object"
_TRIPLE_SEP_RE = re.compile(r"\|")

# RESULT: produced-metric phrasing from an experiment/run
_RESULT_RE = re.compile(
    r"\b(accuracy\s+was|precision\s+was|recall\s+was|f1\s+was|"
    r"we\s+observed|our\s+model\s+achieved|we\s+achieved|"
    r"the\s+model\s+achieved|performance\s+was|speedup\s+of|"
    r"we\s+report|our\s+approach\s+achieves?)\b",
    re.IGNORECASE,
)

# CITATION: DOI or arXiv id
_CITATION_RE = re.compile(
    r"(doi:\s*10\.\d{4,}/\S+|10\.\d{4,}/\S+|arxiv:\s*\d{4}\.\d{4,5})",
    re.IGNORECASE,
)

# NUMERIC: a bare number or percentage (in canonical or raw)
_NUMERIC_RE = re.compile(r"\b\d[\d,]*(\.\d+)?\s*(%|k|m|b|billion|million|thousand)?\b")

# ENTITY_FACT: "X is a/an Y" or definition phrasing
_ENTITY_FACT_RE = re.compile(
    r"\b(is\s+a\b|is\s+an\b|is\s+defined\s+as|refers?\s+to|"
    r"denotes?\b|known\s+as)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------


def classify(raw_text: str, canonical: str) -> ClaimKind:
    """Return the most specific ClaimKind for this claim (rule-based, pure)."""
    combined = raw_text + " " + canonical

    if _CAUSAL_RE.search(combined):
        return ClaimKind.CAUSAL

    if _MAGNITUDE_RE.search(combined):
        return ClaimKind.MAGNITUDE

    if _RELATIONAL_RE.search(combined) or _TRIPLE_SEP_RE.search(canonical):
        return ClaimKind.RELATIONAL

    if _RESULT_RE.search(combined):
        return ClaimKind.RESULT

    if _CITATION_RE.search(combined):
        return ClaimKind.CITATION

    if _ENTITY_FACT_RE.search(combined):
        return ClaimKind.ENTITY_FACT

    if _NUMERIC_RE.search(combined):
        return ClaimKind.NUMERIC

    return ClaimKind.ENTITY_FACT


__all__ = ["classify"]
