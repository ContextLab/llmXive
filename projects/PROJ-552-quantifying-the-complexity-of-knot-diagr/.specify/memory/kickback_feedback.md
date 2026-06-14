# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 10 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Prior concern internal_consistency-70324895 remains UNRESOLVED. The reviser claimed to 'add explicit census-data exception clause to Constitution Principle VII' but the Constitution text provided shows NO such exception was added. Principle VII still states 'All statistical claims...MUST include explicit significance thresholds (p-values, confidence intervals)' while FR-006 states 'p-values are NOT reported for census data'. The Assumptions section documents an exception but the Constitution itself was NOT amended. This is a direct constitutional contradiction that must be resolved by either amending Principle VII or revising FR-006.
- FR-001 states 'for all prime knots with crossing number up to a predefined complexity limit' while SC-001 specifies 'validated completeness benchmark focuses on crossing number ≤10 data' and 'crossing number 11-13 data is downloaded but not validated in Phase 1'. The spec uses both ≤13 (download scope) and ≤10 (validation scope) but FR-001's 'predefined complexity limit' is ambiguous. FR-001 should explicitly state the download limit is ≤13 with validation staged to ≤10 to match SC-001 and Assumptions.
- FR-003's traceability note was corrected (User Story 3 reference removed) but the requirement still contains excessive inline caveats ('Phase 1 Implementation Exclusion', 'Phase 2+ Timeline', 'Threshold Distinction', etc.). While not contradictory, this creates maintenance burden. Consider moving Phase 2+ scope notes to a dedicated section or Assumptions.
- SC-005 states 'A high proportion of knots with computable invariants have all invariants populated' — 'high proportion' is not quantified. Must specify threshold (e.g., ≥90%)
- SC-010 states 'achieves a high match threshold for pass/fail status' — 'high match threshold' is not defined. Must specify numeric threshold (e.g., ≥90%)
- SC-011 states 'families with residuals exceeding a specified threshold' — 'specified threshold' is not defined. Must specify numeric value (e.g., ≥2 standard deviations)
- FR-001 states 'predefined complexity limit' — should explicitly state the limit (e.g., ≤13 crossings) for verifiability
- FR-003 states 'high match threshold' for algorithm validation — should explicitly state the threshold (e.g., ≥90%) for verifiability
- FR-013 states 'Reference coverage threshold set to a high level' — should explicitly state the threshold (e.g., ≥90%) for verifiability
- Prior concern scope-4a074b0a is now adequately addressed. Retry logic justification acknowledges external API dependencies as operational risk. However, this adds implementation work beyond the original idea. Given Constitution Principle I (reproducibility requires fetching from same canonical source), robustness measures are now legitimate scope clarification rather than pure over-reach. No further action needed.

## MAINTAINER DECISION (apply verbatim — quantify every flagged vague phrase)

The testability reviewers have repeatedly flagged the same unquantified
phrases. These are NOT open questions — substitute the concrete,
bound-led values below verbatim (each is consistent with values the spec
already establishes elsewhere) and STOP re-emitting the vague wording:

- FR-001 "predefined complexity limit" → "≤ 13 crossings" (the dataset's
  established bound; align SC-001's completeness benchmark to the same).
- FR-003 "high match threshold" (algorithm validation) → "≥ 90% match
  against KnotInfo reference values".
- FR-013 "Reference coverage threshold set to a high level" → "≥ 90% of
  cited references resolve to a verified source".
- SC-005 "A high proportion of knots ... have all invariants populated" →
  "≥ 95% of knots with computable invariants have all invariants
  populated".
- SC-010 "achieves a high match threshold" → "≥ 90% match against
  reference values".
- SC-011 "families with residuals exceeding a specified threshold" →
  "families with residuals exceeding ≥ 2 standard deviations from the
  fitted trend" (matches SC-011's own residual-analysis text).

Also resolve the FR-001/SC-001 consistency concern by using the SAME
"≤ 13 crossings" bound in both. Remove FR-003's excessive inline caveats
(keep one concise Phase-1 note). After applying these, the spec carries
no unquantified design targets — do not reintroduce any.
