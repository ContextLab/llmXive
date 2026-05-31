# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Research Question

How does the relationship between crossing number and braid index vary across prime knots with crossing number ≤13, and what patterns emerge when stratifying by alternating/non-alternating classification?

## Background

Knot theory is a branch of topology that studies mathematical knots—closed loops in 3-dimensional space. Two classical invariants characterize knot complexity:

1. **Crossing Number (c)**: The minimum number of crossings in any diagram of the knot
2. **Braid Index (b)**: The minimum number of strands needed to represent the knot as a closed braid

The relationship between these invariants is not fully understood. While both measure complexity, they capture different geometric aspects. This research investigates whether a composite measure combining both provides predictive power for other knot invariants.

## Dataset Strategy

| Dataset | Source | Access Method | Scope |
|---------|--------|---------------|-------|
| Knot Atlas (prime knots ≤13) | Knot Atlas | Direct download with retry logic | All prime knots with crossing number ≤13 |
| KnotInfo reference values | KnotInfo | Programmatic validation subset | Validation subset (≥10% coverage required) |

**Important Note on Dataset Sources**: Per the "# Verified datasets" block in the project specification, NO verified source URLs exist for Knot Atlas (FR-001), KnotInfo (SC-001, SC-012), or related knot enumeration data. The spec states "NO verified source found" for these datasets. Therefore:

- The system will attempt to download from Knot Atlas (https://katlas.org/wiki/Main_Page) as specified in FR-001
- Validation against KnotInfo will be attempted where reference values are available
- **No fabricated URLs will be cited**; if Knot Atlas is unavailable, the retry logic with exponential backoff (per FR-010) will be applied, and partial results cached to disk after 3 consecutive failures
- Dataset completeness for crossing numbers ≤10 will be validated against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration counts, but specific URLs are not cited per the verified datasets constraint

## Computational Tasks Order

1. **Data Download**: Download knot data from Knot Atlas (FR-001) with retry logic (FR-010)
2. **Data Parsing & Cleaning**: Parse JSON/CSV and extract consistent representations (FR-002)
3. **Invariant Computation**: Compute arc index, Seifert circle count, bridge number (FR-003)
4. **Exploratory Analysis**: Generate scatter plots (FR-004)
5. **Regression Modeling**: Fit linear and non-linear models (FR-005)
6. **Composite Score Construction**: Create weighted complexity score (FR-006)
7. **Validation**: Test correlation with held-out test set (FR-007)
8. **Statistical Testing**: Compute Pearson/Spearman correlation, ANOVA (FR-008)
9. **Reproducibility Documentation**: Generate checksums, logs, derivation notes (FR-009)

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| Knot Atlas unavailable/rate-limited | Retry logic with exponential backoff (1s → 2s → 4s →... → 60s max); partial results cached after 3 failures (FR-010) |
| Missing invariant data | Flag with missing_invariant_flags rather than silent exclusion (FR-011) |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" (FR-012) |
| Crossing number ties | Apply documented tie-breaking rules (braid word preferred over DT code; lexicographically first DT code) (FR-013) |
| KnotInfo reference coverage <10% | Document limitation in docs/reproducibility/algorithm_validation.md (FR-003) |

## Success Criteria Alignment

| Criterion | Status | Notes |
|-----------|--------|-------|
| SC-001 | Phase 1: ≤10 validated | Dataset completeness benchmarked for crossing numbers ≤10 (≥95% completeness); ≤13 data downloaded but not validated in Phase 1 |
| SC-002 | ≥2 regression models | Linear and polynomial/non-linear models compared with R², AIC/BIC |
| SC-003 | Correlation with arc index & Seifert circle | Both Pearson and Spearman reported with effect sizes on 20% held-out test set |
| SC-004 | Reproducibility documentation | Random seeds pinned; checksums recorded; derivation notes complete |
| SC-005 | Retry logic verified | Exponential backoff tested on simulated failures |
| SC-006 | ≥99% invariant coverage | Remaining records flagged with explicit missing_invariant_flags |
| SC-007 | No silent exclusions | All ambiguous classifications logged |
| SC-008 | Tie-breaking validation | Validation script in docs/reproducibility/; 100% consistency required |
| SC-009 | Scatter plots generated | PNG files 1200x900+ pixels in data/plots/ |
| SC-010 | ≥3 additional invariants | Arc index, Seifert circle count, bridge number computed |
| SC-012 | Algorithm validation | ≥95% match threshold where KnotInfo coverage ≥10% |
