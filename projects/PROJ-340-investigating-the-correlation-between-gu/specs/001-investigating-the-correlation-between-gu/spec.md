# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Feature Branch**: `001-gut-microbiome-sleep-architecture`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1)

The system must ingest raw metagenomic sequencing data (predictors) and polysomnography/actigraphy sleep metrics (outcomes) from a provided dataset, validate that all required variables are present, and execute the entire analysis pipeline within a strict time limit on a standard CI runner.

**Why this priority**: This is the foundational step. Without valid data ingestion, a check for variable completeness, and a guaranteed execution environment, no statistical analysis can proceed. It ensures the "Dataset-variable fit" methodological soundness requirement is met before any computation begins.

**Independent Test**: Can be fully tested by running the data loader script against a mock dataset with a known missing variable (e.g., "REM duration") and verifying the system halts with a specific error message citing the missing field, and by running a dummy pipeline on the specified runner to verify it completes within the time limit.

**Acceptance Scenarios**:

1. **Given** a dataset containing stool metagenomic counts and sleep stage durations, **When** the ingestion pipeline runs, **Then** the system loads the data and reports a success status with a summary of variable counts.
2. **Given** a dataset missing the "Slow-Wave Sleep (SWS) duration" column, **When** the ingestion pipeline runs, **Then** the system halts execution and outputs an error message: "Dataset-variable fit check failed: Variable 'SWS duration' is missing from the source."
3. **Given** a valid dataset and the standard CI environment, **When** the full analysis pipeline is triggered, **Then** the system completes all steps (ingestion, analysis, reporting) within 6 hours.

---

### User Story 2 - Robust Associational Correlation Analysis (Priority: P2)

The system must compute correlations between microbial taxa abundances and sleep architecture metrics, explicitly framing results as associational (not causal), applying corrections for multiple comparisons, and selecting the statistical method based on rigorous data distribution tests.

**Why this priority**: This delivers the core research value: answering the primary research question. It addresses the "Inference framing", "Multiplicity & power", and "Data distribution" methodological requirements by ensuring statistical rigor and appropriate model selection.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset with known zero-inflation and non-normality, verifying the system selects the correct model (ZINB or Spearman), outputs the correct coefficients, and includes Benjamini-Hochberg adjusted p-values.

**Acceptance Scenarios**:

1. **Given** a dataset with 50 microbial taxa and 4 sleep metrics, **When** the correlation analysis runs, **Then** the system outputs a matrix of correlation coefficients and raw p-values.
2. **Given** 200 hypothesis tests (50 taxa × 4 metrics), **When** the analysis completes, **Then** the system outputs a corrected p-value column using the Benjamini-Hochberg method to control the False Discovery Rate (FDR) at q ≤ 0.05.
3. **Given** the analysis output, **When** a user reads the "Interpretation" section, **Then** the text explicitly states "These results represent an associational relationship" and avoids causal language like "causes" or "leads to."
4. **Given** a dataset where the Shapiro-Wilk test yields p < 0.05 AND the proportion of zeros > 30%, **When** the analysis runs, **Then** the system selects a Zero-Inflated Negative Binomial (ZINB) or Hurdle model for correlation estimation.
5. **Given** a dataset where the Shapiro-Wilk test yields p < 0.05 BUT the proportion of zeros ≤ 30%, **When** the analysis runs, **Then** the system selects Spearman rank correlation.

---

### User Story 3 - Threshold Sensitivity, Collinearity Diagnostics, and Power Analysis (Priority: P3)

The system must perform a sensitivity analysis on significance thresholds, calculate multivariate collinearity diagnostics (excluding linearly dependent pairs), and perform a formal power analysis to validate sample size adequacy.

**Why this priority**: This ensures the robustness of the findings against arbitrary cutoff choices, prevents spurious results from correlated predictors, and validates that the study is capable of detecting effects, satisfying the "Threshold justification", "Predictor collinearity", and "Power" methodological requirements.

**Independent Test**: Can be fully tested by running the diagnostics on a dataset with known collinearity structures and varying sample sizes, verifying the system flags high VIFs correctly, detects linear dependence, and reports power calculations.

**Acceptance Scenarios**:

1. **Given** a set of significant correlations at p < 0.05, **When** the sensitivity analysis runs, **Then** the system re-calculates significance at p < 0.01 and p < 0.10 and reports the percentage change in the number of significant findings for each threshold.
2. **Given** a pair of microbial taxa that are definitionally related (nested taxonomic hierarchy), **When** the collinearity diagnostic runs, **Then** the system detects the linear dependence via matrix rank check and flags the pair as "Perfect Multicollinearity" without attempting a standard VIF calculation.
3. **Given** a set of predictors in a multivariate model, **When** the collinearity diagnostic runs, **Then** the system calculates the Variance Inflation Factor (VIF) for each predictor against the set of *other* predictors and flags any predictor with VIF > 5.
4. **Given** a dataset with N subjects, **When** the power analysis runs, **Then** the system calculates the minimum sample size required to detect a correlation of r ≥ 0.3 with power ≥ 0.80 at α = 0.05, and flags the study as "Underpowered" if N is below this threshold.

---

### Edge Cases

- **Zero-Inflated Data**: If the dataset contains zero-inflated count data (proportion of zeros > 30% OR Shapiro-Wilk p < 0.05), the system MUST switch to a Zero-Inflated Negative Binomial (ZINB) or Hurdle model. If the data is non-normal (Shapiro-Wilk p < 0.05) but not zero-inflated, the system MUST switch to Spearman rank correlation. For compositional data, the system SHOULD use SparCC or SpiecEasi if available.
- **Sample Size / Power**: The system MUST perform a power analysis based on the expected effect size (r ≥ 0.3) and power (≥ 0.80). If the observed sample size N is insufficient to achieve this power, the system MUST flag a "Power Limitation" in the output and report the calculated minimum N required.
- **Outliers**: If the sleep data contains outliers (values > 1.5x IQR above the 75th percentile or < 1.5x IQR below the 25th percentile), the system MUST exclude these specific data points from the correlation analysis and report the number of excluded points.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest metagenomic count data and sleep stage metrics from a CSV/TSV source and validate the presence of all required predictor and outcome variables. (See US-1)
- **FR-002**: System MUST compute pairwise correlations between microbial taxa and sleep architecture metrics. The system MUST select the correlation method based on the following priority: 1) If zero-inflation is detected (proportion of zeros > 30% OR Shapiro-Wilk p < 0.05), use a Zero-Inflated Negative Binomial (ZINB) or Hurdle model; 2) Else if non-normality is detected (Shapiro-Wilk p < 0.05), use Spearman rank correlation; 3) Else use Pearson correlation. (See US-2)
- **FR-003**: System MUST apply a multiple-comparison correction (Benjamini-Hochberg) to all generated p-values to control the False Discovery Rate at q ≤ 0.05. (See US-2)
- **FR-004**: System MUST explicitly label all statistical findings as "associational" and prohibit the generation of causal language in the final report. (See US-2)
- **FR-005**: System MUST perform a sensitivity analysis by re-running significance tests at three distinct thresholds (p < 0.01, p < 0.05, p < 0.10) and report the variation in significant findings. (See US-3)
- **FR-006**: System MUST calculate Variance Inflation Factors (VIF) for each predictor against the set of other predictors in the multivariate model. For any pair of predictors that are definitionally related (linearly dependent), the system MUST detect this via matrix rank check and flag it as "Perfect Multicollinearity" without calculating VIF. For all other predictors, the system MUST flag any with VIF > 5. (See US-3)
- **FR-007**: System MUST execute the entire analysis pipeline within 6 hours on a `ubuntu-latest` GitHub Actions runner. (See US-1, Assumption-001)

### Key Entities

- **MicrobialTaxon**: Represents a specific bacterial species or genus, with attributes: `taxon_name`, `abundance_count`, `relative_abundance`.
- **SleepMetric**: Represents a sleep architecture variable, with attributes: `metric_name` (e.g., "REM_duration", "SWS_percentage"), `value`, `unit`.
- **CorrelationResult**: Represents the output of a statistical test, with attributes: `taxon`, `sleep_metric`, `correlation_coefficient`, `p_value_raw`, `p_value_adjusted`, `is_significant`, `method_used`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The percentage of required variables successfully loaded from the dataset is measured against the total number of variables required by the research design. (See US-1)
- **SC-002**: The stability of the "significant findings" count is measured against the variation observed when sweeping the significance threshold across {0.01, 0.05, 0.10}. (See US-3)
- **SC-003**: The presence of collinearity warnings is measured against the calculated VIF values for all predictor pairs and the detection of linear dependence. (See US-3)
- **SC-004**: The total execution time of the analysis pipeline is measured against the 6-hour CI runner limit on `ubuntu-latest`. (See FR-007)
- **SC-005**: The statistical power of the study is measured against the calculated minimum sample size required to detect an effect size of r ≥ 0.3 with power ≥ 0.80. (See US-3)

## Assumptions

- **Assumption-001 (Computational Constraints)**: The project assumes the dataset size is small enough (N < 1000 subjects, < 500 taxa) to fit within 7 GB of RAM and complete within 6 hours on a standard CPU-only `ubuntu-latest` GitHub Actions runner without GPU acceleration.
- **Data Availability**: The project assumes access to a public or internal dataset that contains both metagenomic sequencing data (stool samples) and concurrent polysomnography or actigraphy sleep data for the same subjects. If the dataset lacks specific sleep stages (e.g., only total sleep time is available), the analysis scope will be reduced to available metrics.
- **Statistical Method**: The project assumes that standard correlation methods (Pearson/Spearman) or zero-inflated models (ZINB) are sufficient for the initial exploratory phase, and more complex compositional models (SparCC) will be used if data compositionality is detected.
- **Observational Nature**: The project assumes the data is purely observational (no randomization of microbiome composition), and therefore all results will be framed as associations rather than causal effects.
- **Threshold Justification**: The project assumes a standard significance threshold of p < 0.05 (adjusted) is the community standard for initial discovery, with sensitivity analysis performed at 0.01 and 0.10 to test robustness.