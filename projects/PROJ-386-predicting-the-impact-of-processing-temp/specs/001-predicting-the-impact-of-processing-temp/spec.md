# Feature Specification: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-02  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and Variable Verification (Priority: P1)

As a materials scientist, I want the system to attempt to download, filter, and validate the availability of rolling temperature, alloy composition (wt%), and grain size data from public sources (Materials Project, OpenML, NOMAD, Citrination) so that I can proceed with analysis on a verified dataset or halt with a clear reason if data is missing.

**Why this priority**: Without a verified dataset containing all necessary variables (temperature, composition, grain size), no modeling or hypothesis testing can occur. This is the foundational step that determines project feasibility. The distinction between "missing data" (halt) and "null results" (valid outcome) is critical.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains non-empty columns for temperature, Mg/Si/Cu content, and grain size, OR that the system halts with a specific "Data Missing" error code if schema pre-checks fail or data is absent.

**Acceptance Scenarios**:

1. **Given** a public dataset URL, **When** the ingestion script runs, **Then** the system performs a schema pre-check; if the source (e.g., Materials Project) lacks 'rolling temperature' or 'grain size' fields, the system skips the source immediately without attempting download.
2. **Given** raw data with missing composition values, **When** the filtering logic runs, **Then** rows lacking explicit rolling temperature or grain size measurements are excluded, and the final dataset size is reported.
3. **Given** a dataset where a required variable (e.g., specific alloying element) is missing across ALL configured sources, **When** the validation check runs, **Then** the system halts with exit code 1 and outputs a structured JSON error object: `{"code": "E_DATA_MISSING", "missing_variables": ["temperature", "grain_size"], "failed_sources": ["Materials Project", "NOMAD"]}`.
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

### Edge Cases

- What happens when the dataset contains only pure aluminum entries (no alloying elements)? The system must flag this as insufficient data for interaction analysis and halt.
- How does the system handle collinearity between alloying elements (e.g., Mg and Si often co-vary in specific series)? The system must detect high correlation (>0.8) and report it as a descriptive joint relationship rather than independent effects.
- What happens if the GitHub Actions runner exceeds the 6-hour time limit during grid search? The system must implement a timeout mechanism and default to a reduced grid search range or a single-pass training run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST attempt to download and parse public datasets from Materials Project, OpenML, NOMAD, and Citrination. System MUST perform a schema pre-check to verify the presence of 'rolling temperature', 'full alloy composition (wt%)', and 'measured grain size'. If a source fails the pre-check, skip it immediately. If ALL sources fail or missing variables persist, System MUST halt with exit code 1 and output a structured JSON error object: `{"code": "E_DATA_MISSING", "missing_variables": ["<var1>", ...], "failed_sources": ["<src1>", ...]}` (See US-1).
- **FR-002**: System MUST generate interaction features (e.g., `Temperature × %Mg`, `Temperature × %Si`) and normalize all numeric features before model training (See US-2).
- **FR-003**: System MUST train a baseline linear regression model to quantify main effects of temperature and composition (See US-2).
- **FR-004**: System MUST train a Random Forest regressor with grid search (n_estimators: 50-100, max_depth: 5-10) to capture non-linear interaction effects. If the training process exceeds 4 hours, System MUST fallback to a single-pass training run with default parameters (n_estimators=100, max_depth=10). The fallback mechanism MUST be configured such that the total pipeline execution time (including fallback training and subsequent steps) is guaranteed to remain ≤ 5 hours on a 2-core runner (See US-3).
- **FR-005**: System MUST perform a sensitivity analysis on any decision thresholds (e.g., feature importance cutoffs) by sweeping values over {0.01, 0.05, 0.1} and reporting the variation in significant findings (See US-3).
- **FR-006**: System MUST detect predictor collinearity (correlation > 0.8). If the collinear pair corresponds to a known chemical coupling (e.g., Mg/Si in 6xxx series), System MUST report the combined feature importance for the coupled pair rather than suppressing the signal. For non-chemical collinearity, System MUST suppress independent coefficient interpretation and frame the relationship descriptively as a joint effect (See US-3).
- **FR-007**: System MUST execute the entire pipeline on a CPU-only environment. System MUST verify no GPU device is detected by `torch.cuda.is_available()` and that total execution time is ≤ 5 hours on a 2-core runner (See Assumptions).
- **FR-008**: System MUST perform a confounder analysis to assess the impact of unmeasured variables (e.g., strain rate, cooling rate) by reporting the R² of the model with and without known proxy variables. If no proxy variables are available in the dataset, System MUST report the confounder analysis result as "N/A" and skip the comparative R² calculation (See SC-006).

### Key Entities

- **AlloySample**: Represents a single rolling process entry containing attributes: `temperature`, `composition` (dict of element:wt%), `grain_size`, and `alloy_series`.
- **InteractionFeature**: Represents a derived variable combining temperature and a specific alloying element (e.g., `temp_mg_interaction`).
- **ModelArtifact**: Represents the trained model object, including hyperparameters, coefficients/feature importances, and performance metrics (R², MAE).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model R² score delta (Non-Linear vs. Linear) is measured against the baseline linear regression R². Success is defined as the system successfully calculating and reporting the R² delta value, regardless of the magnitude of improvement (See US-3, FR-004).
- **SC-002**: Sensitivity analysis results are measured against the stability of the top-5 significant interaction terms across the threshold sweep {0.01, 0.05, 0.1}. Success is defined as >80% stability in the top-5 terms, confirming model robustness (not physical reality) (See US-3).
- **SC-003**: Dataset variable completeness is measured against the requirement for temperature, composition, and grain size fields to ensure no critical variables are missing (See US-1).
- **SC-004**: Computational feasibility is measured against the 5-hour limit on a 2-core runner, explicitly including the fallback training path defined in FR-004. Success is defined as pipeline completion in ≤ 5 hours AND peak memory usage ≤ 6.5 GB (See Assumptions, FR-007).
- **SC-005**: Collinearity diagnostic output is measured against the correlation matrix to verify that no two predictors have a correlation coefficient > 0.8 without appropriate descriptive framing in the JSON report (See FR-006).
- **SC-006**: Confounder analysis output is measured against the availability of proxy variables. Success is defined as the system reporting either a JSON object containing R² values (with/without proxies) OR an explicit "N/A" status if proxies are missing (See FR-008).

## Assumptions

- **Assumption about data availability**: Public datasets (Materials Project, OpenML, NOMAD, Citrination) are the primary sources. Materials Project is primarily a crystallographic database and explicitly lacks 'rolling temperature' and 'grain size' process data for conventional rolling. The system is designed to skip such sources immediately via schema pre-check. If no source provides the required variables, the project halts with error code E_DATA_MISSING.
- **Assumption about compute environment**: The analysis will run on a GitHub Actions free-tier runner (limited CPU cores, limited RAM, no GPU). Therefore, all models must be CPU-tractable (e.g., scikit-learn Random Forest with modest depth) and cannot require CUDA, 8-bit quantization, or large-model inference.
- **Assumption about methodology**: The design is observational (no random assignment to temperature/composition); therefore, all findings regarding "impact" or "modulation" will be framed as associational relationships and predictive contributions, not causal effects.
- **Assumption about threshold justification**: Any decision cutoff introduced (e.g., feature importance threshold) will use a community-standard default (0.05) and will be accompanied by a sensitivity analysis sweeping over {0.01, 0.05, 0.1} to demonstrate robustness.
- **Assumption about measurement validity**: The grain size and composition values in the public datasets are treated as validated measurements from the source literature; no additional validation of the instruments is performed within this pipeline.
- **Assumption about confounding**: Unmeasured confounders (e.g., strain rate) may exist. FR-008 and SC-006 are designed to assess the impact of these confounders if proxies exist; however, the observational nature of the data and lack of proxies in public datasets may result in an "N/A" report, which is an acceptable outcome.