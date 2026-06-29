# Feature Specification: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

**Feature Branch**: `001-brain-network-tactile`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Data Pipeline and Variable Validation (Priority: P1)

The researcher loads the HCP dataset (or an alternative multimodal dataset) and validates that all required variables (resting-state fMRI connectivity measures and tactile discrimination behavioral scores) are present and properly formatted for analysis.

**Why this priority**: Without verified data availability, no downstream analysis can proceed. This is the foundational step that gates all subsequent work.

**Independent Test**: Can be fully tested by running the data validation script and receiving a pass/fail report on variable presence and data quality thresholds, without requiring any statistical analysis.

**Acceptance Scenarios**:

1. **Given** the primary dataset (HCP or alternative) is available, **When** the data validation script runs, **Then** it reports ≥ 95% of subjects have complete resting-state fMRI and tactile discrimination data
2. **Given** a subject record, **When** the script checks variable presence, **Then** it flags any missing values exceeding ≤ 5% of the total subject pool
3. **Given** the dataset metadata, **When** validation runs, **Then** it confirms subject count matches the dataset documentation (expected N≈1200±50 for HCP or N≈1000±100 for the alternative) and demographic distributions align with published cohort profiles

---

### User Story 2 - Network Dynamics Computation (Priority: P2)

The researcher computes both **static** brain network metrics (functional connectivity matrices, modularity, segregation) **and** **dynamic** network metrics (sliding‑window connectivity matrices and time‑varying modularity) from resting‑state fMRI data using CPU‑tractable methods.

**Why this priority**: These metrics constitute the primary predictor variables for the analysis. They must run within the 6‑hour GitHub Actions job constraint (≤3‑hour computation target + 3‑hour setup/teardown) and handle the data volume within 7 GB RAM (Target capacity with sufficient headroom).

**Independent Test**: Can be fully tested by computing all metrics on a sample subset (e.g., 50 subjects) and verifying that:
* all metrics are computed within ≤ 2 hours,
* Peak memory usage stays below a moderate, acceptable threshold.,
* dynamic metrics follow the expected O(n × w) scaling (n = subjects, w = window count).

**Acceptance Scenarios**:

1. **Given** resting‑state fMRI data for ≤ 100 subjects, **When** the network dynamics pipeline runs, **Then** it produces static connectivity matrices, modularity, segregation, **and** dynamic modularity time‑series within ≤ 3 hours
2. **Given** the network computation, **When** memory usage is monitored, **Then** Peak RAM usage remains comfortably below the allocated memory limit, with a modest headroom; the maximum permissible RAM is not exceeded.
3. **Given** multiple network metrics (static and dynamic), **When** collinearity diagnostics run, **Then** any VIF > 5.0 triggers a descriptive framing flag rather than independent effect claims
4. **Given** connectivity matrix computation, **When** scaling is tested, **Then** memory usage follows O(n²) scaling with subject count n, validated against theoretical expectation
5. **Given** dynamic community detection, **When** window parameters are set (window length = 60 s, step = 30 s), **Then** the resulting dynamic modularity series is saved for downstream analysis

---

### User Story 3 - Associational Correlation Analysis (Priority: P3)

The researcher runs correlational analyses between network dynamics metrics (both static and dynamic) and tactile discrimination scores, adjusting for known confounds and performing a priori power analysis.

**Why this priority**: This produces the headline research findings. It depends on US‑1 and US‑2 being complete but can be tested independently once those are done.

**Independent Test**: Can be fully tested by running the analysis on a held‑out validation subset and verifying that:
* multiple‑comparison corrections are applied,
* covariate adjustment (age, sex, head‑motion, scanner drift) is performed,
* a priori power analysis for Pearson correlation is reported,
* sensitivity sweeps are reported with correlation stability metrics.

**Acceptance Scenarios**:

1. **Given** network metrics and behavioral scores, **When** the correlation analysis runs, **Then** it applies family‑wise error correction (FDR q ≤ 0.05) for ≥ 3 hypothesis tests
2. **Given** any decision threshold (e.g., connectivity strength cutoff), **When** sensitivity analysis runs, **Then** it sweeps the threshold over ≥ 3 values (e.g., {0.01, 0.05, 0.1}) and reports rate variation with correlation‑coefficient stability measurement
3. **Given** the analysis includes covariates (age, sex, mean framewise displacement, scanner ID), **When** adjusted partial correlations are computed, **Then** the output reports both raw and covariate‑adjusted effect sizes
4. **Given** high collinearity detected (VIF > 5.0), **When** effect‑size comparison runs, **Then** it reports the change in correlation coefficient when high‑VIF predictors are removed
5. **Given** the a priori power analysis (expected effect size r = 0.20, α = 0.05, target power = 0.80), **When** the available sample size N < required ≈ the target sample size., **Then** the system flags the study as under‑powered and includes the power estimate in the report

---

### Edge Cases

- What happens when HCP dataset lacks tactile discrimination behavioral measures? → System validates dataset against HCP documentation; if tactile measures absent, it HALTS analysis and outputs: `Dataset validation failed: Standard HCP Young Adult dataset does NOT include tactile discrimination measures. Resolution required before proceeding: (1) Switch to an alternative dataset that contains both fMRI and tactile measures (e.g., ABCD Study, a large sample of subjects, validated tactile instrument per FR‑013), OR (2) Add tactile measurement protocol to a custom study (2‑point discrimination threshold, n ≥ 50 subjects, validated instrument per FR‑007). Analysis cannot proceed without both data modalities.`
- How does system handle subjects with > 10% missing fMRI data? → Excludes subject from analysis and logs exclusion count (target: ≤ 5% of total sample)
- What happens when network metric collinearity (VIF > 5.0) is detected? → Frames relationship descriptively and adds collinearity diagnostic to output
- How does system handle power limitation for small sample sizes? → Reports statistical power estimate (using CorrelationPower) and marks effect‑size confidence intervals as `[deferred]` if power < 0.80

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST attempt to load HCP resting‑state fMRI data and, **if available**, tactile discrimination behavioral data; if tactile data are absent, the system MUST halt analysis and report the absence per FR‑009 (or switch to an alternative dataset as described in FR‑013) (See US‑1)
- **FR-002**: System MUST compute **static** functional connectivity matrices and graph‑theoretic metrics (modularity, segregation) **and** **dynamic** connectivity matrices (sliding‑window length = 60 s, step = 30 s) and dynamic modularity time‑series using CPU‑only methods within ≤ 3 hours for ≤ 100 subjects (See US‑2)
- **FR-003**: System MUST apply multiple‑comparison correction (FDR q ≤ 0.05 per Benjamini‑Hochberg 1995 convention) for ≥ 3 hypothesis tests (See US‑3)
- **FR-004**: System MUST frame all findings as associational (not causal); output text must contain association‑related terms ("correlation", "association", "relationship") and must NOT contain causal language ("causes", "effect", "determines") (See US‑3)
- **FR-005**: System MUST run collinearity diagnostics (VIF) on network predictors and flag VIF > 5.0 (per Field 2013 convention) for descriptive framing (See US‑2)
- **FR-006**: System MUST perform sensitivity analysis on any decision threshold, sweeping ≥ 3 values (e.g., {0.01, 0.05, 0.1}) and reporting rate variation with correlation stability measurement (See US‑3)
- **FR-007**: System MUST use validated tactile discrimination instruments with citable validation study; output must include DOI/URL of validation source (e.g., two‑point discrimination threshold with published norms from Weinstein, DOI:10.1016/j.neuropsychologia.2011.04.012) (See US‑1)
- **FR-008**: System MUST report sample‑size/power estimates **a priori** for Pearson correlation using expected effect size r = 0.20, α = 0.05, target power = 0.80 (Cohen 1992). If the available N is below the required ≈ the required number of participants, the system MUST flag the study as under‑powered and mark effect‑size confidence intervals as `[deferred]` (See US‑3)
- **FR-009**: System MUST validate dataset availability before analysis; if tactile discrimination measures absent from HCP, analysis halts with explicit resolution path (see US‑1)
- **FR-010**: System MUST compute dynamic network metrics (sliding‑window connectivity, dynamic modularity) and store them for downstream analysis (See US‑2)
- **FR-011**: System MUST perform the a priori power analysis described in FR‑008 and include the required sample size in the final report (See US‑3)
- **FR-012**: System MUST adjust correlation analyses for known confounds (age, sex, mean framewise displacement, scanner ID) using partial correlation or multiple linear regression, and report both raw and adjusted effect sizes (See US‑3)
- **FR-013**: System MUST support loading an alternative multimodal dataset (e.g., ABCD Study) that contains both resting‑state fMRI and tactile discrimination scores; if HCP lacks tactile data, the pipeline automatically switches to the alternative dataset (See US‑1)

### Key Entities *(include if feature involves data)*

- **Subject**: Individual participant with unique ID, containing fMRI scans and behavioral scores
- **Network Metric**: Computed measure (e.g., modularity Q, segregation index, dynamic modularity time‑series) derived from connectivity matrix
- **Behavioral Score**: Tactile discrimination performance metric (e.g., threshold in mm, accuracy %)

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data completeness rate is measured against HCP (or alternative) dataset documentation (expected N≈1200±50 for HCP or N≈1000±100 for alternative) to validate data integrity (See US‑1)
- **SC-002**: Network computation runtime is measured against ≤ 3‑hour constraint for ≤ 100 subjects AND validated via convergence tests against known benchmark connectivity values (See US‑2)
- **SC-003**: Memory usage is measured against 6.5 GB peak RAM limit AND validated via profiling against expected O(n²) scaling with subject count (See US‑2)
- **SC-004**: Multiple‑comparison correction is measured against requirement for ≥ 3 hypothesis tests with family‑wise error control; output must include adjusted p‑values or q‑values using FDR (q ≤ 0.05) or Bonferroni correction, with correction method explicitly named in results (See US‑3)
- **SC-005**: Sensitivity analysis coverage is measured against ≥ 3 threshold values swept WITH correlation coefficient stability measurement reported across threshold range (See US‑3)
- **SC-006**: Collinearity diagnostic completeness is measured against VIF > 5.0 flagging requirement WITH effect‑size comparison metric (correlation coefficient change when high‑VIF predictors removed) (See US‑2)
- **SC-007**: Power/sample‑size estimation completeness is measured against a priori power target (power ≥ 0.80) and reports required N; if available N < required, under‑power flag is emitted (See US‑3)
- **SC-008**: Dynamic network metrics runtime is measured against ≤ 3‑hour constraint and memory ≤ 6.5 GB; scaling validation against sliding‑window parameters is included (See US‑2)
- **SC-009**: Adjusted correlation results (controlling for age, sex, motion, scanner) are reported alongside raw correlations; both sets must include confidence intervals (See US‑3)

## Assumptions

- **Data Availability**: Standard HCP Young Adult dataset does NOT include tactile discrimination behavioral measures; therefore the pipeline will automatically switch to an alternative multimodal dataset (e.g., the Adolescent Brain Cognitive Development (ABCD) Study, which provides both resting‑state fMRI and standardized tactile discrimination scores) **or** require a custom dataset with both modalities (n ≥ 100 subjects, validated instrument per FR‑007). System halts analysis if neither option is feasible within compute constraints.
- **Compute Constraints**: ≤ 3‑hour computation target + 3‑hour setup/teardown = 6‑hour GitHub Actions job limit (industry standard for reproducible CI/CD research pipelines)
- **Memory Constraints**: 7 GB maximum with 6.5 GB target + 0.5 GB headroom (standard GitHub Actions runner allocation)
- **Tactile Instrument**: Tactile discrimination will use a validated two‑point discrimination instrument (Weinstein, 1968) with DOI 10.1016/j.neuropsychologia.2011.04.012 cited in output; if idea does not specify, community‑standard defaults are used.
- **Statistical Methods**: All methods are CPU‑tractable (scikit‑learn, classical statistics, closed‑form computation); no GPU, CUDA, or large‑model training required
- **Power Analysis**: A priori power analysis for Pearson correlation uses expected effect size r = 0.20, α = 0.05, target power = 0.80 (Cohen 1992). If achieved power < 0.80, effect‑size confidence intervals are marked `[deferred]`.
- **Multiple Comparisons**: FDR (q ≤ 0.05) per Benjamini‑Hochberg 1995 convention is the default; Bonferroni may be used as an alternative if stricter family‑wise error control is desired.
- **Collinearity Assessment**: Network metric collinearity assessed using VIF; VIF > 5.0 per Field 2013 convention triggers descriptive framing rather than independent effect claims.
- **Job Time Limit**: Total GitHub Actions job time ≤ 6 hours (industry standard); if exceeded, job fails and requires dataset/method scoping adjustment
- **Contract Files**: The `contracts/` directory will include a `network_metric.schema.yaml` matching the schema described in `data-model.md` (to be added in a subsequent implementation sprint).
