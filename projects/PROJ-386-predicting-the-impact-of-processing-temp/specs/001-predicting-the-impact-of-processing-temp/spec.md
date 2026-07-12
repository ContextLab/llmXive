# Feature Specification: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-02  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and Variable Verification (Priority: P1)

As a materials scientist, I want the system to download, filter, and validate the availability of rolling temperature, alloy composition (wt%), and grain size data from public sources (OpenML, NOMAD, Citrination) so that I can proceed with analysis on a verified dataset or halt with a clear reason if data is missing.

**Why this priority**: Without a verified dataset containing all necessary variables (temperature, composition, grain size), no modeling or hypothesis testing can occur. This is the foundational step that determines project feasibility. The distinction between "missing data" (halt) and "null results" (valid outcome) is critical.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains non-empty columns for temperature, Mg/Si/Cu content, and grain size, OR that the system halts with a specific "Data Missing" error code if schema pre-checks fail or data is absent.

**Acceptance Scenarios**:

1. **Given** a public dataset URL, **When** the ingestion script runs, **Then** the system performs a schema pre-check; if the source (e.g., Materials Project) lacks 'rolling temperature' or 'grain size' fields, the system skips the source immediately without attempting download.
2. **Given** raw data with missing composition values, **When** the filtering logic runs, **Then** rows lacking explicit rolling temperature or grain size measurements are excluded, and the final dataset size is reported.
3. **Given** a dataset where a required variable (e.g., specific alloying element) is missing across ALL configured sources, **When** the validation check runs, **Then** the system halts with Exit Code 1 and logs the message: "Critical variables missing from all sources: [list of missing variables]".
4. **Given** a valid dataset with all variables present but low correlation, **When** the analysis runs, **Then** the system proceeds to modeling and reports a null result (e.g., R² < 0.6) as a valid scientific outcome, NOT a project failure.

---

### User Story 2 - Interaction Feature Engineering and Baseline Modeling (Priority: P2)

As a researcher, I want the system to generate interaction features (e.g., Temperature × %Mg) and train a baseline linear regression model to establish the main effects before attempting complex non-linear modeling.

**Why this priority**: Establishing a baseline linear model is essential to determine if interaction terms are necessary. It provides a technology-agnostic reference point for evaluating the added value of complex models.

**Independent Test**: Can be fully tested by running the feature engineering and baseline training pipeline on a small sample (e.g., 100 rows) and verifying that the output includes a model object with coefficients for main effects and interaction terms.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with temperature and composition columns, **When** the feature engineering step runs, **Then** new columns for interaction terms (Temperature × Element) are created and appended to the dataset.
2. **Given** the training set, **When** the linear regression model is trained, **Then** the model outputs coefficients for temperature, composition, and interaction terms, and the R² score on the validation set is logged.
3. **Given** a scenario where interaction terms have near-zero coefficients, **When** the model evaluation runs, **Then** the system flags that the linear baseline suggests limited interaction effects, prompting a review of the non-linear model strategy.

---

### User Story 3 - Non-Linear Interaction Modeling and Sensitivity Analysis (Priority: P3)

As a process engineer, I want the system to train a Random Forest model to capture non-linear interaction effects and perform a sensitivity analysis on the decision thresholds to ensure robustness.

**Why this priority**: This addresses the core research gap regarding non-linear modulation of grain growth. The sensitivity analysis ensures that any identified thresholds are not artifacts of arbitrary cutoff choices. Note: Results indicate statistical correlation, not physical causation.

**Independent Test**: Can be fully tested by running the Random Forest training with grid search, evaluating the R² score, and generating a sensitivity report that varies a key threshold (e.g., feature importance cutoff) and reports stability of results.

**Acceptance Scenarios**:

1. **Given** the engineered dataset, **When** the Random Forest model is trained with grid search, **Then** the best hyperparameters (n_estimators, max_depth) are selected based on validation R², and the test set R² is recorded.
2. **Given** a selected decision threshold for feature importance (e.g., 0.05), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over {0.01, 0.05, 0.1} and reports how the set of "significant" interaction terms changes.
3. **Given** the final model, **When** partial dependence plots are generated, **Then** the system visualizes how grain size deviates from the baseline at different temperatures for specific alloy compositions.

---

### User Story 4 - Environment Verification and Compute Constraint Enforcement (Priority: P0)

As a DevOps engineer, I want the system to verify the execution environment (runner type, CPU availability) and enforce hard timeout limits so that the pipeline does not exceed the GitHub Actions free-tier constraints.

**Why this priority**: The project relies on a specific free-tier compute budget. Without explicit verification and hard limits, the pipeline may fail unpredictably or incur costs. This is a pre-requisite for all other stories.

**Independent Test**: Can be fully tested by running the environment check script on a local machine and verifying it reports the correct runner type and that a simulated long-running process is terminated at the 5-hour mark.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the pipeline starts, **Then** the system verifies the runner is 'ubuntu-latest' (or compatible) and logs the detected CPU count.
2. **Given** a running process, **When** the elapsed time reaches 5 hours, **Then** the system gracefully terminates the process and logs a "Timeout Enforced" message.

---

### Edge Cases

- What happens when the dataset contains only pure aluminum entries (no alloying elements)? The system must flag this as insufficient data for interaction analysis and halt.
- How does the system handle collinearity between alloying elements (e.g., Mg and Si often co-vary in specific series)? The system must detect high correlation (>0.8) and report it as a descriptive joint relationship rather than independent effects.
- What happens if the GitHub Actions runner exceeds the 6-hour time limit during grid search? The system must implement a timeout mechanism and default to a reduced grid search range or a single-pass training run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST perform a schema pre-check on public datasets (OpenML, NOMAD, Citrination) to verify the presence of 'rolling temperature', 'full alloy composition (wt%)', and 'measured grain size'. If a source (including Materials Project) fails the pre-check, skip it immediately without attempting download. If ALL sources fail or missing variables persist, System MUST halt with Exit Code 1 and log the message: "Critical variables missing from all sources: [list of missing variables]" (See US-1).
- **FR-002**: System MUST generate interaction features (e.g., `Temperature × %Mg`, `Temperature × %Si`) and normalize all numeric features before model training (See US-2).
- **FR-003**: System MUST train a baseline linear regression model to quantify main effects of temperature and composition (See US-2).
- **FR-004**: System MUST train a Random Forest regressor with grid search (n_estimators: 50-200, max_depth: 5-20) to capture non-linear interaction effects. If the training process exceeds 4 hours, System MUST fallback to a single-pass training run with default parameters (n_estimators=100, max_depth=10) to ensure completion within the 6-hour limit (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on any decision thresholds (e.g., feature importance cutoffs) by sweeping values over {0.01, 0.05, 0.1} and reporting the variation in significant findings (See US-3).
- **FR-006**: System MUST detect predictor collinearity (correlation > 0.8) and output a JSON report flagging these pairs. System MUST suppress independent coefficient interpretation for flagged pairs and frame the relationship descriptively as a joint effect (See US-3).
- **FR-007**: System MUST execute the entire pipeline on an 'ubuntu-latest' runner. System MUST verify no GPU device is detected and enforce a hard timeout of GITHUB_ACTIONS_TIMEOUT=5h. If the process exceeds 5 hours, it MUST terminate gracefully (See US-4).
- **FR-008**: System MUST perform a confounder sensitivity analysis by attempting to add available proxy variables (e.g., strain rate, cooling rate) to the model. If proxy variables are present in the dataset, System MUST report the R² change. If no proxy variables are available, System MUST log "No proxy variables available for confounder analysis" and proceed with a caveat in the final report (See US-3).

### Key Entities

- **AlloySample**: Represents a single rolling process entry containing attributes: `temperature`, `composition` (dict of element:wt%), `grain_size`, and `alloy_series`.
- **InteractionFeature**: Represents a derived variable combining temperature and a specific alloying element (e.g., `temp_mg_interaction`).
- **ModelArtifact**: Represents the trained model object, including hyperparameters, coefficients/feature importances, and performance metrics (R², MAE).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model R² score on the held-out test set is measured against the baseline linear regression R². Success is defined as an R² improvement that is statistically significant (p < 0.05 via permutation test) AND (absolute improvement > 0.05 OR relative improvement > 10%), indicating a strong predictive association (not necessarily causal) from interaction terms (See US-3, FR-008).
- **SC-002**: Sensitivity analysis results are measured against the stability of the top-5 significant interaction terms across the threshold sweep {0.01, 0.05, 0.1}. Success is defined as >80% stability in the top-5 terms, confirming model robustness (not physical reality) (See US-3).
- **SC-003**: Dataset variable completeness is measured against the requirement for temperature, composition, and grain size fields to ensure no critical variables are missing (See US-1).
- **SC-004**: Computational feasibility is measured against the standard GitHub Actions free-tier time limit and 7 GB RAM constraint. Success is defined as pipeline completion in ≤ 5 hours (measured via `time -v` stderr parsing or `memory_profiler` peak RSS) AND peak memory usage ≤ 6.5 GB (See Assumption about compute environment, FR-007).
- **SC-005**: Collinearity diagnostic output is measured against the correlation matrix to verify that no two predictors have a correlation coefficient > 0.8 without appropriate descriptive framing in the JSON report (See FR-006).
- **SC-006**: Confounder analysis output is measured against the availability of proxy variables. Success is defined as the system reporting either a JSON object containing R² values (with/without proxies) OR an explicit "N/A" status if proxies are missing (See FR-008).

## Assumptions

- **Assumption about data availability**: Public datasets (OpenML, NOMAD, Citrination) are the primary sources. Materials Project is primarily a crystallographic database and likely lacks 'rolling temperature' and 'grain size' process data. The system is designed to skip such sources immediately via schema pre-check. If no source provides the required variables, the project halts.
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (ubuntu-latest, with standard memory resources, no GPU). Therefore, all models must be CPU-tractable (e.g., scikit-learn Random Forest with modest depth) and cannot require CUDA, 8-bit quantization, or large-model inference.
- **Assumption about methodology**: The design is observational (no random assignment to temperature/composition); therefore, all findings regarding "impact" or "modulation" will be framed as associational relationships and predictive contributions, not causal effects.
- **Assumption about threshold justification**: Any decision cutoff introduced (e.g., feature importance threshold) will use a community-standard default (0.05) and will be accompanied by a sensitivity analysis sweeping over {0.01, 0.05, 0.1} to demonstrate robustness.
- **Assumption about measurement validity**: The grain size and composition values in the public datasets are treated as validated measurements from the source literature; no additional validation of the instruments is performed within this pipeline.
- **Assumption about confounding**: Unmeasured confounders (e.g., strain rate) may exist. FR-008 and SC-006 are designed to assess the impact of these confounders if proxies exist; however, the observational nature of the data and lack of proxies in public datasets may result in an "N/A" report, which is an acceptable outcome.