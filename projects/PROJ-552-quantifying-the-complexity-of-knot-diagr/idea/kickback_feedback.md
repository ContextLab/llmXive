# Downstream review concerns (address in this revision)

## MAINTAINER DECISION (apply verbatim)

The spec panel flagged a methodology drift between this idea and the spec:
the idea promises "predictive power", an 80/20 train/test split,
cross-validated R², ANOVA, and hold-out validation, while the spec treats
the dataset as a complete census analyzed descriptively. This decision
settles the question permanently. Reviewers and revisers MUST NOT re-raise
it.

1. **Descriptive framing is FINAL.** The dataset is the complete census of
   hyperbolic prime knots with ≤ 13 crossings — there is no larger
   population to generalize to, so hold-out validation is not applicable.
   Remove from this idea (everywhere, including the literature-gap
   statements and methodology sketch): the 80/20 train/test split,
   cross-validated R² model selection, ANOVA, "statistical power
   assessment", and "hold-out validation". Replace with:
   - Model assessment via goodness-of-fit on the full census: R², AIC/BIC,
     and MAE.
   - Group comparison (alternating vs. non-alternating) via descriptive
     statistics: mean differences and variance ratios (exact population
     parameters; no inferential testing).
   - Residual analysis identifying hyperbolic knot families deviating by
     ≥ 2 standard deviations from the fitted trend.
2. **Restate the research question** as: "To what extent do crossing number
   and braid index jointly explain variation in hyperbolic volume across
   the complete census of hyperbolic prime knots with ≤ 13 crossings,
   stratified by alternating/non-alternating classification?" Use
   "explain/account for variance" language; do not frame claims as
   predictive performance requiring held-out data.
3. **Phase 1 invariant boundary is unchanged**: crossing number, braid
   index, and hyperbolic volume ONLY. Additional invariants (arc index,
   Seifert circle count, bridge number) remain excluded from Phase 1 and
   reserved for Phase 2+ exploratory extension after primary results are
   established. The spec deferring them to Phase 2+ is CONSISTENT with
   this boundary — reviewers must not flag it as scope creep.
4. **Citations must be verbatim-verified.** Keep every existing verified
   citation exactly as written. Never introduce placeholder citation
   fragments (e.g. "[arXiv identifier]"); if a specific identifier is not
   in the verified list, omit the citation rather than approximating it.
   State each distinct source citation once per section — do not repeat
   the same URL multiple times in a single paragraph.

Everything else in the idea (hyperbolic-prime-knot restriction, dataset
sources, validation of computed invariants against KnotInfo, GitHub
Actions compute envelope of ≤ 6 h / ≤ 7 GB RAM / 2 CPU cores) is correct
and must be preserved verbatim.
