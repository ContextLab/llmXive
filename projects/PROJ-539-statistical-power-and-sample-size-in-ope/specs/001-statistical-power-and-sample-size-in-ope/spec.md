# Feature Specification: Statistical Power and Sample Size in Open Neuroimaging Datasets

**Feature Branch**: `sample-size-reproducibility-analysis`  
**Created**: 2026-10-21  
**Status**: Draft  
**Input**: *Research question*: “How does sample size in open neuroimaging datasets correlate with the reproducibility of reported effect sizes across independent studies?”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify the relationship between sample size and effect‑size reproducibility (Priority: P1)

A neuroscientist wants to know whether larger publicly‑available neuroimaging datasets yield more stable (i.e., reproducible) effect‑size estimates across independent publications. The story is independent: the researcher can run the entire workflow on a single dataset and obtain a usable result.

**Why this priority**: It directly answers the validated research question and provides the core empirical evidence needed for the project’s scientific claim.

**Independent Test**: Execute the end‑to‑end pipeline on a single open dataset (e.g., the “ds000001” OpenNeuro collection) and verify that a regression output, a reproducibility metric, and a visualization are produced without errors.

**Acceptance Scenarios**:

1. **Given** an open neuroimaging dataset with ≥ 2 published independent analyses, **when** the pipeline extracts sample sizes and effect sizes, computes the coefficient of variation (CV) of effect sizes, and runs a linear regression of CV on sample size, **then** a CSV file containing the regression coefficients, a PNG plot of “Sample Size vs. CV”, and a short JSON summary are generated.

2. **Given** the same dataset but with only one published analysis, **when** the pipeline attempts to compute CV, **then** it logs a warning “Insufficient independent studies for reproducibility metric” and skips the regression step while still producing a summary indicating “Not enough data”.

### User Story 2 – Sensitivity to the reproducibility‑metric threshold (Priority: P2)

A methodologist wants to verify that the observed correlation is robust to reasonable variations in how reproducibility is quantified (e.g., using CV versus inter‑quartile range).

**Why this priority**: Demonstrates methodological soundness by ensuring that conclusions do not hinge on an arbitrary metric choice.

**Independent Test**: Re‑run the pipeline with the reproducibility metric set to CV, then to IQR‑based variability, and compare the regression slopes.

**Acceptance Scenario**:

1. **Given** the pipeline configured with two reproducibility metrics (CV and IQR), **when** the analysis is executed on the same set of datasets, **then** a table reporting both slopes and their 95 % confidence intervals is produced, and the difference in slopes is ≤ 0.05 (i.e., negligible) or is explicitly reported.

### User Story 3 – Multiple‑comparison correction when testing several datasets (Priority: P3)

A reviewer requests that the project control the family‑wise error rate because the regression will be run separately on each of the 3–5 selected datasets.

**Why this priority**: Prevents inflated Type I error when interpreting multiple regression results.

**Independent Test**: After running the regression on each dataset, the pipeline applies a Bonferroni correction to the set of p‑values.

**Acceptance Scenario**:

1. **Given** regression p‑values from five datasets, **when** the Bonferroni correction is applied, **then** an adjusted‑p column is added to the results table and the significance decision is based on the corrected level α = 0.05/5.

### Edge Cases

- **Boundary condition**: A dataset reports sample size as “0” (e.g., a placeholder). The pipeline must detect non‑positive sample sizes, log an error, and exclude the dataset from the regression.
- **Error scenario**: Effect‑size values are reported in heterogeneous metrics (Cohen’s d, Pearson r, odds ratio). The pipeline must attempt to convert all to a common metric; if conversion fails for a study, that study is omitted with a logged warning.
- **Missing data**: No published effect sizes are found for a dataset. The pipeline should produce a “No data” status for that dataset without aborting the whole run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download a list of open neuroimaging datasets from OpenNeuro or ADNI as specified in a configuration file (See US-1).  
- **FR-002**: The system MUST parse published articles (via PubMed‑Central XML or PDF‑extracted tables) to extract **sample size** and **effect‑size** for each independent analysis that uses a given dataset (See US-1).  
- **FR-003**: The system MUST compute a reproducibility metric for each dataset (default: coefficient of variation of effect sizes) and optionally alternative metrics (IQR‑based) (See US-2).  
- **FR-004**: The system MUST perform a simple linear regression of the reproducibility metric on sample size for each dataset (See US-1).  
- **FR-005**: The system MUST apply a Bonferroni family‑wise‑error correction across all regression p‑values when more than one dataset is analysed (See US-3).  
- **FR-006**: The system MUST generate (a) a CSV file with regression coefficients, (b) a PNG plot “Sample Size vs. Reproducibility”, and (c) a JSON summary containing raw metrics and corrected p‑values (See US-1).  
- **FR-007**: The system MUST log informative warnings for any dataset that fails pre‑conditions (e.g., non‑positive sample size, missing effect sizes, heterogeneous effect‑size units) and continue processing remaining datasets (See Edge Cases).  
- **FR-008**: The system MUST run entirely on a CPU‑only environment and complete within 5 hours on a GitHub‑Actions free‑tier runner (≤ 2 CPU, ≈ 7 GB RAM) (See Assumptions).  

### Success Criteria *(mandatory)*

- **SC-001**: Regression output CSV contains a non‑null slope estimate for every dataset that meets the minimum‑data requirement (≥ 2 independent effect‑size reports) (See FR-004).  
- **SC-002**: PNG plot is generated for each processed dataset and can be opened without error (See FR-006).  
- **SC-003**: Bonferroni‑adjusted p‑values are ≤ 0.05 for at most one dataset unless the raw p‑values are all > 0.05, confirming that family‑wise error control is applied (See FR-005).  
- **SC-04**: Sensitivity analysis (CV vs. IQR) yields regression slopes that differ by ≤ 0.05 or the difference is explicitly reported in the JSON summary (See FR-003, US-2).  
- **SC-05**: Total wall‑clock runtime on the CI runner does not exceed 5 hours and peak memory usage stays below 6 GB (See FR-008).  

## Assumptions

- The selected open neuroimaging datasets each have **≥ 2** peer‑reviewed publications that report quantitative effect sizes for the same primary outcome (e.g., activation contrast, connectivity metric).  
- Reported effect sizes are either Cohen’s d, Pearson r, or odds ratios; a deterministic conversion to a common metric (Cohen’s d) exists and is applied.  
- Published effect‑size tables are machine‑readable (XML/HTML or well‑structured PDFs). If not, manual curation is outside the scope of this feature.  
- Post‑hoc power estimates will be computed using the standard two‑sample t‑test formula (α = 0.05, two‑tailed) implemented in the open‑source `statsmodels` library.  
- The linear relationship between sample size and reproducibility metric is assumed *associational*; no causal claim will be made.  
- All statistical calculations are performed with `numpy`/`pandas`/`statsmodels` on CPU; no GPU or large‑model inference is required.  
- The CI environment provides internet access to download datasets and open‑access articles; any pay‑walled source would cause the pipeline to skip that dataset with a logged warning.  

---  

*End of specification.*
