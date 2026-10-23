# Feature Specification: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Feature Branch**: `001-data-transformation-sensitivity`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "How do common data transformation techniques (Box-Cox, Yeo-Johnson, rank-based) alter the Type I error rate and statistical power of parametric tests (t-test, ANOVA) when applied to non-normal data from real-world distributions?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Filter Real-World Datasets (US-1) (Priority: P1)

As a researcher, I want to download and filter public datasets from UCI and OpenML that contain continuous variables and known group labels, so that I have valid real-world non-normal data for transformation analysis.

**Why this priority**: This is the foundational step—without valid datasets, no transformations or tests can be run. All downstream analysis depends on this.

**Independent Test**: Can be fully tested by executing the dataset download script and verifying that at least 50 datasets meet the filtering criteria (Shapiro‑Wilk p < 0.05, N ≥ 30, continuous variables present).

**Acceptance Scenarios**:

1. **Given** the UCI/OpenML dataset repository is accessible, **When** the download script executes with the specified query parameters, **Then** at least 50 datasets are downloaded and stored locally with metadata preserved, and their SHA‑256 checksums are recorded in `data/checksums.csv`.
2. **Given** a downloaded dataset, **When** the Shapiro‑Wilk normality test is applied to its continuous variables, **Then** datasets with p < 0.05 are retained and datasets with p ≥ 0.05 are excluded with logging.
3. **Given** a filtered dataset, **When** sample size is verified, **Then** datasets with N ≥ 30 are retained and datasets with N < 30 are excluded with logging.

---

### User Story 2 - Apply Transformations and Run Type I Error Tests (US-2) (Priority: P2)

As a researcher, I want to apply Box‑Cox, Yeo‑Johnson, and rank‑based transformations to each dataset and run t‑tests/ANOVA under null conditions, so that I can measure Type I error rates for each transformation‑test combination.

**Why this priority**: This is the core analytical work for Type I error estimation. Power estimation requires separate simulated data (US-4).

**Independent Test**: Can be fully tested by running the transformation and null simulation pipeline on a single dataset and verifying that Type I error is estimated via label shuffling (**[deferred] iterations**) with a fixed random seed.

**Acceptance Scenarios**:

1. **Given** a filtered dataset with continuous variables, **When** the three transformations (Box‑Cox with λ optimized per dataset, Yeo‑Johnson with λ optimized per dataset, rank‑based inverse normal) are applied, **Then** transformed data is produced for each method without errors.
2. **Given** transformed data, **When** group labels are shuffled **1,000 times** for null simulation with a fixed random seed (e.g., 42), **Then** t‑test/ANOVA p‑values are computed and the proportion of p < 0.05 is recorded as the Type I error estimate.

---

### User Story 3 - Aggregate Results and Generate Reports (US-3) (Priority: P3)

As a researcher, I want to aggregate results across all datasets and generate summary tables and bar plots showing error rates and power by transformation and test type, so that I can compare transformation effects and produce reproducible outputs.

**Why this priority**: This produces the final deliverables that answer the research question. It depends on US-2 and US-4 completing successfully.

**Independent Test**: Can be fully tested by executing the aggregation script on pre‑computed results and verifying that summary tables contain mean Type I error and power for each transformation‑test combination with bootstrap confidence intervals.

**Acceptance Scenarios**:

1. **Given** per‑dataset transformation‑test results, **When** the aggregation script runs, **Then** mean Type I error and power are computed for each transformation‑test combination across all datasets.
2. **Given** aggregated metrics, **When** bootstrap confidence intervals are computed, **Then** the intervals are included in the summary tables alongside point estimates (target half‑width ≤ 0.07, see SC‑004).
3. **Given** summary tables, **When** visualization scripts execute, **Then** bar plots (matplotlib/seaborn) are produced showing error rates and power by transformation and test type.

---

### User Story 4 - Simulate Data with Known Ground Truth for Power Analysis (US-4) (Priority: P4)

As a researcher, I want to generate simulated datasets with known effect sizes and group differences, so that I can measure statistical power (true positive rate) for each transformation‑test combination against ground truth.

**Why this priority**: Power requires known ground truth (true effect size), which real‑world datasets cannot provide. This is essential for valid power estimation.

**Independent Test**: Can be fully tested by running the simulation pipeline with fixed effect sizes and verifying that power estimates match analytically expected power values (derived from the non‑central t distribution; see Cohen 1988) within a 95 % CI half‑width ± 0.02.

**Acceptance Scenarios**:

1. **Given** specified effect sizes (Cohen's d ∈ {0.2 (small), 0.5 (medium), 0.8 (large)}), **When** simulated datasets are generated with known group differences, **Then** at least 1,000 simulated datasets per effect size are produced with ground‑truth labels.
2. **Given** simulated datasets with transformations applied, **When** t‑test/ANOVA is run, **Then** the proportion of significant results (p < 0.05) is recorded as the power estimate for each transformation‑test‑effect combination.
3. **Given** power estimates, **When** bootstrap confidence intervals are computed, **Then** the intervals are validated against the ±0.02 half‑width target and compared to the analytical benchmark values.

---

### Edge Cases

- **Missing values**: System MUST impute missing values using mean for near‑symmetric variables and median for skewed variables (≤ 10 % missing per variable). A sensitivity analysis (FR‑011) will compare results with and without imputation to assess impact on error‑rate and power estimates.
- **Transformation failure** (e.g., Box‑Cox requires positive values): System MUST skip the failing transformation for that variable, apply a log‑shift to make values positive, and log the intervention; verify that intervention is logged with variable name and reason.
- **Insufficient samples for Shapiro‑Wilk (N < 30)**: System MUST exclude the dataset and log the reason; verify that exclusion is recorded in an exclusion log with dataset ID.
- **All non‑significant null simulations**: System MUST record Type I error and include the bootstrap CI; verify that CI bounds are recorded.
- **Extended computational time**: System MUST checkpoint progress after each dataset and allow resumption from the last checkpoint; verify that checkpoint file is created and contains valid state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download at least 50 public datasets from UCI Machine Learning Repository and OpenML with explicit dataset URLs recorded in `data/datasets.csv` and store them locally with metadata preservation (See US‑1).  
- **FR-018**: System MUST maintain a candidate‑dataset registry and ensure that the selected 50+ datasets span at least three distinct domains (e.g., health, finance, image) to provide breadth of real‑world non‑normality (See US‑1).  
- **FR-014**: System MUST ensure that after filtering, at least 45 datasets remain for downstream analysis; if fewer remain, the pipeline shall log a warning and abort (See US‑1).  
- **FR-002**: System MUST filter datasets using Shapiro‑Wilk normality test (p < 0.05) and sample size (N ≥ 30) criteria, excluding non‑conforming datasets with logging (See US‑1).  
- **FR-003**: System MUST apply three transformations (Box‑Cox with λ optimized per dataset, Yeo‑Johnson with λ optimized per dataset, rank‑based inverse normal) to each continuous variable (See US‑2).  
- **FR-004**: System MUST estimate Type I error rate by shuffling group labels **[deferred] times** with a fixed random seed (e.g., 42), recording the proportion of t‑test/ANOVA p‑values < 0.05 (See US‑2).
- **FR-017**: System MUST use **only** label‑shuffling for null‑simulation; residual permutation is **not** employed (See US‑2).  
- **FR-005**: System MUST generate simulated datasets with known effect sizes (Cohen's d ∈ {0.2, 0.5, 0.8}) and ground‑truth labels for power analysis (See US‑4).  
- **FR-006**: System MUST compute statistical power by testing simulated data with known ground truth and recording the proportion of significant results (p < 0.05) for each transformation‑test‑effect combination (See US‑4).  
- **FR-007**: System MUST aggregate results across all available datasets and compute mean Type I error and power for each transformation‑test combination with bootstrap confidence intervals (See US‑3).  
- **FR-008**: *(Removed – original omnibus Friedman test was out of scope.)*  
- **FR-009**: System MUST produce summary tables and bar plots (matplotlib/seaborn) showing error rates and power by transformation and test type (See US‑3).  
- **FR-010**: System MUST compute SHA checksums for all downloaded datasets and record them under `data/checksums.csv` (See US‑1).  
- **FR-011**: System MUST conduct a sensitivity analysis comparing results obtained with mean/median imputation versus results obtained after removing any rows with missing values, reporting any change in Type I error or power; any absolute change > 0.02 triggers a warning (See US‑3, SC‑005).  
- **FR-012**: System MUST apply a hierarchical bootstrap that resamples both datasets and, within each dataset, the permutation‑based error‑rate estimates, to produce confidence intervals that reflect both between‑ and within‑dataset uncertainty (See US‑3, SC‑004).  
- **FR-013**: System MUST enforce a runtime limit of **6 hours** per GitHub Actions job; scripts shall checkpoint after each dataset and abort gracefully if the limit is approached, ensuring reproducibility (See US‑1, US‑2, US‑3).  
- **FR-016**: System MUST perform imputation (mean for near‑symmetric, median for skewed variables) **prior** to any transformation step and record the imputation method per variable in a provenance log (See US‑2, FR‑011).

### Key Entities *(include if feature involves data)*

- **Dataset**: Represents a public data source from UCI/OpenML; key attributes: source URL, sample size, number of continuous variables, Shapiro‑Wilk p‑value, group label existence, SHA‑256 checksum.  
- **Transformation**: Represents one of three methods (Box‑Cox, Yeo‑Johnson, rank‑based); key attributes: method name, λ parameter (for Box‑Cox/Yeo‑Johnson), transformed variable values.  
- **TestResult**: Represents outcome of a statistical test; key attributes: test type (t‑test/ANOVA/Mann‑Whitney U), p‑value, significance flag, transformation applied, null/alternative condition, effect size (for simulated data).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset download and filtering outcomes (count ≥ 50, filtering correctness, metadata preservation) are measured against US‑1 acceptance criteria to validate data acquisition pipeline (See US‑1).  
- **SC-002**: Type I error rate is measured against the nominal α = 0.05 threshold to assess whether transformations maintain or inflate false positive rates (See US‑2).  
- **SC-003**: Statistical power is measured against analytically expected power values for each Cohen's d (a modest proportion → approximately the same modest proportion, ≈ a moderate proportion (about one‑half), ≈ a high proportion) derived from the non‑central t distribution (Cohen 1988) to assess whether transformations improve or reduce detection of true group differences (See US‑4).  
- **SC-004**: Bootstrap confidence‑interval half‑width is measured against a target of **≤ 0.07** to assess precision of aggregated estimates. This relaxed target reflects realistic variability when fewer than 45 usable datasets remain after filtering, while still providing useful precision (See US‑3, FR‑012).  
- **SC-005**: Imputation sensitivity analysis reports the absolute change in Type I error and power when imputation is omitted; any change > 0.02 triggers a warning (See US‑3, FR‑011).

## Assumptions

- **Compute feasibility**: All analysis runs on GitHub Actions free‑tier runner (CPU cores, ~7 GB RAM, 6 h per job; no GPU, no large‑model training).  
- **Dataset‑variable fit**: UCI and OpenML datasets contain continuous variables and group labels required for t‑test/ANOVA; datasets lacking either are excluded with logging (enforced by FR‑002).  
- **Inference framing**: All findings are framed as ASSOCIATIONAL (observational design, no random assignment); no causal claims are made about transformation effects.  
- **Multiplicity correction**: Bonferroni correction is used for any post‑hoc pairwise comparisons that may be added in future extensions; the current scope does not require an omnibus test.  
- **Threshold justification**: The α = 0.05 significance threshold follows community‑standard practice; the α‑sweep range was removed to stay within the original research question.  
- **Measurement validity**: No questionnaires/instruments are used; data is from public repositories with documented variable definitions.  
- **Predictor collinearity**: Transformations are mutually exclusive per variable (one method applied at a time); no collinearity diagnostics required.  
- **Data handling**: Missing values are imputed using mean (near‑symmetric) or median (skewed) per variable; datasets with > 10 % missing are excluded (FR‑002). FR‑011 explicitly evaluates the impact of this imputation.  
- **Transformation handling**: Box‑Cox requires positive values; log‑shift is applied when necessary and logged (Edge Cases).  
- **Checkpointing**: System checkpoints after each dataset to allow resumption if a predefined time limit is approached (FR‑013).  
- **Null‑simulation strategy**: Type I error estimation relies solely on label shuffling; residual permutation is not employed (FR‑017).  
