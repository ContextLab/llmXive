# Factual-Grounding Extraction Pass — shared prompt snippet (spec 015, F-19)

# SINGLE SOURCE OF TRUTH (Constitution Principle I): editing this file changes
# the factual-grounding extraction contract for EVERY pipeline agent that runs
# the grounding guard at once. Do NOT copy this text into individual modules —
# `src/llmxive/agents/grounding_guard.py` loads this block at render time and
# prepends the document to audit.
#
# WHY THIS EXISTS (the bug it closes — PROJ-552 fabrication cascade, F-19):
#   A reviewer flagged the (CORRECT) knot count "9,988" as implausible. The
#   reviser "resolved" it by FABRICATING a wrong number (1,296) attached to a
#   free-text author-year citation ("Kauffman & Lambropoulou 2004"), and the
#   panel PASSED it. F-18's citation guard only verifies that REFERENCES RESOLVE
#   (DOI/arXiv/URL existence) — it cannot catch a WRONG NUMBER attached to a
#   citation, nor a free-text citation with no resolvable identifier. This pass
#   extracts every factual claim that is ATTRIBUTED TO AN EXTERNAL SOURCE so the
#   grounding step can verify the source actually substantiates it.

## Your task

You are given a document. Extract EVERY factual claim that is EXPLICITLY
ATTRIBUTED TO AN EXTERNAL SOURCE — i.e. a statistic, count, measurement, or
empirical fact presented TOGETHER WITH a citation or source attribution.

A claim is "attributed to an external source" when its number/fact appears with
ANY of:
  - a citation in parentheses or inline (e.g. "9,988 (Lee et al. 2024)",
    "9,988 [12]", "per Smith 2020", "according to Kauffman & Lambropoulou 2004");
  - a DOI, arXiv id, or URL presented as the source of the fact
    (e.g. "the count is 9,988 (arXiv:2402.13)", "shown in https://...", a
    markdown link "[Knot Atlas](https://katlas.org) reports 9,988");
  - phrasing like "per/from/according to/as reported by/as shown in <source>".

## CRITICAL SCOPE GUARD — bias HARD toward precision (miss rather than over-flag)

ONLY extract claims tied to an EXTERNAL SOURCE. A specification document is full
of LEGITIMATE UNCITED numbers — those MUST be left untouched. NEVER extract:
  - design parameters / thresholds (e.g. "p<0.05", "R² ≥ 0.05", "alpha = 0.8",
    "1200x900 pixels", "max 3 rounds", "timeout 60s", "131072 tokens");
  - requirement / task / section identifiers (FR-027, SC-004, T123, US2);
  - dates, version numbers, issue numbers (#239), enumerated list counts;
  - any number that is the system's OWN design choice, success criterion, or
    configuration value — NOT a fact borrowed from an outside source;
  - a bare citation with NO factual claim attached to it (a reference in a
    bibliography list is not a cited claim).

When in doubt, DO NOT extract. A missed claim is recoverable; a false flag on a
legitimate design number wrongly hard-blocks a good document.

## Output contract (ONE YAML document, no prose around it)

```yaml
claims:            # empty list if the document has NO source-attributed factual claims
  - claim_text: "<the full sentence/phrase making the factual claim>"
    number: "9988"            # the salient numeric value if the claim hinges on a number; omit/null otherwise
    source: "Lee et al. 2024, arXiv:2402.13"   # the source string EXACTLY as written in the doc
```

Rules:
- `claims` is an empty list when nothing qualifies — that is the COMMON, CORRECT
  outcome for a spec full of uncited design numbers.
- `number` is the bare numeric value (digits only, drop thousands separators and
  units) ONLY when the claim's substance is that number; omit it for non-numeric
  empirical facts.
- `source` is copied VERBATIM from the document (so the grounding step can try to
  resolve any DOI/arXiv/URL inside it, or detect that it is free-text-only).
- Do NOT invent claims, numbers, or sources. Extract only what is literally in
  the document.
