# Feature Specification: Assessing the Impact of Data Heterogeneity on Meta-Analysis Results

**Feature Branch**: `001-assess-heterogeneity-impact`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Assessing the Impact of Data Heterogeneity on Meta-Analysis Results"

## User Scenarios & Testing

### User Story 1 - Simulation Engine Execution (Priority: P1)

**Journey**: A researcher needs to generate synthetic meta-analysis datasets with controlled levels of between-study variance ($\tau^2$) to test statistical methods under known ground truths. The system must accept a base dataset (e.g., from Cochrane Reviews) and perturb it to varying heterogeneity levels (including baseline and elevated magnitudes) for a sufficient number of replicates per level, ensuring the process completes within the 6-hour CI limit.

**Why this priority**: Without the ability to generate controlled, reproducible data with known heterogeneity parameters, the core research question (relationship between heterogeneity and estimator performance) cannot be answered. This is the foundational capability.

**Independent Test**: The system is tested by running the simulation script with a fixed seed and a small subset of heterogeneity levels (e.g., $\tau^2 \in \{0, 0.1\}$) and 10 replicates. The output JSON must contain the injected $\tau^2$ values and the generated effect sizes, and the process must exit with status code 0 within 10 minutes.

**Acceptance Scenarios**:

1. **Given** a valid Cochrane meta-analysis dataset with study-level effect sizes and standard errors, **When** the simulation engine is invoked with $\tau^2 = 0.5$ and 500 replicates, **Then** the system generates 500 synthetic datasets where the empirical between-study variance approximates 0.5, and the process completes without memory overflow.
2. **Given** a dataset with $N=20$ studies, **When** the simulation is run with $\tau^2 = 2.0$, **Then** the generated effect sizes exhibit a wider distribution consistent with the high heterogeneity parameter, and the standard error of the pooled estimate increases relative to the $\tau^2 = 0$ baseline.
3. **Given** the GitHub Actions runner environment (2 CPU, 7GB RAM), **When** the full simulation (5 levels $\times$ 500 replicates) is executed, **Then** the job completes within 360 minutes (6 hours) and utilizes less than 6GB of RAM.

---

### User Story 2 - Estimator Application and Metric Calculation (Priority: P2)

**Journey**: A researcher needs to apply standard meta-analysis methods (Fixed-Effects, Random-Effects with DerSimonian-Laird and REML) to the simulated datasets and calculate performance metrics (bias and coverage) to evaluate estimator reliability.

**Why this priority**: Generating data is insufficient; the value lies in applying the methods and quantifying their failure modes (bias/coverage) relative to the ground truth.

**Independent Test**: The system is tested by processing a pre-generated small set of simulated datasets. The output must include the calculated pooled effect size, the corresponding confidence interval, and a flag indicating whether the true effect (known from simulation) falls within the interval.

**Acceptance Scenarios**:

1. **Given** a set of 500 simulated datasets with a known true effect size of 0.5, **When** the Random-Effects (DerSimonian-Laird) estimator is applied, **Then** the system calculates the pooled estimate and 95% CI for each, and correctly flags the proportion of CIs containing 0.5 (coverage).
2. **Given** the same 500 datasets, **When** the Fixed-Effects estimator is applied, **Then** the system calculates the pooled estimate and CI, and the resulting bias (pooled estimate - 0.5) is recorded for each replicate.
3. **Given** a simulation run where $\tau^2$ is set to 0, **When** the Fixed-Effects model is applied, **Then** the coverage probability must be statistically indistinguishable from 95% (within Monte Carlo error defined as $\pm 1.5\%$ at 95% confidence, calculated as $1.96 \times \sqrt{0.95 \times 0.05 / 500}$), confirming the baseline validity of the implementation. (See US-2)

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Journey**: A researcher needs to aggregate the simulation results to perform statistical tests (exact binomial for coverage, Kruskal-Wallis/ANOVA for bias) and generate visualizations showing the degradation of accuracy and coverage as heterogeneity increases.

**Why this priority**: This transforms raw simulation data into interpretable scientific conclusions, addressing the "Expected Results" section of the idea.

**Independent Test**: The system is tested by running the analysis script on a CSV of pre-computed simulation results. The output must include a summary table of coverage rates per $\tau^2$ level and a plot file (PNG) showing coverage vs. heterogeneity.

**Acceptance Scenarios**:

1. **Given** a CSV file containing bias and coverage data for 500 replicates across 5 heterogeneity levels, **When** the analysis script is executed, **Then** it outputs a summary table showing the observed coverage rate for each $\tau^2$ level.
2. **Given** the summary table, **When** the exact binomial test for coverage deviation is performed against the nominal [deferred] level, **Then** the system reports the p-value indicating if the observed coverage significantly deviates from the target confidence level for each condition. (See US-3)
3. **Given** the bias data across $\tau^2$ levels, **When** a normality check is performed and the Kruskal-Wallis test (or ANOVA if normal) is applied, **Then** the system reports whether there is a statistically significant difference in mean bias across the different heterogeneity levels. (See US-3)

### Edge Cases

- **Zero Variance**: What happens when $\tau^2$ is set to exactly 0 (perfect homogeneity)? The Random-Effects estimator must converge to the Fixed-Effects result without numerical instability.
- **Convergence Failure**: How does the system handle REML estimation failures (e.g., negative variance estimates) in high-heterogeneity, low-sample scenarios? The system must log the failure, impute a minimal positive variance or skip the replicate, and record the event count.
- **Small Study Effects**: How does the system handle datasets with very few studies ($N < 5$)? The simulation must either exclude these or explicitly flag that coverage estimates may be unreliable due to insufficient degrees of freedom for the chi-square approximation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic meta-analysis datasets by perturbing between-study variance ($\tau^2$) at levels {0, 0.1, 0.5, 1.0, 2.0} based on input Cochrane data, producing ≥500 replicates per level. (See US-1)
- **FR-002**: System MUST implement Fixed-Effects, DerSimonian-Laird Random-Effects, and REML Random-Effects estimators using CPU-tractable algorithms (no GPU/CUDA). (See US-2)
- **FR-003**: System MUST calculate the bias (pooled estimate - true effect) and nominal confidence interval coverage for every simulation replicate. (See US-2)
- **FR-004**: System MUST perform an exact binomial test to compare observed coverage against the nominal [deferred] level for each $\tau^2$ condition. (See US-3)
- **FR-005**: System MUST generate a summary visualization (PNG) plotting coverage probability and mean bias as functions of the injected $\tau^2$ value. (See US-3)
- **FR-006**: System MUST handle REML convergence failures by logging the event and proceeding with a fallback variance estimate or exclusion, ensuring the total simulation does not crash. (See US-2)
- **FR-007**: System MUST apply a Bonferroni correction to the significance threshold (adjusted $\alpha = 0.05 / 5 = 0.01$) when performing multiple hypothesis tests across the 5 heterogeneity levels. (See US-3)
- **FR-008**: System MUST perform a Shapiro-Wilk test for normality on bias distributions; if $p < 0.05$, the system MUST use the Kruskal-Wallis test instead of ANOVA to compare bias across levels. (See US-3)

### Key Entities

- **SimulatedDataset**: Represents a single synthetic meta-analysis instance, containing study-level effect sizes, standard errors, and the injected true between-study variance ($\tau^2$).
- **EstimationResult**: Represents the output of a single estimation run, containing the pooled effect size, confidence interval bounds, heterogeneity statistics ($I^2$, $Q$), and a boolean flag for coverage success.
- **AggregatedMetric**: Represents the summary statistics for a specific $\tau^2$ level, containing mean bias, observed coverage rate, and p-values from statistical tests.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Coverage probability is measured against the nominal [deferred] level for each heterogeneity level ($\tau^2$), with deviations reported via exact binomial test p-values. (See US-3)
- **SC-002**: Estimator bias is measured against the known ground-truth effect size injected during simulation, aggregated as mean absolute bias across multiple replicates. (See US-2)
- **SC-003**: Computational feasibility is measured against the GitHub Actions free-tier constraints (≤6 hours runtime, ≤7GB RAM, CPU-only), with a pass/fail result based on job completion. (See US-1)
- **SC-004**: Methodological validity is measured by the presence of a sensitivity analysis sweeping the heterogeneity thresholds (e.g., $\tau^2 \in \{0.05, 0.1, 0.5\}$) and reporting the stability of coverage rates. (See US-3)
- **SC-005**: Inference framing is measured by the explicit labeling of results as "associational" in the final report when observational data sources are used, avoiding causal claims unless randomization is specified. (See US-3)

## Assumptions

- **Dataset Availability**: Publicly available Cochrane Review meta-analyses with sufficient study-level data (effect sizes, standard errors, sample sizes) exist and can be programmatically accessed or manually extracted for an initial set of meta-analyses.
- **Methodological Framing**: The study design is observational (simulation based on existing data structures); therefore, all findings regarding estimator performance are framed as associational relationships between heterogeneity magnitude and estimator reliability, not causal effects of heterogeneity on truth.
- **Computational Tractability**: The simulation of 500+ replicates across 5 heterogeneity levels using standard R/Python statistical libraries (e.g., `metafor`, `statsmodels`) will complete within 6 hours on a 2-core CPU without requiring GPU acceleration or 8-bit quantization.
- **Threshold Justification**: The selected heterogeneity levels ($\tau^2 \in \{0, 0.1, 0.5, 1.0, 2.0\}$) are based on community standards for low, moderate, and high heterogeneity in medical meta-analysis. To ensure scale independence, the simulation will normalize heterogeneity using the $I^2$ statistic alongside $\tau^2$ and will explicitly specify the effect size metric (e.g., Log Odds Ratio) used for the base data, ensuring results are generalizable. A sensitivity analysis will sweep these values to ensure results are not artifacts of specific cutoff choices.
- **Measurement Validity**: The Cochrane data used as the base for simulation represents valid, peer-reviewed effect size estimates, ensuring the "ground truth" for the simulation is grounded in real-world statistical properties.
- **Multiplicity Control**: Since multiple hypothesis tests (coverage at 5 levels, bias at 5 levels) are performed, a Bonferroni correction is applied to the significance thresholds to control family-wise error rate, as mandated by FR-007.