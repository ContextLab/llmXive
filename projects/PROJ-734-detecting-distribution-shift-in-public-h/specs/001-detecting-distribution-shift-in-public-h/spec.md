# Feature Specification: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

**Feature Branch**: `001-detect-distribution-shift`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: “Detect distributional shifts in CDC FluView weekly ILI rates using kernel two‑sample tests (MMD) and compare performance to Pettitt and Bayesian online change‑point methods.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Automated shift detection for public‑health analysts (Priority: P1)

An analyst wants to run a reproducible pipeline that flags weeks where the ILI distribution has changed, and obtain quantitative performance metrics (precision, recall, detection delay) against a known list of outbreak weeks.

**Why this priority**: This delivers the core scientific value—demonstrating that kernel two‑sample tests can be used for early outbreak monitoring.

**Independent Test**: Execute the full pipeline on the FluView dataset and verify that a CSV of flagged weeks is produced together with a summary report containing the required metrics.

**Acceptance Scenarios**:

1. **Given** the FluView ILI CSV is available, **when** the pipeline is executed with default parameters, **then** a `flags.csv` file is created listing all weeks with p < 0.01 (Bonferroni‑adjusted) and a `report.pdf` containing precision, recall, detection delay, and false‑positive rate is generated.  
2. **Given** a ground‑truth list of outbreak weeks, **when** the report is inspected, **then** the precision, recall, and average detection delay are computed within a ±2‑week tolerance window.

### User Story 2 – Baseline change‑point comparison (Priority: P2)

A researcher wants to see how the kernel‑based detector stacks up against classic methods (Pettitt test and Bayesian Online Change‑Point Detection) on the same data.

**Why this priority**: Provides the necessary benchmark to evaluate added value of the kernel approach.

**Independent Test**: Run the baseline methods on the same pre‑processed series and verify that their detected change points are reported alongside the MMD results.

**Acceptance Scenarios**:

1. **Given** the pre‑processed ILI series, **when** the Pettitt and BOCPD algorithms are invoked, **then** a `baselines.csv` file lists their detected change weeks and associated statistics (test statistic, posterior run‑length, etc.).

### User Story 3 – Robustness & sensitivity analysis (Priority: P3)

A statistician wants to assess how sensitive the detector is to the choice of kernel bandwidth and window length before deploying it operationally.

**Why this priority**: Ensures methodological defensibility and guards against over‑fitting to a single hyper‑parameter setting.

**Independent Test**: Execute the sensitivity module, which reruns the detector over a grid of bandwidths and window lengths, and verify that a `sensitivity.csv` summarising metric variation is produced.

**Acceptance Scenarios**:

1. **Given** the default pipeline, **when** the sensitivity analysis is triggered, **then** the system runs MMD with (i) median‑heuristic bandwidth, (ii) cross‑validated bandwidth, and (iii) three window lengths (8, 12, 16 weeks), and records precision, recall, and detection delay for each configuration in `sensitivity.csv`.

---

### Edge Cases

- What happens when a week is missing from the FluView CSV?  
- How does the system behave if the ILI series is constant (zero variance) over a window?  
- How are extreme outliers (e.g., a single week with an implausibly high ILI value) handled during preprocessing?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the CDC FluView weekly ILI CSV (≈ 20 years, < 10 MB) and store it locally for analysis. *(See US-1)*
- **FR-002**: System MUST preprocess the series by (a) removing weeks with missing values, (b) applying a log‑transform, and (c) standardizing to zero mean and unit variance. *(See US-1)*
- **FR-003**: System MUST compute the Gaussian‑kernel Maximum Mean Discrepancy (MMD) statistic for every pair of consecutive 12‑week windows (stride = 1 week) and estimate a null distribution using 1 000 permutations. *(See US-1)*
- **FR-004**: System MUST flag a shift when the two‑sample p‑value is **< 0.01** after Bonferroni correction for the total number of window‑pairs, citing the standard α = 0.01 family‑wise error control as justification. *(See US-1)*
- **FR-005**: System MUST run the Pettitt test (sliding‑window adaptation) and Bayesian Online Change‑Point Detection (Gaussian observation model) on the same preprocessed series and output their detected change weeks. *(See US-2)*
- **FR-006**: System MUST generate a performance report containing (a) detection delay (weeks), (b) precision, (c) recall, and (d) false‑positive rate, evaluated against an independently compiled ground‑truth list of outbreak weeks (±2‑week matching tolerance). *(See US-1)*
- **FR-007**: System MUST conduct a sensitivity analysis by varying (i) kernel bandwidth (median heuristic vs. cross‑validated) and (ii) window length (8, 12, 16 weeks), and record the resulting metric changes. *(See US-3)*
- **FR-008**: System MUST ensure the entire pipeline executes on a CPU‑only environment (no GPU, CUDA, or large‑model dependencies) and completes within **30 minutes** on the GitHub Actions free‑tier runner. *(Assumption: compute feasibility)*
- **FR-009**: System MUST log all runtime parameters, random seeds, and version information to guarantee reproducibility. *(General reproducibility)*

### Key Entities

- **FluViewSeries**: Weekly ILI rates with attributes `week_id`, `ili_rate`, `log_ili`, `standardized_ili`.  
- **WindowPair**: Consecutive windows (`window_a`, `window_b`) each containing 12 (or 8/16) weekly observations.  
- **MMDResult**: Contains `mmd_stat`, `p_value`, `flagged` (boolean).  
- **BaselineResult**: Contains method identifier (`Pettitt`/`BOCPD`), detected change week, and statistic.  
- **GroundTruthEvent**: External outbreak week interval with attributes `start_week`, `end_week`, `event_name`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Precision of the MMD detector on the ground‑truth outbreak weeks is **≥ 0.80**. *(See US-1)*
- **SC-002**: False‑positive rate (proportion of flagged weeks outside any ground‑truth interval) is **≤ 0.05** as estimated via block‑bootstrap resampling. *(See US-1)*
- **SC-003**: Average detection delay for known events is **≤ 2 weeks**. *(See US-1)*
- **SC-004**: Pettitt and BOCPD detection delays are **not significantly shorter** than MMD’s (two‑sample t‑test, p > 0.05), confirming that the kernel method is at least as timely. *(See US-2)*
- **SC-005**: Variation in precision, recall, and detection delay across the bandwidth/window sensitivity grid is **≤ 10 %** of the baseline (12‑week, median‑heuristic) values, demonstrating robustness. *(See US-3)*

## Assumptions

- The FluView CSV contains weekly timestamps that align exactly with the external outbreak week intervals used for ground truth. **[NEEDS CLARIFICATION: does the FluView dataset contain week identifiers compatible with the compiled outbreak list?]**
- Ground‑truth outbreak weeks are available in a simple CSV format (`event_name,start_week,end_week`) and are independent of the ILI series. **[NEEDS CLARIFICATION: precise source and format of the ground‑truth list]**
- The chosen significance threshold (α = 0.01) is appropriate for the surveillance context; this is a conventional standard in epidemiological hypothesis testing.  
- Permutation‑based p‑value estimation with 1 000 permutations provides sufficiently accurate null approximations for the sample sizes involved.  
- No GPU or specialized hardware is required; all numerical operations (MMD, permutations, Pettitt, BOCPD) are performed with NumPy/SciPy on ≤ 7 GB RAM.  
- The pipeline will be executed on the GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h wall‑time).  
- Missing weeks are removed rather than imputed; analysts accept that this may slightly reduce effective sample size.  

---
