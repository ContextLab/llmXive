# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-29

## Research Question

How does the relationship between crossing number and braid index vary across prime knots with crossing number ≤13, and what patterns emerge when stratifying by alternating/non-alternating classification?

## Dataset Strategy

| Dataset | Purpose | Source/URL | Notes |
|---------|---------|------------|-------|
| Knot Atlas (crossing number ≤13) | Primary dataset for all prime knots with crossing numbers 1-13 | NO verified source found | Per "# Verified datasets" block, no verified URL exists for Knot Atlas download. Implementation must handle this by: (1) attempting download from https://katlas.org/wiki/Main_Page with retry logic (FR-010), (2) documenting "NO verified source found" in `docs/reproducibility/validation_scope.md`, (3) implementing fallback to manual data extraction if API unavailable |
| KnotInfo (reference values) | Algorithm validation against reference invariants | NO verified source found | Per "# Verified datasets" block, no verified URL exists. Implementation must validate algorithms where reference coverage ≥10% of dataset (SC-012), documenting coverage constraints in `docs/reproducibility/algorithm_validation.md` |
| Hoste-Thistlethwaite-Weeks enumeration | Prime knot count validation for crossing numbers ≤10 | NO verified source found | Per "# Verified datasets" block, no verified URL exists. Used for dataset completeness validation (SC-001) |

**Dataset Strategy Note**: The "# Verified datasets" block indicates NO verified source found for the primary datasets required by this project (Knot Atlas, KnotInfo, Hoste-Thistlethwaite-Weeks). This is a critical implementation constraint. The system must:

1. Attempt download from Knot Atlas with exponential backoff retry logic (FR-010)
2. Cache partial results after 3 consecutive failures (User Story 4, Edge Case 1)
3. Document the "NO verified source found" status in reproducibility artifacts
4. Implement manual data extraction fallback if programmatic access fails
5. Record all data source attempts and failures in `docs/reproducibility/reproducibility_logs.jsonl`

## Literature Review

### Key References

1. **Birman, J. & Menasco, W. (1988)**. "A Algorithm for the Arc Index of a Knot". *Mathematische Annalen*, 281, pp. 127-138.
   - Provides algorithm for arc index computation from diagram representations
   - Validation target for FR-003 invariant computation

2. **Seifert, H. (1934)**. "Über das Geschlecht von Knoten". *Mathematische Annalen*, 110, pp. 571-592.
   - Foundational work on Seifert circles and genus computation
   - Validation target for FR-003 invariant computation

3. **Schubert, H. (1956)**. "Über eine numerische Knoteninvariante". *Mathematische Zeitschrift*, 61, pp. 245-288.
   - Bridge number decomposition methodology
   - Validation target for FR-003 invariant computation

4. **Hoste, J., Thistlethwaite, M. B., & Weeks, J. (1998)**. "A Census of Knots". *Experimental Mathematics*, 7(4), 281–299.
   - Prime knot enumeration for crossing numbers up to 13
   - Reference for dataset completeness validation (SC-001)

### Theoretical Framework

The crossing number (minimal number of crossings in any diagram) and braid index (minimal number of strands in any braid representation) are both classical knot invariants. This research hypothesizes a non-linear relationship between these invariants, with stratified patterns emerging when distinguishing alternating from non-alternating knots.

**Composite Complexity Score**: The weighted combination of crossing number and braid index (default 1:1 ratio per assumptions) serves as a novel measure that may exhibit stronger correlation with additional invariants (arc index, Seifert circle count) than either component alone.

## Methodology Overview

### Phase 1 Workflow (Computational Ordering)

1. **Data Download** (FR-001, FR-010): Download knot data from Knot Atlas with exponential backoff retry logic
2. **Data Parsing** (FR-002): Parse and clean dataset, extract crossing number, braid index, alternating classification
3. **Invariant Computation** (FR-003): Compute arc index, Seifert circle count, bridge number from available diagram representations
4. **Exploratory Analysis** (FR-004): Generate stratified scatter plots (crossing number vs. braid index)
5. **Regression Modeling** (FR-005): Fit linear and non-linear regression models
6. **Composite Score Construction** (FR-006): Build weighted complexity score with configurable weights
7. **Validation** (FR-007, FR-008): Test correlation with arc index and Seifert circle count on held-out test set
8. **Reproducibility Documentation** (FR-009): Generate checksums, derivation notes, timestamped logs

### Edge Case Handling (User Story 4)

| Edge Case | Handling Strategy |
|-----------|-------------------|
| Knot Atlas unavailable/rate-limited | Exponential backoff (1s → 2s → 4s → ... → 60s max), cache partial results after 3 failures |
| Missing invariant data | Flag with `missing_invariant_flags` rather than silent exclusion (FR-011) |
| Ambiguous alternating classification | Exclude from stratified analysis OR mark as "unclassifiable" (FR-012) |
| Crossing number ties | Apply tie-breaking rules: prefer braid word over DT code, prefer lexicographically first DT code (FR-013) |

### Statistical Analysis Plan

- **Correlation Analysis**: Both Pearson AND Spearman coefficients (FR-008, Constitution Principle VII)
- **Regression Models**: Linear regression + polynomial/non-linear regression (FR-005)
- **Group Comparisons**: ANOVA for alternating vs. non-alternating differences (FR-008)
- **Effect Sizes**: Cohen's d for group comparisons, r or r² for correlations (FR-008)
- **Significance Threshold**: p < 0.05 (exploratory, no multiple comparison correction per assumptions)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Knot Atlas API unavailable | High - blocks all analysis | Retry logic with exponential backoff, manual extraction fallback, document "NO verified source found" |
| Reference coverage <10% | Medium - limits algorithm validation | Document coverage constraint in `docs/reproducibility/algorithm_validation.md` (SC-012) |
| Dataset completeness <95% for ≤10 | High - invalidates benchmarking | Validate against KnotInfo/Hoste-Thistlethwaite-Weeks, exclude from Phase 1 if <95% (SC-001) |
| Missing diagram representations | Medium - limits invariant computation | Flag records with `missing_invariant_flags`, include in summary report (FR-003) |

## Phase 1 Scope Boundaries

- **Stratification**: Alternating/non-alternating classification only (multi-class exploration deferred to Phase 2+)
- **Validation Scope**: Dataset completeness validated for crossing numbers ≤10 (benchmarking scope), while data collection covers ≤13
- **Test Set**: 20% random stratified split by crossing number (assumptions)
- **Weight Configuration**: Default equal weights (1:1 ratio), configurable via `config/complexity_weights.yaml` (FR-006)
