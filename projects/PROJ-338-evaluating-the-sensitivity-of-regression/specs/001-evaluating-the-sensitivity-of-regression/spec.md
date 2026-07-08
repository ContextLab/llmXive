# Feature Specification: Evaluating the Sensitivity of Regression Models to Outlier Removal Strategies

**Feature Branch**: `001-evaluating-the-sensitivity-of-regression-models`  
**Created**: 2026-06-27  
**Status**: Draft  
**Input**: User description: "Evaluating the Sensitivity of Regression Models to Outlier Removal Strategies"

## Verified Datasets

> To satisfy Constitution Principle II (Verified Accuracy) and ensure reproducibility, the pipeline MUST use a set of regression datasets from the UCI Machine Learning Repository. The target variable for each is explicitly specified. The list is hardcoded to ensure deterministic selection.
> **Note**: The dataset `boston_housing` has been replaced with `parkinsons_telemonitoring` due to ethical restrictions and unavailability in standard UCI mirrors. All datasets are verified to have continuous targets and sufficient sample size (n > 30).

| ID | Dataset Name | Target Variable | Notes |
| :--- | :--- | :--- | :--- |
| 1 | `california_housing` | `MedHouseVal` | Continuous housing values |
| 2 | `airfoil_self_noise` | `SoundPressureLevel` | Aerodynamic noise data |
| 3 | `wine_quality_red` | `quality` | Red wine physicochemical properties |
| 4 | `student_performance_math` | `G3` | Final grade in math |
| 5 | `student_performance_por` | `G3` | Final grade in Portuguese |
| 6 | `concrete_compressive_strength` | `Concrete compressive strength` | Material strength data |
| 7 | `yacht_hydrodynamics` | `hydrodynamic resistance` | Yacht design data |
| 8 | `energy_efficiency` | `Y1` (Cooling load) | Building energy data |
| 9 | `energy_efficiency` | `Y2` (Heating load) | Building energy data |
| 10 | `automobile_data` | `price` | Automobile characteristics |
| 11 | `parkinsons_telemonitoring` | `MDVP:Jitter(%)` | Parkinson's disease telemonitoring |
| 12 | `kin8nm` | `y` | Robot arm kinematics |
| 13 | `cpu_activity` | `class` (mapped to numeric) | CPU performance |
| 14 | `naval_propulsion` | `STF` | Propulsion plant data |
| 15 | `superconductivity` | `Tc` | Critical temperature |

*Note: If any dataset is unavailable or does not match the target type, the pipeline MUST log an error, skip that ID, and proceed with the remaining valid datasets. The minimum valid dataset count for the analysis is sufficient to ensure statistical power (n ≥ 10 valid datasets).*

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Pipeline Execution on Sample Dataset (Priority: P1)

A researcher needs to download a single UCI regression dataset, preprocess it, run an OLS regression on the raw data, and then re-run the regression after applying a standard IQR-based outlier removal strategy (using Union logic) to observe the immediate change in coefficients and p-values.

**Why this priority**: This is the Minimum Viable Product (MVP). Without the ability to fetch data, preprocess, and run the core comparison loop (Raw vs. IQR), no sensitivity analysis is possible. It validates the end-to-end data flow and basic statistical computation on CPU.

**Independent Test**: Can be fully tested by executing the pipeline on the "California Housing" dataset and verifying that a CSV report is generated containing baseline and post-IQR metrics.

**Acceptance Scenarios**:

1. **Given** the system has network access to the UCI repository, **When** the pipeline is triggered for "California Housing", **Then** the system downloads the dataset, handles missing values, and executes OLS regression on the raw data.
2. **Given** the raw regression is complete, **When** the system applies the 1.5×IQR rule to identify and remove outliers (using **Union logic**: remove row if outlier in ANY continuous feature), **Then** the system refits the OLS model and records the new coefficients and p-values.
3. **Given** both models are fitted, **When** the comparison logic runs, **Then** the system outputs a summary table showing the absolute difference in R², RMSE, and the delta in p-values for every coefficient.

---

### User Story 2 - Multi-Strategy Comparison and Significance Testing (Priority: P2)

A researcher needs to compare the stability of regression results across three distinct outlier removal strategies (IQR, Z-score, and Cook's Distance) on a batch of datasets. The analysis distinguishes between **Feature-Space Sensitivity** (IQR, Z-score) and **Influence-Based Sensitivity** (Cook's Distance). The primary analysis uses a Wilcoxon signed-rank test on the absolute coefficient deltas, stratified by dataset, to determine if the choice of strategy significantly alters statistical conclusions.

**Why this priority**: The core research question asks about the *sensitivity* across *different* strategies. This story extends the MVP to include the comparative analysis and the valid statistical test (Wilcoxon) required to answer the research question rigorously. The sample size of datasets is chosen to align with the upper bound of the research idea to maximize statistical power.

**Independent Test**: Can be tested by running the pipeline on the fixed set of 15 UCI datasets defined in the "Verified Datasets" section and verifying that the output includes a statistical significance report (Wilcoxon p-value) comparing the magnitude of coefficient changes between strategies.

**Acceptance Scenarios**:

1. **Given** the list of 15 valid UCI dataset identifiers from the "Verified Datasets" section, **When** the pipeline processes them, **Then** it applies IQR (1.5×IQR, **Union logic**), Z-score (|z|>3, **Union logic**), and Cook's Distance (>4/n) removal methods independently to each dataset.
2. **Given** the results for all three strategies are collected, **When** the analysis phase runs, **Then** the system calculates the absolute change in coefficients (delta) for each variable between the Raw model and each cleaned model.
3. **Given** the coefficient deltas are calculated, **When** the statistical test is executed, **Then** the system performs a **Wilcoxon signed-rank test** on the distribution of **absolute coefficient deltas**, **stratified by dataset**, to determine if the median delta differs significantly from zero (p<0.05) for each pairwise strategy comparison. The unit of analysis is **per-variable** coefficient deltas.
4. **Given** the test results, **When** the report is generated, **Then** it explicitly separates the findings for "Feature-Space Sensitivity" (IQR vs Z-score) and "Influence-Based Sensitivity" (Cook's vs Raw).

---

### User Story 3 - Visualization and Sensitivity Threshold Sweep (Priority: P3)

A researcher needs to visualize the divergence in coefficients via boxplots and verify the robustness of the "1.5×IQR" threshold by sweeping the multiplier over a finer range to see if the headline sensitivity rates change. The sweep uses the corrected **Union logic**.

**Why this priority**: Visualization is essential for interpreting the results, and the sensitivity sweep addresses the methodological requirement to justify thresholds and ensure findings are not artifacts of a specific arbitrary cutoff.

**Independent Test**: Can be tested by running the pipeline and verifying the generation of a PDF report containing boxplots of metric changes and a table showing sensitivity rates at IQR multipliers of 1.0, 1.25, 1.5, 1.75, and 2.0.

**Acceptance Scenarios**:

1. **Given** the multi-strategy results are available, **When** the visualization module runs, **Then** it generates a boxplot of R² and RMSE changes grouped by removal method.
2. **Given** the IQR analysis is complete, **When** the sensitivity sweep is triggered, **Then** the system re-runs the IQR removal with multipliers 1.0, 1.25, 1.5, 1.75, and 2.0 using **Union logic**.
3. **Given** the sweep results, **When** the summary is generated, **Then** it reports the median absolute coefficient delta for each multiplier, demonstrating the stability of the findings.

---

### Edge Cases

- **How does the system handle a dataset where outlier removal removes >50% of the rows?** The system must detect this condition, abort the refit for that specific strategy/dataset, and record the result as "Data Loss" rather than crashing.
- **What happens if a specific UCI dataset is temporarily unavailable?** The pipeline must retry the download 2 times with a 5-second backoff before marking the dataset as "Failed" and continuing to the next one, ensuring the overall batch process completes.
- **What happens if the remaining sample size after outlier removal is insufficient for OLS (n < k+1)?** The system must skip the VIF and coefficient calculation for that specific dataset/strategy, log a "Insufficient Data" warning, and proceed to the next iteration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download regression datasets from the UCI Machine Learning Repository using HTTP requests (GET) **only for the specific dataset IDs listed in the "Verified Datasets" section**, and MUST verify the URL against the primary source or the provided block before execution. (See US-1)
- **FR-002**: System MUST preprocess data by imputing missing values with the median for continuous features (coercing non-numeric placeholders like '?' to NaN first) and handling categorical variables via one-hot encoding. (See US-1)
- **FR-003**: System MUST fit an Ordinary Least Squares (OLS) regression model on the raw (unmodified) dataset and store coefficients, p-values, R², and RMSE. (See US-1)
- **FR-004a**: System MUST identify and remove outliers using **Union logic** (remove row if outlier in **ANY** continuous feature) for IQR (1.5×IQR rule) and Z-score (|z|>3) methods. This measures **Feature-Space Sensitivity**. (See US-2)
- **FR-004b**: System MUST identify and remove outliers using Cook's Distance (>4/n) to measure **Influence-Based Sensitivity**. This analysis must be reported separately from FR-004a. (See US-2)
- **FR-005**: System MUST perform a **Wilcoxon signed-rank test** on the distribution of **absolute coefficient deltas** between the Raw model and each cleaned model. The test MUST be **stratified by dataset** to account for within-dataset correlation (collinearity). The null hypothesis is that the median delta is zero. The unit of analysis is **per-variable** coefficient deltas. (See US-2)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the IQR multiplier over the set {1.0, 1.25, 1.5, 1.75, 2.0} using **Union logic** and report the variation in median coefficient delta. (See US-3)
- **FR-007**: System MUST generate a PDF report containing boxplots of metric changes by removal method and a summary table of sensitivity rates. (See US-3)
- **FR-011**: System MUST compute Variance Inflation Factors (VIF) for all predictors in every dataset **after** outlier removal but **before** final coefficient reporting. System MUST flag any variable with VIF > 5. This check is performed **per-variable** to align with the unit of analysis in FR-005. If the remaining sample size (n) is less than the number of predictors (k) + 1, the system MUST skip VIF calculation for that dataset/strategy and log "Insufficient Data". (See US-2)

### Non-Functional Requirements

- **NFR-001**: System MUST frame all reported findings as associational (observational) and explicitly avoid causal language regarding the effect of outliers on the underlying population relationship. (Global)

### Key Entities

- **Dataset**: Represents a UCI regression task with attributes: `name`, `url`, `raw_data`, `preprocessed_data`, `target_variable`.
- **RegressionResult**: Represents the output of an OLS fit with attributes: `coefficients`, `p_values`, `r_squared`, `rmse`, `strategy_used` (e.g., "Raw", "IQR", "Z-Score").
- **SensitivityReport**: Represents the comparative analysis with attributes: `dataset_name`, `metric_changes`, `wilcoxon_p_value`, `sweep_results`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of coefficient changes (absolute delta) is measured across the different removal methods (IQR, Z-score, Cook's) to assess sensitivity. (See FR-004a, FR-004b, FR-005)
- **SC-002**: The variation in the median coefficient delta is measured across the IQR multiplier sweep {1.0, 1.25, 1.5, 1.75, 2.0} to assess threshold sensitivity. (See FR-006)
- **SC-003**: The computational resource usage (CPU time and peak RAM) is measured against the free-tier CI limits (≤6 hours total, ≤7 GB RAM) to ensure feasibility. (See FR-001, FR-002)
- **SC-004**: The pipeline determinism is measured by re-running the analysis multiple times with distinct fixed random seeds and verifying that the **Wilcoxon p-value** and the **median coefficient delta distribution** remain stable across runs. (See FR-005)
- **SC-005**: The validity of the methodology is measured by the presence of a collinearity diagnostic report for any dataset where predictors are definitionally related, specifically requiring the report to flag **per-variable** VIF > 5. (See FR-011)

## Assumptions

- **Assumption about data source**: The UCI Machine Learning Repository datasets listed in the "Verified Datasets" section are accessible via standard HTTP GET requests without requiring API keys or complex authentication mechanisms.
- **Assumption about compute environment**: The analysis will run on a CPU-only environment with sufficient RAM (≥7 GB) to hold the largest UCI regression dataset in memory after preprocessing; no GPU acceleration is required or available.
- **Assumption about statistical validity**: The datasets selected from UCI contain sufficient sample sizes (n > 30) to justify the use of asymptotic p-values and the Wilcoxon signed-rank test. The stratified approach accounts for the non-independence of variables within datasets.
- **Assumption about outlier definition**: The "1.5×IQR" and "|z|>3" thresholds are treated as community-standard defaults for exploratory outlier removal. The sensitivity sweep (a range sufficient to demonstrate threshold stability) is sufficient to demonstrate threshold stability, assuming the data is approximately Gaussian or that the sweep captures non-Gaussian behavior.
- **Assumption about observational nature**: Since the data is observational and not randomized, the study assumes that any detected sensitivity reflects data cleaning artifacts rather than causal interventions, and the reporting will strictly adhere to associational framing.