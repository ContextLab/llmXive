# Feature Specification: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Feature Branch**: `001-knot-complexity-analysis`  
**Created**: 2026-06-12  
**Status**: Draft  
**Input**: User description: "Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1)

As a researcher, I need to download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤ 13 crossings so that I have a testable dataset for correlation analysis.

**Why this priority**: This is the foundational step without which no analysis can proceed. The dataset quality and completeness directly determines the validity of all downstream findings.

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with crossing number ≤ 13 crossings with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields. A validation against standard knot tables (KnotInfo, Hoste-Thistlethwaite-Weeks enumeration) confirms dataset completeness for the highest crossing number in scope.

**Acceptance Scenarios**:

1. **Given** the Knot Atlas is accessible, **When** the download script executes, **Then** the dataset contains all prime knots with crossing number ≤ 13 crossings with crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields populated
2. **Given** the dataset is downloaded, **When** a data quality check runs, **Then** ≥ 95% of knots with computable invariants have all invariants populated (crossing number, braid index, hyperbolic volume present)

---

### User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

As a researcher, I need to establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots.

**Why this priority**: This addresses marie-curie's feedback on measurement precision standards. "We did not claim a new element until the atomic weight could be determined with precision." Similarly, this work must establish the precision of its measurements across different classes of prime knots. The crossing number is well-defined (tabulated), but the braid index requires careful experimental validation. **Phase 1 Scope**: Only core invariants (crossing number, braid index) are validated in Phase 1. Additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+ per original idea methodology boundary.

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with validation against reference values where available.

**Acceptance Scenarios**:

1. **Given** the parsed dataset, **When** the precision validation module runs, **Then** each knot record includes crossing number and braid index values where available from Knot Atlas
2. **Given** the computed invariants, **When** exploratory plots are generated, **Then** scatter plots show crossing number vs. braid index with distinct stratification for alternating and non-alternating prime knots

**Phase 2+ Deferred Note**: Algorithm validation for additional invariants (arc index, Seifert circle count, bridge number) against KnotInfo reference values aims to achieve ≥ 90% match against reference values. If reference coverage is ≥ 90% but match rate is < 90%, validation fails and limitation documented. This acceptance scenario is not applicable to Phase 1 implementation.

---

### User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

As a researcher, I need to fit multiple regression models to test linear vs. non-linear relationships for associating hyperbolic volume from crossing number and braid index, and assess correlation against exploratory sample so that I can determine whether the joint invariants describe the association with geometric complexity.

**Why this priority**: This is the core analytical output that answers the research question. It builds on the data foundation and exploratory analysis to produce the predictive model and validation results. **Core Methodology**: Analysis focuses on crossing number and braid index as separate predictors (per original idea), not composite measures.

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory sample and producing correlation coefficients and goodness-of-fit metrics. Results are considered valid if correlation coefficients, effect sizes, and model metrics are reported with appropriate statistical context, regardless of whether thresholds are met.

**Acceptance Scenarios**:

1. **Given** the exploratory analysis results, **When** regression models are fitted, **Then** at least three model types (linear, polynomial, and logarithmic) are compared with goodness-of-fit metrics (R², AIC/BIC, MAE) documented for each
2. **Given** regression model residuals are computed, **When** residual analysis runs, **Then** specific hyperbolic knot families (e.g., pretzel, hyperbolic non-alternating) that deviate significantly (≥ 2 standard deviations from the fitted trend) from the global trend are identified and documented. **Residual Family Analysis**: This acceptance scenario implements the methodology from the original idea which explicitly included "Analyze residuals to identify specific knot families that deviate significantly from the global trend." Since torus and satellite knots are filtered out per FR-012, residual analysis targets only hyperbolic knot families.
3. **Given** alternating and non-alternating knot classifications, **When** descriptive comparison analysis runs, **Then** group difference analysis is performed with mean differences and variance ratios reported for the crossing number vs. braid index relationship between groups (see SC‑009)

---

### User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

As a researcher, I need the system to handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation for all code and data transformations, so that analysis can proceed robustly and results can be independently verified.

**Why this priority**: Edge case handling ensures reproducibility and robustness. Without explicit handling, silent failures or inconsistent behavior could invalidate downstream results. Reproducibility documentation is essential for scientific validation and community verification.

**Independent Test**: Can be fully tested by (1) simulating edge cases (API failures, missing data fields, ambiguous classifications) and verifying that the system produces appropriate flags, logs, and partial results rather than crashing or silently excluding data, AND (2) verifying that all reproducibility artifacts (checksums, logs, derivation notes, random seeds) are present and complete according to FR‑007.

**Acceptance Scenarios**:

1. **Given** the Knot Atlas is unavailable, **When** retry logic executes, **Then** exponential backoff is applied and partial results are cached to disk after a threshold of consecutive failures (see FR‑008 and SC‑004)
2. **Given** a knot record has missing invariant data, **When** the computation module processes it, **Then** the record is flagged with `missing_invariant_flags` rather than being silently excluded
3. **Given** a knot has ambiguous alternating/non-alternating classification, **When** stratified analysis runs, **Then** the record is either excluded (with count logged) or marked as "unclassifiable"
4. **Given** diagram representation ties exist, **When** invariant computations run, **Then** documented tie‑breaking rules are applied consistently across all records (see FR‑011 and SC‑007)
5. **Given** all data transformations complete, **When** reproducibility check runs, **Then** all required artifacts (SHA‑256 checksums, derivation notes, random seeds, timestamped logs) are present in `docs/reproducibility/` directory

### User Story 5 - Additional Invariant Computation, Validation, and Extended Visualisation (Priority: P5)

As a researcher, I need to compute additional topological invariants (arc index, Seifert‑circle count, bridge number) where diagram representations exist, generate exploratory scatter‑plot visualisations for these invariants, and validate the computed values against independent reference data (KnotInfo). I also need hyperbolic volume cross‑checks against KnotInfo and reporting of coverage and validation metrics.

**Why this priority**: Extending the analysis to richer invariant sets enables deeper exploratory insights and prepares the groundwork for Phase 2+ extensions while still being anchored to a concrete, testable deliverable.

**Independent Test**: Can be fully tested by (a) running the additional‑invariant computation module and confirming ≥ 95% of knots with computable representations have all three invariants populated (see SC‑005), (b) verifying ≥ 90% match against KnotInfo reference values where coverage ≥ 90% (see SC‑010), (c) confirming that scatter‑plot PNGs are produced at ≥ 1200×900 px resolution (see FR‑004), and (d) confirming that hyperbolic volume consistency with KnotInfo meets ≥ 90% match (see SC‑013).

**Acceptance Scenarios**:

1. **Given** a knot record with at least one diagram representation, **When** the additional‑invariant module runs, **Then** arc index, Seifert‑circle count, and bridge number are computed and stored; records lacking a representation are flagged with `missing_invariant_flags` (see FR‑003, see US‑5)
2. **Given** the computed invariants, **When** visualisation scripts execute, **Then** PNG scatter‑plots for each invariant versus crossing number are saved in `data/plots/` with minimum resolution 1200×900 px (see FR‑004, see US‑5)
3. **Given** the hyperbolic volume values from Knot Atlas, **When** cross‑check against KnotInfo is performed, **Then** ≥ 90% of overlapping records agree within the tolerance defined in SC‑013 (see FR‑013, see US‑5)
4. **Given** the validation results, **When** the reproducibility report is generated, **Then** coverage percentages, match rates, and any limitations (e.g., insufficient reference coverage) are documented (see SC‑010, SC‑013)

### Edge Cases

- What happens when Knot Atlas is unavailable or rate‑limited during download? (System should implement retry logic with exponential backoff and cache partial results)
- How does system handle knots where braid index, hyperbolic volume, or other invariants are not computable from available diagram representations? (Records should be flagged with `missing_invariant_flags` rather than silently excluded)
- What happens when alternating vs. non‑alternating classification is ambiguous or missing for a knot? (System should either exclude from stratified analysis or mark as unclassifiable)
- How does system handle diagram representation ties when determining "minimal" representations? (Document tie‑breaking rules and ensure consistency across all invariant computations)
- What happens when hyperbolic volume is zero or undefined (e.g., for torus or satellite knots)? (Records should be flagged and excluded from volume prediction analysis with count logged)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download knot data from Knot Atlas (https://katlas.org) including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤ 13 crossings. Data format follows Knot Atlas JSON schema or CSV export with documented column mapping. **Scope Distinction**: Data availability extends to crossing numbers up to 13 crossings, but validated completeness for the initial phase focuses on crossing number within a limited range (per SC-001). This distinction must be maintained throughout implementation and reporting. **Phase 1 Validation Benchmark**: Phase validation benchmark focuses on crossing number ≤ 10 data; any analysis using crossing number 11‑13 data must be marked as exploratory/unvalidated in final reports. The research question targets the complete census of hyperbolic prime knots with ≤ 13 crossings; validation is staged for practical feasibility. **Data Quality Reference**: Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage ≤ 5% per field across all records in the validated dataset subset for hyperbolic prime knots (volume > 0), per SC-001.

- **FR-002**: System MUST parse and clean the dataset to extract consistent representations of crossing number, braid index, and hyperbolic volume for each prime knot, creating new derived dataset files (no in‑place modification per Constitution Principle III). **Data Quality Definition**: 'Clean' means: (1) null percentage ≤ 5% per field in required invariant fields (crossing number, braid index, hyperbolic volume), (2) format validation pass rate ≥ 99% for all records (valid DT code format, valid braid word format where present), (3) duplicate knot IDs = 0 (see SC-015). Any record failing these conditions is flagged with `data_quality_flags` and documented in `docs/reproducibility/data_quality_report.md`. **Flag Distinction**: `data_quality_flags` is used for general data quality issues (null values, format failures, duplicates); `missing_invariant_flags` (per FR‑009) is used specifically when invariants cannot be computed from available diagram representations. These are distinct flag categories with different triggering conditions.

- **FR-003**: System SHOULD compute additional invariants (arc index, Seifert circle count, bridge number) from available diagram representations (minimal crossing diagrams, braid words, or Dowker‑Thistlethwaite codes as provided by Knot Atlas) as an exploratory extension for Phase 2+ scope beyond core methodology. **Phase 1 Implementation Exclusion**: Additional invariants MUST NOT be computed in Phase 1 implementation. Algorithm validation against KnotInfo reference values requires ≥ 90% match against reference values. **Phase 2+ Scope Boundary**: Additional invariants are explicitly excluded from Phase 1 implementation and reserved for exploratory extension only after primary results are established. **Algorithm Validation**: System MUST validate algorithm implementation correctness for additional invariants against available reference values from KnotInfo with ≥ 90% match against reference values. If KnotInfo reference coverage is < 90%, validation is skipped and the limitation documented. **Representation Availability**: Invariant computation requires at least one non‑null diagram representation (DT code **or** braid word). When no representations are available, the record is flagged and excluded from invariant computation but retained in the dataset for documentation purposes. **Mathematical Constraint Acknowledgment**: Additional invariants have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number). Validation is exploratory correlation analysis, not independence testing. Additional invariants cannot claim independent predictive value beyond crossing number and braid index. **Algorithm Implementation**: Arc index computed via Birman‑Menasco algorithm (source: arXiv preprint by Birman and Menasco), Seifert circle count via Seifert's algorithm = s(D) (source: arXiv preprint, https://arxiv.org/abs/math/...), bridge number via Schubert's decomposition (source: https://en.wikipedia.org/wiki/Bridge_number). **See US‑5**.

- **FR-004**: System MUST generate exploratory scatter‑plot visualisations of crossing number vs. braid index, and additionally of each newly computed invariant versus crossing number, stratified by alternating/non‑alternating classification, and save PNG files to `data/plots/` with minimum resolution 1200×900 px (see US‑5).

- **FR-006**: System MUST compute correlation coefficients (Spearman primary, Pearson supplementary) as descriptive statistics to characterize relationships between crossing number, braid index, and hyperbolic volume, and MUST report effect size measures (Cohen's d for group comparisons, r or r² for correlations) for all comparisons (p‑values are NOT reported for census data, per research.md). **Primary Correlation Method**: Spearman correlation is the primary method for discrete integer‑valued invariants. **Supplementary Pearson**: System MUST report Pearson correlation for completeness; interpretation must acknowledge discrete data limitation. **Descriptive Comparison Metrics**: System MUST compute mean differences, variance ratios, AND Cohen's d for alternating vs. non‑alternating knot groups (see SC‑009). **Census Data Acknowledgment**: Since the dataset represents a complete census, all statistical analysis is descriptive; effect sizes are the primary metrics, p‑values are not applicable. **See US‑3**.

- **FR-007**: System MUST document all code and data transformations for reproducibility, including random seed pinning for all stochastic operations, checksums (SHA‑256) for all data files recorded under `data/` directory per Constitution Principle III with documentation in `docs/reproducibility/`, derivation notes for all transformations, and timestamped logs stored in `docs/reproducibility/`. Random seeds MUST be pinned in code per Constitution Principle I (implementation action, not documentation storage); documentation of seed values used lives in `docs/reproducibility/`. Checksums MUST be recorded under `data/` directory per Constitution Principle III; documentation about checksums lives in `docs/reproducibility/`. Derivation notes reference checksums but do not duplicate them. Logs MUST capture sufficient detail for reproducibility including: `timestamp`, `operation`, `input_file`, `output_file`, `parameters`, `status`, `duration_ms`, and any relevant error information. *Traceability: Anchored to User Story 4 (edge cases/data quality/reproducibility) as part of robustness requirements.* **Cross‑reference (FR‑006 vs. FR‑007)**: FR‑007 covers reproducibility documentation (checksums, derivation notes, logs, random seeds), while FR‑006 covers statistical methodology (correlation tests, effect sizes, p‑value handling). These are separate concerns and should not be conflated.

- **FR-008**: System MUST implement retry logic with exponential backoff (configurable initial and maximum durations, constant multiplier) when Knot Atlas is unavailable or rate‑limited during download. Retry sequence: initial delay followed by exponential backoff up to a maximum threshold. Partial results MUST be cached to disk after multiple consecutive failures (see SC‑004).

- **FR-009**: System MUST flag records with `missing_invariant_flags` rather than silently excluding knots where invariants are not computable from available diagram representations. **Flag Distinction**: `missing_invariant_flags` is used specifically when invariants cannot be computed from available diagram representations (per FR‑003 representation availability definition). This is distinct from `data_quality_flags` (per FR‑002) which is used for general data quality issues (null values, format failures, duplicates). Records may have both flag types if multiple conditions apply.

- **FR-010**: System MUST either exclude from stratified analysis or mark as unclassifiable knots where alternating vs. non‑alternating classification is ambiguous or missing.

- **FR-011**: System MUST apply documented tie‑breaking rules for diagram representation ties and ensure consistency across all invariant computations via validation check specified in SC‑007 (tie‑breaking validation). **Tie‑Breaking Rules**: (1) When multiple diagram representations exist for a knot, prefer braid word representation over Dowker‑Thistlethwaite code; (2) When multiple Dowker‑Thistlethwaite codes exist, prefer lexicographically first code. *Traceability: Validation mechanism defined in SC‑007 (tie‑breaking validation).*

- **FR-012**: System MUST filter the dataset to include only prime knots with hyperbolic volume > 0 (exclude torus/satellite knots where volume is zero or undefined) for volume prediction analysis, with excluded records documented in `docs/reproducibility/excluded_knots.md`. **Selection Bias Acknowledgment**: Filtering to knots with valid hyperbolic volume means the research question about 'prime knots' cannot be fully answered—only 'hyperbolic prime knots' are analyzed. All final reports MUST acknowledge this limitation. **Scope Clarification**: The analysis applies only to hyperbolic prime knots (volume > 0); conclusions do not extend to torus or satellite knots. **Invariant Type Distinction**: Combinatorial invariants (crossing number, braid index) and geometric invariants (hyperbolic volume) measure fundamentally different properties; the explanatory relationship may be weak or non‑existent by mathematical definition, not empirical finding. All final reports MUST explicitly acknowledge this distinction.

- **FR-013**: System MUST perform data consistency cross‑check of hyperbolic volume data against KnotInfo reference values (source: KnotInfo, https://knotinfo.org/) for the subset of knots where reference data is available. Consistency check results documented in `docs/reproducibility/hyperbolic_volume_validation.md` with match rate documentation and coverage percentage. **Consistency Check Threshold**: System MUST achieve ≥ 90% match against KnotInfo reference values where both are available. If KnotInfo reference coverage is < 90% of the analyzed knots, data consistency cross‑check is skipped and the limitation documented with skip rationale. **Source Independence Assessment**: System MUST document whether Knot Atlas and KnotInfo share underlying data sources or methodologies. If both databases derive from common sources (e.g., Hoste‑Thistlethwaite‑Weeks enumeration), this must be explicitly stated and the data consistency cross‑check interpreted as cross‑check rather than independent verification. The ≥ 90% threshold measures internal consistency rather than validation against independent ground truth. All final reports MUST explicitly state this limitation. **See US‑5**.

### Key Entities *(include if feature involves data)*

- **KnotRecord**: Represents a single prime knot with attributes including:
  - `knot_id` (string, e.g., "3_1")
  - `crossing_number` (integer)
  - `braid_index` (integer)
  - `hyperbolic_volume` (float, zero for non‑hyperbolic knots)
  - `alternating` (boolean)
  - `source` (object, required by contract):
    - `database` (string, e.g., "KnotAtlas")
    - `version` (string, e.g., "v1.2")
    - `url` (string, URL of the source record)
    - `accessed_at` (ISO‑8601 timestamp)
  - `source_timestamp` (ISO‑8601 string) – timestamp when this record was retrieved from the source database.
  - `checksum_sha256` (string, 64‑hex characters) – SHA‑256 checksum of the raw source record file for integrity verification.

- **InvariantsDataset**: Aggregated collection of `KnotRecord` entities with computed relationships and metadata about data source and computation timestamps.
- **RegressionModel**: Represents fitted model with attributes including model type, coefficients, goodness‑of‑fit metrics, and training/validation split information.

**Invariant Dependency Note**: Additional invariants (arc index, Seifert circle count, bridge number) have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number). These dependencies must be acknowledged in all analysis and reporting. Validation is exploratory correlation analysis, not independence testing. Additional invariants cannot claim independent predictive value beyond crossing number and braid index.

## Implementation Plan *(optional but addresses concerns)*

- **Robust Data Acquisition (FR‑008)**: The download module will implement exponential backoff with configurable parameters: initial delay = 1 s, multiplier = 2, maximum delay = 32 s. After three consecutive failures the partially retrieved dataset will be written to `data/cache/partial_knot_atlas.json` and the process will abort with a logged warning. This behavior satisfies FR‑008.

- **Verification of Retry Logic (SC‑004)**: A test script `tests/test_retry_logic.py` will simulate HTTP failures using a mock server. The script asserts that the backoff schedule follows the specified parameters and that the partial cache file is created after three failures. Successful execution returns exit code 0, fulfilling SC‑004.

- **Descriptive Group Comparison (SC‑009)**: After data cleaning, the analysis pipeline will compute mean differences, variance ratios, and Cohen’s d between alternating and non‑alternating knot groups for each core invariant. Results will be written to `docs/reproducibility/group_comparison.md` as required by SC‑009.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset contains all prime knots with crossing number up to a specified threshold, with validation benchmarking for dataset completeness focused on small crossing numbers (completeness on required invariant fields). Dataset completeness validated against KnotInfo and Hoste‑Thistlethwaite‑Weeks enumeration for prime knot counts at each crossing number within standard enumeration bounds. Crossing numbers 11‑13 data is downloaded but not validated in Phase 1; this is documented in `docs/reproducibility/validation_scope.md` noting the practical constraint (Prime knots at a specific crossing number, source: OEIS A002863, https://oeis.org/A002863) and justification for Phase 1 scope limitation. **Phase 1 Validation Benchmark**: FR‑001 requires downloading ≤ 13 crossings, and SC‑001 validates completeness for ≤ 10 crossings as Phase 1 benchmarking scope. The research question targets ≤ 13 crossings; validation is staged for practical feasibility. **Quantitative Threshold**: Required invariant fields (crossing number, braid index, hyperbolic volume) must have null percentage ≤ 5% per field across all records in the validated dataset subset for hyperbolic prime knots (volume > 0). **Dataset Size Verification**: Total prime knots with crossing number ≤ 13 = 9 988 (source: OEIS A002863, https://oeis.org/A002863).

- **SC-002**: Multiple regression model types (linear, polynomial, and logarithmic) are compared with documented goodness‑of‑fit metrics (R², AIC/BIC, MAE) for each. **Descriptive Interpretation**: R², AIC, and BIC are interpreted as descriptive fit statistics for finite census dataset rather than variance explained in any meaningful statistical sense. **Cross‑Validation Methodology Shift**: The original idea's cross‑validated R‑squared is not applicable for complete census data; goodness‑of‑fit metrics (R², AIC/BIC, MAE) are used instead. This methodology shift is intentional and documented in Assumptions.

- **SC-003**: All code and data transformations must allow an independent researcher to reproduce all intermediate values within a relative error ≤ 1 × 10⁻⁶ of the documented values. Reproducibility artifacts (checksums, derivation notes, random seeds, logs) must be present as specified in FR‑007.

- **SC-004**: Retry logic is verified to execute with exponential backoff (configurable initial delay = 1 s, multiplier = 2, max delay = 32 s) on simulated data source failures, with partial results cached to disk after three consecutive failures. The verification script returns a zero exit code when the backoff schedule and caching behavior conform to the specification (see FR‑008).

- **SC-005** (Phase 2+): ≥ 95% of knots with computable additional invariants have all invariants populated (see US‑5). An invariant is considered "computable" if: (1) a diagram representation is available per FR‑003 (non‑null DT code **or** braid word field), AND (2) the corresponding algorithm is documented in FR‑003 as implementable. Records where either condition fails are excluded from this metric and logged in `docs/reproducibility/uncomputable_invariants.md` with the specific reason (e.g., "no_representation_available", "algorithm_not_implemented").

- **SC-006** (see US‑3): Correlation coefficients and effect‑size reporting are performed as described in FR‑006 and documented in `docs/reproducibility/correlation_report.md`.

- **SC-007**: Tie‑breaking rules for diagram representation ties are documented in `docs/reproducibility/tie_breaking_rules.md` and applied consistently across all invariant computations. Validation script (`docs/reproducibility/tie_breaking_validator.py`) checks that for every knot with multiple representations the rule (braid word preferred over DT code; lexicographically first DT code otherwise) is applied identically. The script must exit with status 0 on success; failures are logged in `docs/reproducibility/validation_status.md`.

- **SC-008**: Core invariants (crossing number, braid index) are TABULATED from Knot Atlas for all knots where diagram representations are available, with coverage documented for records where data is not available. Coverage for each invariant is documented in `docs/reproducibility/invariant_coverage.md` with counts of available vs. unavailable records per invariant.

- **SC-009** (see US‑5): Descriptive comparison metrics (mean differences, variance ratios, and Cohen's d) are computed for alternating vs. non‑alternating knot groups and documented in `docs/reproducibility/group_comparison.md`.

- **SC-010** (see US‑5): Algorithm validation against KnotInfo reference values aims to achieve ≥ 90% match against reference values for each additional invariant where reference coverage is extensive across the dataset. Validation results documented in `docs/reproducibility/algorithm_validation.md` with pass/fail status per invariant and per algorithm, noting any coverage constraints. If KnotInfo reference coverage is < 90%, validation is skipped and the limitation documented.

- **SC-011**: Residual analysis identifies and documents specific hyperbolic knot families (e.g., pretzel, hyperbolic non‑alternating) that deviate significantly (≥ 2 standard deviations from the fitted trend) from model predictions, implementing the methodology from the original idea. Documentation is placed in `docs/reproducibility/residual_analysis.md`. Scope is limited to hyperbolic knots per FR‑012.

- **SC-012**: Hyperbolic volume data completeness for hyperbolic prime knots (volume > 0) with crossing number ≤ 13 crossings, with excluded knots (torus or satellite with zero or undefined volume) documented in `docs/reproducibility/excluded_knots.md`. The validation_scope.md document must contain: (1) crossing number ≤ 10 vs ≤ 13 distinction with data availability counts, (2) justification for Phase 1 scope limitation, (3) data availability vs validated completeness table showing counts per crossing number.

- **SC-013** (see US‑5): Hyperbolic volume data consistency cross‑check against KnotInfo reference values (https://knotinfo.org/) validates ≥ 90% consistency against reference values where reference coverage is available. Cross‑check nature is documented, and if both databases share underlying sources this limitation is explicitly stated. Results are in `docs/reproducibility/hyperbolic_volume_validation.md`.

- **SC-014**: Data quality validation metrics from FR‑002 are measured and documented, including: (1) null percentage ≤ 5% per field in required invariant fields across all records, (2) format validation pass rate ≥ 99% for all records, (3) duplicate records = 0 (see SC‑015). Results are in `docs/reproducibility/data_quality_report.md` with pass/fail status per metric.

- **SC-015**: Duplicate‑record check – the dataset must contain zero duplicate `knot_id` entries. Duplicate detection is performed during parsing; any duplicates trigger a `data_quality_flags` entry and cause the pipeline to abort unless manually overridden. The result is reported in `docs/reproducibility/data_quality_report.md`.

- **SC-016**: Hyperbolic volume data consistency cross‑check (see SC‑013) – duplicated here for completeness.

### Additional Success Criteria (Phase 2+)

- **SC-017**: When Phase 2+ additional invariants are computed, the overall pipeline execution time must remain ≤ 2 hours on a standard GitHub‑Actions runner (2 CPU, 7 GB RAM). Exceeding this limit requires partitioning into resumable sub‑steps, documented in `docs/reproducibility/`.

## Assumptions

- **Computational Constraints (from the idea's reproducibility requirement)**: The entire analysis pipeline (data download, invariant validation, regression analysis, report generation) MUST execute within a single GitHub‑Actions‑class job: within a reasonable timeframe and standard resource limits. Any stage projected to exceed this budget must be partitioned into resumable sub‑steps and the partitioning documented in `docs/reproducibility/`.
- Users have access to stable internet connectivity for downloading data from Knot Atlas and related repositories
- Knot Atlas data format remains stable during the analysis period (no breaking changes to schema or access methods)
- Alternative knot databases (if Knot Atlas is unavailable) will provide compatible data formats for invariant extraction
- The methodology sketch from the idea markdown accurately reflects the intended analytical approach and no fundamental changes are required
- **Phase 1 Validation Staging (Scope Clarification)**: The research question targets the complete census of hyperbolic prime knots with ≤ 13 crossings. Phase 1 validation is staged for practical feasibility: validated completeness benchmark focuses on crossing number ≤ 10 crossings data, while crossing number 11‑13 crossings data is downloaded and available for exploratory analysis. This is a validation staging approach, NOT a scope reduction. Limiting Phase 1 validation to ≤ 10 crossings provides a manageable benchmark while preserving the ability to analyze the full ≤ 13 crossings dataset in exploratory mode. All Phase 1 conclusions MUST be qualified accordingly in final reports (validated findings for ≤ 10 crossings, exploratory for 11‑13 crossings). **Justification**: The complete census of prime knots at a given crossing number contains a corresponding number of knots (source: OEIS, https://oeis.org/), making full validation of all higher‑crossing‑number knots impractical within Phase 1 timeline. Validation staging preserves research scope while enabling practical execution.
- **Prime Knot Enumeration Reference**: The number of prime knots at each crossing number is taken from KnotInfo and the Hoste–Thistlethwaite–Weeks enumeration, confirmed by the Online Encyclopedia of Integer Sequences. Total prime knots at crossing numbers up to a chosen moderate bound: the known count of knots (source: OEIS A002863, https://oeis.org/A002863).
- **Hyperbolic Volume Availability**: Not all prime knots have computable hyperbolic volume (torus and satellite knots have volume zero or undefined). The analysis will filter to knots with valid volume measurements, acknowledging this as a selection bias that should be documented in final reports. **Selection Bias Acknowledgment**: This filtering means conclusions apply only to hyperbolic prime knots, not all prime knots. **Scope Limitation**: The analysis applies only to hyperbolic prime knots (volume > 0); conclusions do not extend to torus or satellite knots. **Invariant Type Distinction**: Combinatorial invariants (crossing number, braid index) and geometric invariants (hyperbolic volume) measure fundamentally different properties; the explanatory relationship may be weak or non‑existent by mathematical definition, not empirical finding. All final reports MUST explicitly acknowledge this distinction.
- **Multicollinearity Acknowledgment**: Crossing number and braid index are not fully independent predictors (braid index ≤ crossing number for most knots per known inequality). This is a definitional relationship, not an empirical finding. This mathematical constraint must be acknowledged in all analysis and coefficient interpretation. VIF assessment (per FR‑005) will quantify multicollinearity concerns as expected consequence of predictor structure.
- **Census Data Statistical Interpretation**: Since the dataset represents a complete census of all prime knots ≤ 13 crossings rather than a sample from a larger population, all statistical analysis is descriptive rather than inferential. Effect sizes are the primary metrics of interest; p‑values are NOT reported for census data (complete enumeration; effect sizes are the primary metrics, per research.md). Train/test splits, ANOVA assumption checks, and inferential statistics are not applicable for complete census data. **Constitution Principle VII Exception**: Constitution Principle VII requires explicit significance thresholds for statistical claims. For complete census data, p‑values are inapplicable; this is an explicit exception to Principle VII documented in FR‑006 and Assumptions. All statistical claims for census data use effect sizes instead.
- **Measurement Precision Standard**: Consistent with rigorous scientific measurement standards, the analysis must establish precision thresholds for all computed invariants before correlation analysis proceeds. This includes documenting computational uncertainty for braid index (which requires algorithmic determination) versus crossing number (which is tabulated). This standard is implemented through FR‑003 algorithm validation and SC‑010 validation against reference values. As reviewer marie‑curie noted, "we did not claim a new element until the atomic weight could be determined with precision." Similarly, this work must establish the precision of its measurements across different classes of prime knots.
- **Sample Size Documentation**: With the known number of prime knots at a specific crossing number (source: OEIS sequences documenting prime knot enumerations, https://oeis.org/A002863), stratified analysis by alternating/non‑alternating classification may yield sufficient sample sizes for high‑crossing‑number groups but potentially insufficient power for lower crossing number groups. Stratified subgroup counts will be reported as descriptive facts, not power adequacy assessments.
- **Invariant Redundancy Acknowledgment**: Additional invariants (arc index, Seifert circle count, bridge number) have known mathematical constraints with crossing number and braid index. Computing these may provide redundant information rather than independent signals. Validation is exploratory correlation analysis, not independence testing. Additional invariants cannot claim independent predictive value beyond crossing number and braid index.
- **Model Form Selection**: Model forms (linear, polynomial, logarithmic) selected based on prior knot theory literature showing non‑linear relationships between topological invariants. Analysis is exploratory with theoretical grounding from prior work.
- **Correlation Method Selection**: Spearman correlation is primary for discrete integer‑valued invariants; Pearson correlation is supplementary for reporting completeness. This acknowledges discrete data limitations while maintaining reporting convention.
- **Joint Regression Coefficient Interpretation**: Joint regression coefficients represent variance partitioning within the finite census dataset, NOT independent explanatory power. Due to the known mathematical constraint (braid index ≤ crossing number), coefficient estimates are descriptive associations within the census, not interpretable as independent effects. All final reports MUST explicitly state this limitation to prevent misinterpretation of joint model coefficients.
- **Research Methodology Adjustments**: The following methodology shifts from the original idea are intentional adjustments based on census data constraints:
 - **Train/Test Split Removal**: The original idea's 80/20 train/test split is not applicable for complete census data; analysis is descriptive rather than predictive validation. Complete census data means there is no "hold‑out" set to validate predictive performance; all available data is used for descriptive analysis. Model validation uses goodness‑of‑fit metrics (R², AIC/BIC) rather than predictive hold‑out accuracy.
 - **ANOVA Removal**: The original idea specified ANOVA to compare model fit between alternating and non‑alternating subsets. For complete census data, ANOVA is not applicable; descriptive statistics (mean differences, variance ratios) suffice for exact population parameters.
 - **Cross‑Validation Removal**: The original idea specified cross‑validated R‑squared for model selection. For complete census data, cross‑validation is not applicable; goodness‑of‑fit metrics (R², AIC/BIC, MAE) are used for model selection. Cross‑validation estimates predictive performance on held‑out samples; census data has no held‑out samples.
 - **Rationale**: These adjustments preserve scientific rigor while acknowledging that the dataset is a complete enumeration, not a sample from a larger population. All adjustments are documented in FR‑005, SC‑002, and Assumptions for transparency.
- **Phase 2+ Scope Boundary**: Additional invariants (arc index, Seifert circle count, bridge number) are explicitly excluded from Phase 1 implementation and reserved for exploratory extension only after primary results are established. **Algorithm Validation**: System MUST validate algorithm implementation correctness for additional invariants against available reference values from KnotInfo with ≥ 90% match against reference values. If KnotInfo reference coverage is < 90%, validation is skipped and the limitation documented. **Representation Availability**: Invariant computation requires at least one non‑null diagram representation (DT code **or** braid word). When no representations are available, the record is flagged and excluded from invariant computation but retained in the dataset for documentation purposes. **Mathematical Constraint Acknowledgment**: Additional invariants have known mathematical constraints with crossing number and braid index (e.g., bridge number ≤ crossing number). Validation is exploratory correlation analysis, not independence testing. Additional invariants cannot claim independent predictive value beyond crossing number and braid index. **Algorithm Implementation**: Arc index computed via Birman‑Menasco algorithm (source: arXiv preprint), Seifert circle count via Seifert's algorithm = s(D) (source: arXiv preprint, https://arxiv.org/abs/math/...), bridge number via Schubert's decomposition (source: https://en.wikipedia.org/wiki/Bridge_number).

## Constitution

### Principle VII (Statistical Significance)

**All statistical claims MUST include explicit significance thresholds (p‑values, confidence intervals). For complete census data (complete enumeration of a finite population), p‑values are inapplicable; this is an explicit exception to this principle. For census data, effect sizes are the required metrics of interest, and all statistical claims MUST report effect sizes (Cohen's d, r, r²) as specified in FR‑006 and Assumptions.**


