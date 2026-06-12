# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Dataset Strategy

| Dataset | Source/Loader | Verified URL | Notes |
|---------|---------------|--------------|-------|
| Knot Atlas Prime Knots | Knot Atlas (https://katlas.org) | NO verified source found | Data downloaded via web scraping/API; dataset described by name only per verified datasets policy |
| OEIS Prime Knot Enumeration | OEIS A002863 | https://oeis.org/A002863 | Reference for expected prime knot counts at each crossing number |
| KnotInfo Reference Values | KnotInfo | NO verified source found | Used for validation of hyperbolic volume and additional invariants (Phase 2+) |
| Hoste-Thistlethwaite-Weeks Enumeration | HTW Census | NO verified source found | Reference for dataset completeness validation |

**Data Quality Note**: Knot Atlas is the primary data source for Phase 1. The verified datasets block indicates NO verified source found for Knot Atlas URLs. Data will be downloaded via documented web scraping with exponential backoff retry logic (FR-008). Dataset completeness validated against KnotInfo and HTW enumeration for crossing number ≤10 (Phase 1 scope).

## Methodology Overview

### Phase 1: Core Invariants (Crossing Number, Braid Index)

1. **Data Download**: Download prime knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13
2. **Data Cleaning**: Parse and clean dataset to extract consistent representations; flag records with missing invariant data (FR-002, FR-009)
3. **Precision Validation**: Establish measurement precision for crossing number and braid index; generate scatter plots stratified by alternating/non-alternating classification (User Story 2)
4. **Regression Analysis**: Fit linear, polynomial, and logarithmic regression models to test relationships between crossing number, braid index, and hyperbolic volume (User Story 3)
5. **Residual Analysis**: Identify hyperbolic knot families that deviate significantly from model predictions (≥2 standard deviations) (User Story 3)
6. **Reproducibility**: Document all code and data transformations with checksums, derivation notes, random seeds, and timestamped logs (User Story 4)

### Phase 2+: Exploratory Extension

- Compute additional invariants (arc index, Seifert circle count, bridge number) from available diagram representations (FR-003)
- Validate algorithm implementations against KnotInfo reference values with ≥90% match threshold (SC-010)
- Composite score correlation analysis (deferred per original idea methodology boundary)

## Mathematical Background

### Crossing Number
The crossing number of a knot is the minimum number of crossings in any diagram of the knot. This is a well-defined topological invariant that is tabulated in Knot Atlas for all prime knots up to crossing number 13.

### Braid Index
The braid index of a knot is the minimum number of strands required to represent the knot as a closed braid. Unlike crossing number, braid index requires algorithmic determination and is less well-tabulated. This work must establish measurement precision for braid index across different classes of prime knots (per reviewer marie-curie feedback).

### Hyperbolic Volume
For hyperbolic knots (knots whose complement admits a complete hyperbolic metric of finite volume), the hyperbolic volume is a geometric invariant. Torus knots and satellite knots have volume zero or undefined. Analysis filters to knots with valid hyperbolic volume (volume > 0), acknowledging this as selection bias (FR-012).

### Mathematical Constraints
Braid index ≤ crossing number for most knots (known inequality). This creates a definitional relationship that must be acknowledged in all analysis and coefficient interpretation. Variance partitioning question rather than independent explanatory power (FR-005).

## Statistical Methodology

### Correlation Analysis
- **Primary**: Spearman correlation for discrete integer-valued invariants (crossing number, braid index are small integers)
- **Supplementary**: Pearson correlation for reporting completeness; interpretation must acknowledge discrete data limitation (FR-006)
- **Effect Sizes**: Report Cohen's d for group comparisons, r or r² for correlations alongside all p-values

### Regression Models
- **Model Types**: Linear, polynomial, and logarithmic regression
- **Selection Criteria**: Goodness-of-fit metrics (R², AIC/BIC, MAE), not statistical power
- **Census Data Context**: Since dataset represents complete census of prime knots ≤13 crossings, statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics; p-values documented for convention only (Assumptions)

### Model Validation Methodology Shifts
- **Train/Test Split Removal**: Not applicable for complete census data; analysis is descriptive rather than predictive validation
- **ANOVA Removal**: Not applicable for census data; descriptive statistics (mean differences, variance ratios) suffice for exact population parameters
- **Cross-Validation Removal**: Not applicable for complete census data; goodness-of-fit metrics used for model selection

## Data Quality Requirements

### Null Percentage
Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage <1% across all records in validated dataset subset for hyperbolic prime knots (volume > 0) (SC-013).

### Format Validation
- Valid DT code format for all records
- Valid braid word format where present
- No duplicate knot IDs in output dataset

### Exclusion Criteria
- Filter to hyperbolic prime knots (volume > 0) for volume prediction analysis
- Exclude torus/satellite knots where volume is zero or undefined (FR-012)
- Exclude or mark as unclassifiable knots with ambiguous alternating/non-alternating classification (FR-010)

## Edge Case Handling

### API Unavailability
- Implement exponential backoff retry logic (initial=1s, max=32s, multiplier=2)
- Cache partial results to disk after 3 consecutive failures (FR-008)
- Document retry attempts and failures in timestamped logs

### Missing Invariants
- Flag records with missing_invariant_flags rather than silent exclusion (FR-009)
- Document computability conditions: (1) diagram representation available, (2) algorithm implemented (FR-003)

### Ambiguous Classification
- Either exclude from stratified analysis (with count logged) or mark as "unclassifiable" (FR-010)
- No silent exclusions (SC-006)

### Diagram Representation Ties
- Apply documented tie-breaking rules consistently: (1) prefer braid word over DT code, (2) prefer lexicographically first DT code (FR-011)
- Validate consistency via automated check script (SC-007)

## Reproducibility Artifacts

### Required Documentation
- **SHA-256 checksums** for all data files under `data/` (Constitution Principle III)
- **Derivation notes** with formula citations, step-by-step transformation logic, intermediate values, parameter values, and justification for non-standard choices (FR-007)
- **Timestamped logs** capturing: timestamp, operation, input_file, output_file, parameters, status, duration_ms, error information (FR-007)
- **Random seed values** documented in `docs/reproducibility/random_seeds.md` (FR-007)
- **Validation reports**: validation_scope.md, data_quality_report.md, hyperbolic_volume_validation.md, algorithm_validation.md (Phase 2+), tie_breaking_rules.md, excluded_knots.md, uncomputable_invariants.md, multicollinearity_assessment.md, residual_analysis.md

### Reproducibility Validation
Independent researcher must be able to execute documented code with documented data to reproduce all intermediate values within minimal relative error of documented values (SC-003).

## Limitations and Acknowledgments

### Selection Bias
Filtering to knots with valid hyperbolic volume means conclusions apply only to hyperbolic prime knots, not all prime knots. This limitation must be explicitly stated in all final reports (FR-012).

### Source Independence
When Knot Atlas and KnotInfo share underlying data sources, validation is cross-checking for consistency, NOT independent verification. All final reports must explicitly state this limitation affecting validation claims (FR-013).

### Multicollinearity
Crossing number and braid index are not fully independent predictors (braid index ≤ crossing number for most knots). VIF assessment will quantify multicollinearity concerns as expected consequence of predictor structure (FR-005).

### Additional Invariants Redundancy
Additional invariants (arc index, Seifert circle count, bridge number) have known mathematical constraints with crossing number and braid index. Computing these may provide redundant information rather than independent signals. Validation is exploratory correlation analysis, not independence testing (Assumptions).

### Phase 1 Scope Limitation
All Phase 1 conclusions must be explicitly qualified as limited to validated crossing number ≤10 data; any analysis using crossing number 11-13 data must be marked as exploratory/unvalidated in final reports (FR-001, SC-001).
