# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Dataset Strategy

| Dataset | Source | Format | Verified URL | Notes |
|---------|--------|--------|--------------|-------|
| Knot Atlas Data | Knot Atlas (katlas.org) | CSV/JSON | NO verified source found | Per verified datasets block, NO verified source found for Knot Atlas. Will attempt download from https://katlas.org with documented fallback behavior (FR-010). |
| OEIS A002863 | OEIS | Text | https://oeis.org/A002863 | Prime knot counts by crossing number; verified source for 9988 total knots (crossing 1-13) |
| KnotInfo Reference | KnotInfo | Web API | NO verified source found | Used for algorithm validation (SC-012); per verified datasets block, NO verified source found |
| Hyperbolic Volume | SnapPy/Regina | Computed | NO verified source found | Hyperbolic volume for prime knots; per verified datasets block, NO verified source found |
| 2024 Arc Index Study | arXiv | PDF | https://arxiv.org/abs/2402.02717 | Provides empirical data on prime knots with crossing number 13 |
| 2018 Braid Index Bounds | arXiv | PDF | https://arxiv.org/abs/1806.09719 | Upper bounds for braid index in terms of crossing number |

**Dataset Availability Statement**: Per the verified datasets block, NO verified source is found for the primary Knot Atlas dataset. The implementation will attempt download from https://katlas.org (as specified in FR-001) with exponential backoff retry logic (FR-010). If Knot Atlas becomes unavailable, the system will flag this limitation in `docs/reproducibility/validation_scope.md` and document partial results.

**Prime Knot Counts**: Total prime knots from crossing numbers 1-13 is 9988 (source: OEIS A002863, https://oeis.org/A002863). Phase 1 validation focuses on crossing number ≤10 for practical benchmarking purposes, with crossing numbers 11-13 downloaded but marked as exploratory/unvalidated (per SC-001).

## Methodology Overview

### Research Question

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

### Analytical Approach

1. **Data Collection**: Download prime knot data with crossing numbers ≤13 from Knot Atlas, extracting crossing number, braid index, hyperbolic volume, and alternating classification
2. **Invariant Computation**: Compute additional invariants (arc index via Birman-Menasco method, Seifert circle count via Seifert's algorithm, bridge number via Schubert's decomposition) from available diagram representations
3. **Exploratory Analysis**: Generate stratified scatter plots of crossing number vs. braid index for alternating and non-alternating knots separately
4. **Regression Modeling**: Fit linear, polynomial, and logarithmic regression models to test joint predictive relationships
5. **Composite Score Validation**: Construct weighted complexity score (default 1:1 crossing:braid) and validate correlation with hyperbolic volume
6. **Residual Analysis**: Identify knot families (pretzel, torus) that deviate significantly from global trend

### Precision Standards (Per Marie Curie Reviewer Feedback)

Consistent with rigorous scientific measurement standards, the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds:

- **Crossing Number**: Tabulated from Knot Atlas; precision = exact (integer)
- **Braid Index**: Algorithmic determination; precision documented via algorithm validation against KnotInfo reference values (SC-012)
- **Hyperbolic Volume**: Computed via SnapPy/Regina; precision documented with computational uncertainty bounds

Algorithm validation against KnotInfo reference values achieves match threshold for pass/fail status per invariant where reference coverage of dataset. If KnotInfo reference coverage <80% of dataset, validation is skipped and limitation documented in `docs/reproducibility/algorithm_validation.md` (per FR-003).

## Edge Cases & Handling

| Edge Case | Handling Strategy | Documentation Location |
|-----------|-------------------|------------------------|
| Knot Atlas unavailable | Exponential backoff retry (3 attempts), cache partial results to disk | `docs/reproducibility/validation_scope.md` |
| Missing invariant data | Flag with `missing_invariant_flags` rather than silent exclusion | `docs/reproducibility/uncomputable_invariants.md` |
| Ambiguous alternating classification | Exclude from stratified analysis or mark as "unclassifiable" | `docs/reproducibility/validation_status.md` |
| Hyperbolic volume = 0 (torus/satellite) | Exclude from volume prediction analysis; document excluded records | `docs/reproducibility/excluded_knots.md` |
| Crossing number ties | Apply documented tie-breaking rules (braid word > DT code; lexicographic first) | `docs/reproducibility/tie_breaking_rules.md` |

## Success Metrics

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| Dataset completeness (≤10) | All prime knots present | Validation against KnotInfo and OEIS A002863 |
| Invariant computation coverage | ≥80% of computable invariants populated | Check `docs/reproducibility/uncomputable_invariants.md` |
| Model comparison | ≥3 model types with R², AIC/BIC, MAE | Regression output logs |
| Correlation reporting | Both Pearson AND Spearman coefficients | Statistical test output |
| Reproducibility artifacts | SHA-256 checksums, derivation notes, logs | `docs/reproducibility/` directory completeness |

## Limitations & Acknowledgments

1. **Dataset Verification**: Per verified datasets block, NO verified source found for Knot Atlas. Download attempts will be documented with success/failure status.
2. **Phase 1 Scope**: All conclusions explicitly limited to validated crossing number ≤10 data; crossing numbers 11-13 marked as exploratory/unvalidated.
3. **Multicollinearity**: Braid index ≤ crossing number for most knots (known inequality); VIF assessment performed to quantify multicollinearity impact.
4. **Composite Score**: No established mathematical basis for linear combination of crossing number and braid index; equal-weight default is exploratory.
5. **Hyperbolic Volume**: Not available for torus/satellite knots; selection bias documented in final reports.
6. **Algorithm Validation**: Coverage may be <100% for higher crossing numbers; skip condition documented per FR-003.
