# Feature Specification: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis`
**Created**: 2026-05-31
**Status**: Draft
**Input**: User description: "Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index"

## Scope Boundaries

<!--
 Consolidated scope-related disclaimers for clarity and consistency.
 All scope decisions made here apply throughout the specification.
-->

### Phase 1 Scope (Alternating/Non-Alternating Dichotomy)

This Phase 1 analysis explicitly narrows the original multi-class prime knot exploration (torus, satellite, hyperbolic) to alternating/non-alternating dichotomy only. Multi-class exploration is deferred to Phase 2+ as documented in Assumptions. This scope boundary is the implementation default for this iteration and acknowledges the original research question encompasses broader knot classes.

**Original Intent Preservation**: The full research question regarding multi-class prime knot exploration remains the long-term goal; Phase 1 establishes foundational analysis on the alternating/non-alternating dichotomy as a tractable first step.

### Validation Scope (Crossing Number ≤10 vs ≤13)

Dataset completeness validation focuses on crossing numbers ≤10 as the Phase 1 benchmarking scope. Data collection covers all knots with crossing number ≤13, but full validation across all crossing numbers ≤13 is deferred to future iterations.

**Rationale**: With 9988 prime knots at crossing number 13 (per Hoste-Thistlethwaite-Weeks enumeration), full validation is computationally impractical for Phase 1 exploratory analysis. This is a deliberate scope decision for practical verification purposes.

**Phase 1 Conclusions Limitation**: Phase 1 conclusions are explicitly limited to the alternating/non-alternating dichotomy AND validated crossing number ≤10 data. Generalization to other knot classes (torus, hyperbolic, satellite) or to unvalidated crossing number 11-13 data requires additional validation in future phases and should not be claimed in Phase 1 final reports.

### Measurement Precision Standard

Consistent with rigorous scientific measurement standards, the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (which requires algorithmic determination) versus crossing number (which is tabulated). See FR-003 for algorithm validation requirements and SC-012 for validation against reference values.

### Multi-Phase Framing

The project is structured as a multi-phase research program. Phase 1 establishes foundational analysis on alternating/non-alternating dichotomy. Phase 2+ will incorporate additional knot classes (torus, satellite, hyperbolic) as data extraction pipelines and classification logic are developed. This phased approach ensures incremental validation.

## Research Question (Phase 1)

To what extent do crossing number and braid index jointly predict the hyperbolic volume of prime knots, and does this relationship differ systematically between alternating and non-alternating classes?

## User Scenarios & Testing *(mandatory)*

<!--
 IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
 Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
 you should still have a viable MVP (Minimum Viable Product) that delivers value.

 Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
 Think of each story as a standalone slice of functionality that can be:
 - Developed independently
 - Tested independently
 - Deployed independently
 - Demonstrated to users independently
-->

### User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1)

As a researcher, I need to download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13 so that I have a testable dataset for correlation analysis.

**Why this priority**: This is the foundational step without which no analysis can proceed. The dataset quality and completeness directly determines the validity of all downstream findings.

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with crossing number ≤13 with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields. A validation against standard knot tables (KnotInfo, Hoste-Thistlethwaite-Weeks enumeration) confirms dataset completeness for the highest crossing number in scope.

**Acceptance Scenarios**:

1. **Given** the Knot Atlas is accessible, **When** the download script executes, **Then** the dataset contains all prime knots with crossing number ≤13 with crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields populated
2. **Given** the dataset is downloaded, **When** a data quality check runs, **Then** at least 95% of records have crossing number, braid index, and hyperbolic volume values present (no nulls in required invariant fields)

---

### User Story 2 - Compute Additional Invariants and Perform Exploratory Analysis (Priority: P2)

As a researcher, I need to compute additional invariants (arc index, Seifert circle count, bridge number) from available diagram representations and perform exploratory data analysis including scatter plots of crossing number vs. braid index stratified by alternating/non-alternating classification so that I can identify correlation patterns before fitting models.

**Why this priority**: Exploratory analysis informs model selection and reveals whether the hypothesized non-linear relationship exists. This step validates the research direction before committing to regression modeling. **Exploratory Extension Acknowledgment**: Computation of arc index, Seifert circle count, and bridge number extends beyond the original idea's methodology (which focused on crossing number and braid index). These additional invariants are exploratory additions to enable richer analysis, with acknowledgment that the core research question concerns crossing number and braid index jointly predicting hyperbolic volume.

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with at least 3 additional invariants computed per knot.

**Acceptance Scenarios**:

1. **Given** the parsed dataset, **When** the invariant computation module runs, **Then** each knot record includes arc index, Seifert circle count, and bridge number values where computable from available diagram representations (minimal crossing diagrams, braid words, or Dowker-Thistlethwaite codes)
2. **Given** the computed invariants, **When** exploratory plots are generated, **Then** scatter plots show crossing number vs. braid index with distinct stratification for alternating and non-alternating prime knots

---

### User Story 3 - Fit Regression Models and Validate Composite Complexity Score (Priority: P3)

As a researcher, I need to fit multiple regression models to test linear vs. non-linear relationships for predicting hyperbolic volume from crossing number and braid index, construct a composite complexity score as a weighted combination of crossing number and braid index, and validate against exploratory validation sample so that I can determine whether the composite measure shows predictive power for geometric complexity.

**Why this priority**: This is the core analytical output that answers the research question. It builds on the data foundation and exploratory analysis to produce the predictive model and validation results. **Composite Score Acknowledgment**: The composite complexity score is an exploratory construct not present in the original idea, which asked about joint predictive relationships rather than composite measures. This addition enables richer analysis while maintaining the core research question focus.

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory validation sample (e.g., 20% of knots) and producing correlation coefficients and goodness-of-fit metrics. Results are considered valid if correlation coefficients, effect sizes, and model metrics are reported with appropriate statistical context, regardless of whether thresholds are met.

**Acceptance Scenarios**:

1. **Given** the exploratory analysis results, **When** regression models are fitted, **Then** at least three model types (linear, polynomial, and logarithmic) are compared with goodness-of-fit metrics (R², AIC/BIC, MAE) documented for each
2. **Given** a composite complexity score is constructed, **When** validation is performed on exploratory validation sample, **Then** correlation with hyperbolic volume is computed and reported with statistical significance testing (ANOVA for group differences where applicable), effect sizes (Cohen's d or r), and comparison against individual invariants to demonstrate composite performance
3. **Given** alternating and non-alternating knot classifications, **When** ANOVA testing runs, **Then** group difference analysis is performed with p-values and effect sizes (Cohen's d) reported for the crossing number vs. braid index relationship between groups
4. **Given** regression model residuals are computed, **When** residual analysis runs, **Then** specific knot families (e.g., pretzel knots, torus knots) that deviate significantly from the global trend are identified and documented. **Residual Family Analysis**: This acceptance scenario implements the methodology from the original idea which explicitly included "Analyze residuals to identify specific knot families that deviate significantly from the global trend."

---

### User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

As a researcher, I need the system to handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation for all code and data transformations, so that analysis can proceed robustly and results can be independently verified.

**Why this priority**: Edge case handling ensures reproducibility and robustness. Without explicit handling, silent failures or inconsistent behavior could invalidate downstream results. Reproducibility documentation is essential for scientific validation and community verification.

**Independent Test**: Can be fully tested by (1) simulating edge cases (API failures, missing data fields, ambiguous classifications) and verifying that the system produces appropriate flags, logs, and partial results rather than crashing or silently excluding data, AND (2) verifying that all reproducibility artifacts (checksums, logs, derivation notes, random seeds) are present and complete according to FR-009.

**Acceptance Scenarios**:

1. **Given** the Knot Atlas is unavailable, **When** retry logic executes, **Then** exponential backoff is applied and partial results are cached to disk after 3 consecutive failures
2. **Given** a knot record has missing invariant data, **When** the computation module processes it, **Then** the record is flagged with missing_invariant_flags rather than being silently excluded
3. **Given** a knot has ambiguous alternating/non-alternating classification, **When** stratified analysis runs, **Then** the record is either excluded (with count logged) or marked as "unclassifiable"
4. **Given** crossing number ties exist, **When** invariant computations run, **Then** documented tie-breaking rules are applied consistently across all records
5. **Given** all data transformations complete, **When** reproducibility check runs, **Then** all required artifacts (SHA-256 checksums, derivation notes, random seeds, timestamped logs) are present in docs/reproducibility/ directory

### Edge Cases

<!--
 ACTION REQUIRED: The content in this section represents placeholders.
 Fill them out with the right edge cases.
-->

- What happens when Knot Atlas is unavailable or rate-limited during download? (System should implement retry logic with exponential backoff and cache partial results)
- How does system handle knots where braid index, hyperbolic volume, or other invariants are not computable from available diagram representations? (Records should be flagged with missing_invariant_flags rather than silently excluded)
- What happens when alternating vs. non-alternating classification is ambiguous or missing for a knot? (System should either exclude from stratified analysis or mark as unclassifiable)
- How does system handle ties or near-ties in crossing number when determining "minimal" representations? (Document tie-breaking rules and ensure consistency across all invariant computations)
- What happens when hyperbolic volume is zero or undefined (e.g., for torus or satellite knots)? (Records should be flagged and excluded from volume prediction analysis with count logged)

## Related Work

<!--
 ACTION REQUIRED: Copy citations from the idea markdown verbatim. Do NOT add new ones.
-->

- — Establishes foundational inequalities relating crossing number and braid index for classical links.
- — Extends Ohyama's inequality to virtual links and generalizes the relationship framework.
- [The algebraic crossing number and the braid index of knots and links (2006)] — Investigates the conjecture that algebraic crossing number is uniquely determined in minimal braid representation.
- [Minimal grid diagrams of the prime knots with crossing number 13 and arc index 13 (2024)](https://arxiv.org/abs/2402.02717) — Provides empirical data on 9,988 prime knots with crossing number 13, establishing a testable dataset for correlation analysis.
- — Relates crossing number to bridge number, offering a third invariant for potential composite measures.
- [Bisected vertex leveling of plane graphs: braid index, arc index and delta diagrams (2018)](https://arxiv.org/abs/1806.09719) — Presents upper bounds for braid index in terms of crossing number using planar graph embeddings.

## Requirements *(mandatory)*

<!--
 ACTION REQUIRED: The content in this section represents placeholders.
 Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST download knot data from Knot Atlas (https://katlas.org) including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13. Data format follows Knot Atlas JSON schema or CSV export with documented column mapping. **Scope Distinction**: Data availability extends to crossing number ≤13, but validated completeness for Phase 1 focuses on crossing number ≤10 (per SC-001). This distinction must be maintained throughout implementation and reporting. **Phase 1 Conclusion Limitation**: All Phase 1 conclusions must be explicitly qualified as limited to validated crossing number ≤10 data; any analysis using crossing number 11-13 data must be marked as exploratory/unvalidated in final reports.
- **FR-002**: System MUST parse and clean the dataset to extract consistent representations of crossing number, braid index, and hyperbolic volume for each prime knot, creating new derived dataset files (no in-place modification per Constitution Principle III)
- **FR-003**: System MUST compute additional invariants (arc index, Seifert circle count, bridge number) from available diagram representations (minimal crossing diagrams, braid words, or Dowker-Thistlethwaite codes as provided by Knot Atlas). A diagram representation is considered "available" if the corresponding field in the Knot Atlas record is non-null and non-empty. When no representations are available for a knot, the record MUST be flagged with missing_invariant_flags and included in a summary report at `docs/reproducibility/uncomputable_invariants.md`. Invariant computation algorithms: arc index via Birman-Menasco method (Birman & Menasco, 1988, "A Algorithm for the Arc Index of a Knot", *Mathematische Annalen*, 281, pp. 127-138); Seifert circle count via Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, "Über das Geschlecht von Knoten", *Mathematische Annalen*, 110, pp. 571-592); bridge number via Schubert's bridge decomposition (Schubert, 1956, "Über eine numerische Knoteninvariante", *Mathematische Zeitschrift*, 61, pp. 245-288). Reference implementations and mathematical definitions documented in docs/reproducibility/invariant_algorithms.md. **Algorithm Validation Requirement**: System MUST validate algorithm implementation correctness against available reference values from KnotInfo for the dataset subset. If KnotInfo reference coverage is <10% of the dataset, validation against KnotInfo MUST be skipped and the limitation MUST be documented in `docs/reproducibility/algorithm_validation.md` with pass/fail status per invariant and per algorithm, noting the coverage constraint and the skip rationale. Pass/fail threshold: ≥95% match with reference values where reference data exists. **Invariant Dependency Acknowledgment**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). Validation is exploratory correlation analysis, not independence testing. This limitation must be acknowledged in all final reports. **Exploratory Extension Note**: Computation of arc index, Seifert circle count, and bridge number extends beyond the original idea's methodology and is an exploratory addition for richer analysis. **Representation Availability Definition**: "Available" diagram representations are explicitly defined as: (1) minimal crossing diagram with non-empty DT code field, (2) braid word representation with non-empty braid word field, (3) any combination of the above where at least one field is non-null and non-empty. When no representations are available, the record is flagged and excluded from invariant computation but retained in dataset for documentation purposes.
- **FR-004**: System MUST perform exploratory data analysis including scatter plots of crossing number vs. braid index, stratified by alternating/non-alternating classification, with output as PNG files saved to data/plots/ directory with minimum resolution 1200x900 pixels
- **FR-005**: System MUST fit at least 3 regression model types (linear regression, polynomial/non-linear regression models, AND logarithmic regression models) to test relationships between crossing number, braid index, and hyperbolic volume. **Multicollinearity Assessment**: System MUST compute variance inflation factors (VIF) for all predictors in regression models to assess multicollinearity, given that braid index ≤ crossing number for most knots (known inequality). VIF values MUST be documented alongside model metrics. If VIF > 5 (https://doi.org/10.1142/S0218216519500020, https://arxiv.org/pdf/1805.04428) for any predictor, this MUST be flagged in final reports as a potential multicollinearity issue affecting coefficient interpretation. **Residual Analysis**: System MUST identify and document specific knot families (e.g., pretzel knots, torus knots) that deviate significantly from model predictions based on residual analysis, implementing the methodology from the original idea.
- **FR-006**: System MUST construct a composite complexity score as a weighted combination of crossing number and braid index with default equal weights (1:1 ratio between crossing number and braid index), weights configurable via `config/complexity_weights.yaml`. **Theoretical Limitation Acknowledgment**: No established mathematical basis exists in knot theory literature for linear combination of crossing number and braid index. The equal-weight default is exploratory and configurable. Justification for default: no theoretical basis exists for differential weighting at this stage. This limitation must be acknowledged in all final reports. **Composite Score Note**: This composite complexity score is an exploratory construct not present in the original idea, added to enable richer analysis of joint predictive relationships.
- **FR-007**: System MUST validate the composite complexity score against exploratory validation sample by testing correlation with hyperbolic volume. **Correlation Reporting Requirement**: Correlation coefficients and effect sizes MUST be reported regardless of magnitude; analysis is considered complete and valid whether correlation values are strong or weak. **Definitional Relationship Acknowledgment**: Validation targets (hyperbolic volume) are geometrically distinct from predictors (crossing number, braid index), providing empirical rather than definitional validation. This is exploratory correlation analysis. This limitation must be acknowledged in all final reports. **Terminology Consistency**: "Exploratory validation sample" is used consistently throughout the spec (not "held-out test set") to acknowledge this is correlation analysis, not ML prediction validation.
- **FR-008**: System MUST apply statistical tests (Pearson AND Spearman correlation where distribution assumptions are uncertain, ANOVA for group differences where applicable) to assess significance of findings, and MUST report effect size measures (Cohen's d for group comparisons, r or r² for correlations) alongside all p-values. **Mandatory Dual Correlation**: Per Constitution Principle VII, BOTH Pearson AND Spearman correlations MUST be reported when distribution assumptions cannot be verified a priori—this is a mandatory requirement, not conditional. **ANOVA Assumption Checks**: Before ANOVA testing, system MUST perform Levene's test for equal variances and Shapiro-Wilk test for normality. If assumptions are violated, system MUST use robust alternatives (e.g., Welch's ANOVA, Kruskal-Wallis test) and document the deviation from standard ANOVA. **Discrete Data Acknowledgment**: Pearson and Spearman correlations are reported for discrete integer-valued invariants (crossing number, braid number are small integers). Pearson assumes continuous data with normal distribution—interpretation limited by discrete nature. Spearman is primary; Pearson is supplementary. This limitation must be acknowledged in all final reports.
- **FR-009**: System MUST document all code and data transformations for reproducibility, including random seed pinning for all stochastic operations, checksums (SHA-256) for all data files recorded under data/ directory per Constitution Principle III with documentation in docs/reproducibility/, derivation notes for all transformations, and timestamped logs stored in docs/reproducibility/. Random seeds MUST be pinned in code per Constitution Principle I (implementation action, not documentation storage); documentation of seed values used lives in docs/reproducibility/. Checksums MUST be recorded under data/ directory per Constitution Principle III; documentation about checksums lives in docs/reproducibility/. Derivation notes for all transformations go to docs/reproducibility/ and MUST include formula citations with page/section references, step-by-step transformation logic with intermediate values, all parameter values used, and justification for any non-standard choices. Derivation notes reference checksums but do not duplicate them. Logs MUST capture sufficient detail for reproducibility including: `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`, and any relevant error information. *Traceability: Anchored to User Story 4 (edge cases/data quality/reproducibility) as part of robustness requirements.*
- **FR-010**: System MUST implement retry logic with exponential backoff (initial 1s, max 60s, multiplier 2) when Knot Atlas is unavailable or rate-limited during download
- **FR-011**: System MUST flag records with missing_invariant_flags rather than silently excluding knots where invariants are not computable from available diagram representations
- **FR-012**: System MUST either exclude from stratified analysis or mark as unclassifiable knots where alternating vs. non-alternating classification is ambiguous or missing
- **FR-013**: System MUST apply documented tie-breaking rules for crossing number ties and ensure consistency across all invariant computations via validation check specified in SC-008. **Tie-Breaking Rules**: (1) When multiple diagram representations exist for a knot, prefer braid word representation over Dowker-Thistlethwaite code; (2) When multiple Dowker-Thistlethwaite codes exist, prefer lexicographically first code. *Traceability: Verification mechanism defined in SC-008 (tie-breaking validation).*
- **FR-014**: System MUST filter the dataset to include only prime knots with complete hyperbolic volume data (exclude torus/satellite knots where volume is zero or undefined) for volume prediction analysis, with excluded records documented in `docs/reproducibility/excluded_knots.md`

### Key Entities *(include if feature involves data)*

- **KnotRecord**: Represents a single prime knot with attributes including crossing number, braid index, arc index, Seifert circle count, bridge number, alternating classification, and hyperbolic volume
- **InvariantsDataset**: Aggregated collection of KnotRecord entities with computed relationships and metadata about data source and computation timestamps
- **RegressionModel**: Represents fitted model with attributes including model type, coefficients, goodness-of-fit metrics, and training/validation split information
- **CompositeComplexityScore**: Represents the weighted complexity measure with attributes including weight parameters, per-knot scores, and validation correlation metrics

**Invariant Dependency Note**: Arc index, Seifert circle count, and bridge number have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number for most knots). These dependencies must be acknowledged in all analysis and reporting. Validation is exploratory correlation, not independence testing.

## Success Criteria *(mandatory)*

<!--
 ACTION REQUIRED: Define measurable success criteria.
 These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Dataset contains all prime knots with crossing number ≤13, with validation benchmarking for dataset completeness focused on crossing numbers ≤10 (≥95% completeness on required invariant fields). Dataset completeness validated against KnotInfo and Hoste-Thistlethwaite-Weeks enumeration for prime knot counts at each crossing number ≤10. Crossing numbers 11-13 data is downloaded but not validated in Phase 1; this is documented in `docs/reproducibility/validation_scope.md` noting the practical constraint (9,988 prime knots at crossing number 13) and justification for Phase 1 scope limitation. **Phase 1 Scope Decision**: FR-001 requires downloading ≤13, and SC-001 validates completeness for ≤10 as Phase 1 benchmarking scope. All other ≤13 references in the spec are understood to be Phase 1 scope-limited to ≤10 for validation purposes. This is a deliberate implementation default, not a pending confirmation item. **Data Availability vs Validated Completeness**: Final report MUST clearly distinguish between 'data availability (≤13)' and 'validated completeness (≤10)' to avoid misrepresenting dataset quality for higher crossing numbers. **Phase 1 Conclusion Limitation**: All Phase 1 analytical conclusions must be explicitly limited to validated crossing number ≤10 data; any findings from crossing number 11-13 data must be marked as exploratory/unvalidated.
- **SC-002**: At least 3 regression model types (linear, polynomial, and logarithmic) are compared with documented goodness-of-fit metrics (R², AIC/BIC, MAE) for each
- **SC-003**: Composite complexity score correlation with hyperbolic volume is reported on exploratory validation sample (using 20% random stratified split by crossing number with documented random seed per FR-009), with effect sizes reported. Both Pearson and Spearman correlation coefficients MUST be reported where distribution assumptions cannot be verified a priori. Correlation coefficients and effect sizes are documented as exploratory findings regardless of magnitude; analysis is considered complete and valid whether correlation values are strong or weak. **Mathematical Property Acknowledgment**: Invariants are mathematical properties of knots, not predictive model outputs. Exploratory validation sample is used for exploratory correlation analysis, not statistical prediction validation. This limitation must be acknowledged in all final reports.
- **SC-004**: All code and data transformations are documented in reproducible format (e.g., Jupyter notebooks or R scripts with version-controlled dependencies), with random seeds pinned, checksums recorded, and derivation notes complete. Derivation notes MUST include formula citations with page/section references, step-by-step transformation logic with intermediate values, all parameter values used, and justification for any non-standard choices. Derivation notes MUST enable an independent researcher to execute the documented code with the documented data to reproduce all intermediate values within documented tolerance thresholds. Log format follows FR-009 requirements for traceability. *Traceability: Anchored to User Story 4 (edge cases/data quality/reproducibility).*
- **SC-005**: Retry logic is verified to execute with exponential backoff (1s → 2s → 4s →... → 60s max) on simulated data source failures, with partial results cached to disk after 3 consecutive failures
- **SC-006**: ≥99% of knots with computable invariants have all invariants populated. An invariant is considered "computable" if: (1) a diagram representation is available per FR-003 (non-null DT code OR braid word field), AND (2) the corresponding algorithm is documented in FR-003 as implementable (arc index via Birman-Menasco, Seifert circle count via Seifert's algorithm, bridge number via Schubert's decomposition). Records where either condition fails are excluded from this metric and logged in `docs/reproducibility/uncomputable_invariants.md` with the specific reason (e.g., "no_representation_available", "algorithm_not_implemented"). **Independent Verification**: This criterion is independently verifiable by checking the uncomputable_invariants.md log and confirming that all excluded records match the documented exclusion criteria.
- **SC-007**: All knots with ambiguous or missing alternating classification are either excluded from stratified analysis (with count logged) or explicitly marked as "unclassifiable" in the output dataset; no silent exclusions occur
- **SC-008**: Tie-breaking rules for crossing number ties are documented in docs/reproducibility/tie_breaking_rules.md and applied consistently across all invariant computations. **Tie-Breaking Rules**: (1) When multiple diagram representations exist for a knot, prefer braid word representation over Dowker-Thistlethwaite code; (2) When multiple Dowker-Thistlethwaite codes exist, prefer lexicographically first code. **Validation check procedure**: (1) Extract all knot records from the downloaded dataset where multiple diagram representations are present (if any), (2) Verify that tie-breaking rule is applied identically across all such records, (3) If no knots have multiple representations, document validation as 'not applicable' in docs/reproducibility/validation_status.md with justification, (4) If knots with multiple representations exist, confirm 100% consistency by comparing invariant computation outputs before and after tie-breaking rule application. A validation script MUST be included in docs/reproducibility/ that automates this check. **Validation Failure Handling**: If the validation script fails (non-zero exit code or consistency check fails), invariant computations are considered incomplete and MUST be re-run before proceeding to downstream analysis. Validation failure MUST be logged and reported in docs/reproducibility/validation_status.md with error details and remediation steps.
- **SC-009**: Exploratory analysis produces scatter plots of crossing number vs. braid index with distinct stratification for alternating and non-alternating prime knots (per User Story 2), saved as PNG files with minimum resolution 1200x900 pixels in the data/plots/ directory
- **SC-010**: At least 3 additional invariants (arc index, Seifert circle count, bridge number) are computed per knot where diagram representations are available, with coverage documented for records where computation is not possible
- **SC-011**: Statistical tests (ANOVA for group differences between alternating and non-alternating knots) are performed with effect sizes (Cohen's d) reported alongside p-values. **Reporting Requirement**: ANOVA analysis is exploratory/supplementary to the core research question; results MUST be reported regardless of significance level. This criterion is satisfied when results are documented, not when statistical thresholds are met. Analysis is complete and valid whether or not significant differences are found. **Assumption Check Requirement**: Levene's test and Shapiro-Wilk test MUST be performed before ANOVA; if assumptions violated, robust alternatives MUST be used and documented.
- **SC-012**: Algorithm validation against KnotInfo reference values achieves ≥95% match threshold for pass/fail status per invariant where reference coverage ≥10% of dataset. Validation results documented in `docs/reproducibility/algorithm_validation.md` with pass/fail status per invariant and per algorithm, noting any coverage constraints. **Traceability**: This success criterion is anchored to User Story 2 (Compute Additional Invariants and Perform Exploratory Analysis) per FR-003's algorithm validation requirement. **Skip Condition**: If KnotInfo reference coverage <10%, validation is skipped and limitation documented per FR-003.
- **SC-013**: Dataset completeness and scope validation documentation in `docs/reproducibility/validation_scope.md` confirms Phase 1 scope boundaries and provides justification for crossing number ≤10 validation benchmarking vs. ≤13 data collection. **Traceability**: This success criterion is anchored to FR-001 (download data) and FR-002 (parse/clean) per the scope validation requirements.
- **SC-014**: Hyperbolic volume data completeness ≥95% for prime knots with crossing number ≤13, with excluded knots (torus/satellite with zero or undefined volume) documented in `docs/reproducibility/excluded_knots.md`

## Assumptions

<!--
 ACTION REQUIRED: The content in this section represents placeholders.
 Fill them out with the right assumptions based on reasonable defaults
 chosen when the feature description did not specify certain details.
-->

- Users have access to stable internet connectivity for downloading data from Knot Atlas and related repositories
- Knot Atlas data format remains stable during the analysis period (no breaking changes to schema or access methods)
- Statistical significance threshold of p < 0.05 is appropriate for this exploratory analysis (no multiple comparison correction applied unless findings suggest otherwise)
- Alternative knot databases (if Knot Atlas is unavailable) will provide compatible data formats for invariant extraction
- The methodology sketch from the idea markdown accurately reflects the intended analytical approach and no fundamental changes are required
- The composite complexity score uses equal weights (1:1 ratio) between crossing number and braid index as the default configuration. This follows standard practice in exploratory composite scoring where no theoretical justification exists for differential weighting. The implementation will support user-configurable weights via a configuration file for future iterations.
- The exploratory validation sample will use a 20% random stratified split by crossing number. This ensures representation across all complexity levels while maintaining the independence required for validation. Time-based split is not applicable to knot data (no temporal ordering), and crossing-number-based split without stratification would risk unbalanced representation. **Terminology Consistency**: "Exploratory validation sample" is used consistently (not "held-out test set") to acknowledge this is correlation analysis, not ML prediction validation.
- **Prime Knot Enumeration Reference**: The number of prime knots at each crossing number is taken from KnotInfo and the Hoste–Thistlethwaite–Weeks enumeration. For crossing number 13, the exact count is 9,988 prime knots, as established in OEIS A002863 (https://oeis.org/A002863) and confirmed by the 2024 study "Minimal grid diagrams of the prime knots with crossing number 13 and arc index 13."
- **Hyperbolic Volume Availability**: Not all prime knots have computable hyperbolic volume (torus and satellite knots have volume zero or undefined). The analysis will filter to knots with valid volume measurements, acknowledging this as a selection bias that should be documented in final reports.
- **Multicollinearity Acknowledgment**: Crossing number and braid index are not fully independent predictors (braid index ≤ crossing number for most knots per known inequality). VIF assessment will be performed to quantify multicollinearity impact on coefficient interpretation.
- **ANOVA Assumption Acknowledgment**: ANOVA testing assumes normality and equal variances. With discrete integer-valued invariants and potentially heterogeneous variance between groups, these assumptions may be violated. Levene's test and Shapiro-Wilk test will be performed; robust alternatives (Welch's ANOVA, Kruskal-Wallis) will be used if assumptions are violated.
- **Measurement Precision Standard**: Consistent with rigorous scientific measurement standards, the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (which requires algorithmic determination) versus crossing number (which is tabulated). This standard is implemented through FR-003 algorithm validation and SC-012 validation against reference values.