# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Overview

This research quantifies the relationship between classical knot invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for prime knots. Phase 1 establishes foundational analysis on the alternating/non-alternating dichotomy with validated completeness for crossing number ≤10.

## Literature Review

### Foundational Inequalities

The relationship between crossing number and braid index has been established through foundational work. The standard inequality relating these invariants provides a theoretical framework for understanding their joint behavior. This work establishes foundational inequalities relating crossing number and braid index for classical links.

Extensions to virtual links generalize the relationship framework, demonstrating the robustness of these invariants across broader knot classes.

### Algebraic Crossing Number Conjecture

Research into the algebraic crossing number investigates the conjecture that algebraic crossing number is uniquely determined in minimal braid representation. This has implications for understanding whether braid index provides independent information beyond crossing number.

### Empirical Data for High Crossing Numbers

Recent work provides empirical data on 9,988 prime knots with crossing number 13, establishing a testable dataset for correlation analysis. This dataset forms the basis for Phase 1 data collection, though validation is limited to crossing number ≤10 due to computational constraints.

### Braid Index Upper Bounds

Planar graph embeddings provide upper bounds for braid index in terms of crossing number, offering theoretical constraints on the relationship being studied.

### Bridge Number Relationships

Crossing number relates to bridge number, offering a third invariant for potential composite measures. This supports the exploratory computation of bridge number as part of the invariant extension.

## Dataset Strategy

### Primary Data Source: Knot Atlas

**Source**: Knot Atlas (https://katlas.org)

**Verified Source Status**: NO verified source found for direct programmatic access. The specification requires downloading data from Knot Atlas, but no verified URL exists in the "# Verified datasets" block. This limitation is explicitly documented in `docs/reproducibility/data_sources.md`.

**Fallback Strategy**: 
- Primary: Direct download from Knot Atlas with retry logic (FR-010)
- Secondary: Manual CSV export if API unavailable (documented in reproducibility logs)
- Tertiary: Alternative knot databases (KnotInfo) if Knot Atlas permanently unavailable

**Data Fields Required**:
| Field | Description | Required |
|-------|-------------|----------|
| crossing_number | Minimal crossing count | ✅ Yes |
| braid_index | Minimal braid representation | ✅ Yes |
| hyperbolic_volume | Geometric volume (if hyperbolic) | ✅ Yes |
| alternating | Boolean classification | ✅ Yes |
| dt_code | Dowker-Thistlethwaite code | Optional |
| braid_word | Braid representation | Optional |

**Completeness Validation**:
- Phase 1 benchmark: ≥95% completeness for crossing number ≤10 (SC-001)
- Phase 1 scope limitation: Data collected for ≤13, but validation only for ≤10
- Reference counts: OEIS A002863 confirms 9,988 prime knots at crossing number 13

### Additional Data Sources (for Validation)

**KnotInfo**: Used for algorithm validation (SC-012) if reference coverage ≥10% of dataset.

**Hoste-Thistlethwaite-Weeks enumeration**: Used for prime knot count verification at each crossing number ≤10.

## Methodology

### Phase 1: Data Collection and Validation

**Task Order** (per computational task ordering requirement):
1. Download knot data from Knot Atlas
2. Parse and clean dataset (FR-002)
3. Validate completeness against reference counts (SC-001)
4. Compute checksums and document derivation (FR-009)

**Edge Case Handling**:
- API unavailability: Exponential backoff (1s → 2s → 4s → ... → 60s max), cache partial results after 3 failures (FR-010, SC-005)
- Missing invariants: Flag with missing_invariant_flags, do not silently exclude (FR-011, SC-007)
- Ambiguous classification: Exclude from stratified analysis or mark "unclassifiable" (FR-012)

### Phase 2: Invariant Computation

**Algorithms** (per FR-003):
- **Arc index**: Birman-Menasco method (Birman & Menasco, 1988)
- **Seifert circle count**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934)
- **Bridge number**: Schubert's bridge decomposition (Schubert, 1956)

**Representation Availability**: Diagram representation considered "available" if non-null DT code OR non-empty braid word field exists.

**Validation** (SC-012):
- Validate against KnotInfo reference values if coverage ≥10%
- Pass/fail threshold: ≥95% match with reference values
- Document in `docs/reproducibility/algorithm_validation.md`

### Phase 3: Exploratory Analysis

**Outputs** (FR-004, SC-009):
- Scatter plots: crossing number vs. braid index
- Stratification: alternating vs. non-alternating
- Format: PNG, minimum 1200x900 pixels
- Location: data/plots/

**Additional Invariants** (SC-010):
- At least 3 additional invariants computed per knot where representations available
- Coverage documented for records where computation not possible

### Phase 4: Regression Modeling

**Model Types** (FR-005, SC-002):
1. Linear regression
2. Polynomial/non-linear regression
3. Logarithmic regression

**Metrics** (FR-005, SC-002):
- R² (coefficient of determination)
- AIC/BIC (information criteria)
- MAE (mean absolute error)
- VIF (variance inflation factor for multicollinearity assessment)

**Multicollinearity** (FR-005):
- VIF > 5 flagged as potential multicollinearity issue
- Documented in final reports

**Residual Analysis** (FR-005):
- Identify knot families deviating from global trend (e.g., pretzel knots, torus knots)
- Document specific families with significant residuals

### Phase 5: Composite Complexity Score

**Construction** (FR-006):
- Weighted combination of crossing number and braid index
- Default: equal weights (1:1 ratio)
- Configuration: `config/complexity_weights.yaml`

**Theoretical Limitation**: No established mathematical basis for linear combination; equal-weight default is exploratory (acknowledged in all reports).

**Validation** (FR-007, SC-003):
- Exploratory validation sample: 20% random stratified split by crossing number
- Correlation with hyperbolic volume computed
- Both Pearson AND Spearman coefficients reported (FR-008)
- Effect sizes reported regardless of magnitude

### Phase 6: Statistical Testing

**Tests** (FR-008, SC-011):
- Pearson correlation (supplementary, assumes continuous normal data)
- Spearman correlation (primary, handles discrete integer-valued invariants)
- ANOVA for group differences (alternating vs. non-alternating)
- Effect sizes: Cohen's d for group comparisons, r or r² for correlations

**Assumption Checks** (FR-008):
- Levene's test for equal variances (before ANOVA)
- Shapiro-Wilk test for normality (before ANOVA)
- If violated: use robust alternatives (Welch's ANOVA, Kruskal-Wallis)

**Reporting** (SC-011):
- Results documented regardless of significance level
- Analysis complete and valid whether or not significant differences found

## Reproducibility Requirements

### Random Seed Pinning (FR-009, Constitution Principle I)

All stochastic operations must have pinned random seeds:
- Data split (20% validation sample)
- Any sampling operations
- Documented in `docs/reproducibility/`

### Checksums (FR-009, Constitution Principle III)

- SHA-256 checksums for all data files under `data/`
- Recorded in `data/` directory and `docs/reproducibility/checksums.md`
- Raw data preserved unchanged; derivations produce new files

### Derivation Notes (FR-009)

- Formula citations with page/section references
- Step-by-step transformation logic with intermediate values
- All parameter values used
- Justification for non-standard choices

### Logs (FR-009)

Format: `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`, error information

### Tie-Breaking Rules (FR-013, SC-008)

1. When multiple diagram representations exist: prefer braid word over DT code
2. When multiple DT codes exist: prefer lexicographically first code

Validation script included in `docs/reproducibility/` to automate consistency check.

## Phase 1 Limitations

### Scope Boundaries

- **Alternating/Non-alternating only**: Multi-class prime knot exploration (torus, satellite, hyperbolic) deferred to Phase 2+
- **Crossing number ≤10 validated**: Data collected for ≤13, but validation benchmarking limited to ≤10 due to computational constraints (9,988 knots at c=13)
- **Exploratory extensions**: Arc index, Seifert circle count, bridge number, and composite complexity score are exploratory additions beyond original methodology

### Data Availability vs Validated Completeness

Final report MUST distinguish between:
- "Data availability (≤13)" - data downloaded for all knots up to c=13
- "Validated completeness (≤10)" - completeness verified only for c≤10

### Conclusion Limitation

All Phase 1 analytical conclusions must be explicitly limited to validated crossing number ≤10 data. Findings from crossing number 11-13 data must be marked as exploratory/unvalidated.
