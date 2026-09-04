# Feature Specification: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

**Feature Branch**: `001-eva-predictive-power-hea`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Novel Composition Generation (Priority: P1)

The researcher needs to ingest existing High-Entropy Alloy (HEA) thermodynamic data from public repositories (Materials Project/AFLOW) and programmatically generate two distinct sets of compositions: (1) a "Hold-out Known" set (compositions present in the source APIs but excluded from training) to measure extrapolation error relative to the training manifold, and (2) a "True Novel" set (compositions returning "Not Found" on query to the source APIs) to measure uncertainty calibration.

**Why this priority**: Without a clean separation between training data and test candidates, and without a ground-truth subset to validate error metrics, the evaluation of extrapolative capability is impossible. This is the foundational step for the entire study.

**Independent Test**: Can be fully tested by verifying that the generated `heas_train.csv` contains only known entries, `holdout_known.csv` contains a measured number of unique composition hashes that exist in the source API but not in training, and `true_novel.csv` contains a measured number of unique composition hashes that return "Not Found" when queried against the source API.

**Acceptance Scenarios**:

1. **Given** the Materials Project and AFLOW APIs are accessible, **When** the script filters for 5+ element systems and exports to `heas_train.csv`, **Then** the resulting dataset contains only entries with valid formation energy and mixing enthalpy values.
2. **Given** a set of elemental combinations, **When** the script filters for combinations existing in the API but not in `heas_train.csv`, **Then** the resulting `holdout_known.csv` contains a measured number of entries with zero overlap with the training set.
3. **Given** a set of elemental combinations, **When** the script filters for combinations that return "Not Found" on query to both the training set and the source API, **Then** the resulting `true_novel.csv` contains a measured number of entries.
4. **Given** the `holdout_known.csv` and `true_novel.csv`, **When** a validation query is run against the source API for these specific hashes, **Then** the system confirms that `holdout_known` entries exist in the API (but not training) and `true_novel` entries return "Not Found".

---

### User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

The researcher needs to compute standard compositional descriptors (atomic radius, electronegativity, VEC, melting point) for all datasets and train Random Forest and Gradient Boosting models using 5-fold cross-validation to establish a baseline interpolation performance.

**Why this priority**: This establishes the "interpolation" baseline. If the models cannot learn the relationship within the known data, the extrapolation test is invalid. It also ensures the feature engineering pipeline is CPU-tractable.

**Independent Test**: Can be fully tested by running the training pipeline on a subset of data and verifying that the 5-fold cross-validation $R^2$ score is calculated and reported, and that the model artifacts (pickle files) are generated without GPU dependencies.

**Acceptance Scenarios**:

1. **Given** the `heas_train.csv` dataset, **When** the feature engineering script runs using `pymatgen`, **Then** the output dataset includes weighted mean and variance columns for atomic radius, electronegativity, VEC, and melting point.
2. **Given** the feature-engineered training data, **When** the `RandomForestRegressor` and `GradientBoostingRegressor` are trained with 5-fold cross-validation, **Then** the mean $R^2$ score for the interpolation task is calculated and reported.
3. **Given** the training environment, **When** the model training executes, **Then** the process completes within the GitHub Actions time limit using only CPU resources (no CUDA/GPU errors).

---

### User Story 3 - Extrapolation Evaluation and Uncertainty Analysis (Priority: P3)

The researcher needs to apply the trained models to the "Hold-out Known" set to calculate extrapolation error ($R^2$) relative to the training manifold and to the "True Novel" set to analyze prediction uncertainty (SHAP/ensemble variance) as a proxy for reliability in unexplored chemical spaces. For the "True Novel" set, the evaluation is limited to uncertainty analysis unless independent ground truth is generated.

**Why this priority**: This directly addresses the research question regarding the limits of descriptor-based prediction. It validates the model's ability to detect its own uncertainty when ground truth is unavailable.

**Independent Test**: Can be fully tested by comparing the model's $R^2$ on the "Hold-out Known" set against the training set (if ground truth exists) and by verifying that uncertainty metrics (variance) correlate with the distance of "True Novel" compositions from the training convex hull.

**Acceptance Scenarios**:

1. **Given** the trained models and `holdout_known.csv`, **When** predictions are generated, **Then** the $R^2$ score for the hold-out set is calculated and compared to the training $R^2$.
2. **Given** the trained models and `true_novel.csv`, **When** predictions are generated, **Then** the system calculates ensemble variance and computes the distance of each composition from the training convex hull.
3. **Given** the results, **When** the final report is generated, **Then** it includes a CSV of the top novel candidates ranked by lowest prediction uncertainty and a statistical summary of the accuracy degradation (if ground truth exists) or uncertainty correlation (if ground truth is absent).

---

### Edge Cases

- **What happens when** the Materials Project API rate-limits or times out during the bulk retrieval of measured novel candidates? The system must implement exponential backoff with a maximum of 3 retries before marking the batch as "partial failure" and logging the error.
- **How does system handle** the scenario where the generated "novel" composition accidentally matches a known entry due to a hash collision or API update? The system must perform a final strict composition string comparison (not just hash) against the training set before finalizing the test set.
- **What happens when** the calculated descriptors (e.g., variance of electronegativity) result in zero or near-zero values for highly symmetric compositions, potentially causing division errors in derived features? The system must clamp these values to a minimum threshold of $1e-6$ to prevent numerical instability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve HEA thermodynamic data (formation energy, mixing enthalpy) from the Materials Project API and AFLOWlib, filtering strictly for 5+ element systems, and export to `heas_train.csv` (See US-1).
- **FR-002**: System MUST programmatically enumerate a measured number of "Hold-out Known" compositions (present in API, absent from training) and a measured number of "True Novel" compositions (returning "Not Found" on query to the API), verifying via composition hash and negative query response, and export to `holdout_known.csv` and `true_novel.csv` respectively (See US-1).
- **FR-003**: System MUST calculate weighted mean and variance descriptors for atomic radius, electronegativity, valence electron count (VEC), and melting point using `pymatgen` for all entries (See US-2).
- **FR-004**: System MUST train `RandomForestRegressor` and `GradientBoostingRegressor` models using 5-fold cross-validation to tune hyperparameters (max_depth, n_estimators) without requiring GPU acceleration (See US-2).
- **FR-005**: System MUST evaluate model performance on the "Hold-out Known" set by computing $R^2$ and MAE against ground truth (with explicit acknowledgment that ground truth is from the same source as selection), and on the "True Novel" set by calculating ensemble variance and distance from the training convex hull, explicitly limiting evaluation to uncertainty analysis unless independent ground truth is available (See US-3).
- **FR-006**: System MUST perform a permutation test or bootstrap test (instead of a standard t-test) to determine if the error distribution of the "Hold-out Known" set is significantly different from the interpolation error distribution, IF ground truth is available (See US-3).
- **FR-007**: System MUST perform a Spearman rank correlation test between prediction variance and distance from the convex hull for the "True Novel" set, IF ground truth is unavailable (See US-3).
- **FR-008**: System MUST generate a final report containing a CSV of the top novel candidates ranked by prediction reliability (lowest uncertainty) and a summary of accuracy degradation metrics (if available) or uncertainty correlation coefficients (See US-3).
- **FR-009**: System MUST attempt to validate the uncertainty metric on a small subset of "True Novel" candidates via DFT calculation (if computationally feasible within 6 hours) OR explicitly state in the report that the uncertainty metric is an unvalidated assumption (See US-3).

### Key Entities

- **TrainingSet**: A logical dataset containing known HEA compositions, elemental descriptors, and ground-truth thermodynamic properties (formation energy, mixing enthalpy), exported as `heas_train.csv`.
- **HoldoutKnown**: A logical dataset of unique 5-element compositions present in the source APIs but excluded from the TrainingSet, used to measure extrapolation error relative to the training manifold, exported as `holdout_known.csv`.
- **TrueNovel**: A logical dataset of unique 5-element compositions that return "Not Found" on query to the source APIs, used to measure uncertainty calibration, exported as `true_novel.csv`.
- **PredictedProperties**: The output of the ML models, including predicted formation energy and mixing enthalpy, along with uncertainty metrics (variance/SHAP).
- **PerformanceMetrics**: Aggregated statistics ($R^2$, MAE, p-values from permutation tests, Spearman correlation) comparing interpolation vs. extrapolation performance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The interpolation $R^2$ score on the training set (via 5-fold CV) is measured and reported; the value is compared against the hypothesis of a high threshold (See US-2) [FR-004].
- **SC-002**: The extrapolation $R^2$ score on the "Hold-out Known" set is measured and reported; if ground truth is unavailable for the "True Novel" set, the correlation between ensemble variance and distance from the convex hull is measured and reported (See US-3) [FR-005].
- **SC-003**: The statistical significance of the error degradation is measured by a p-value from a permutation test; the result is reported and interpreted, with a check for ground truth availability (See US-3) [FR-006].
- **SC-004**: The computational feasibility is measured by the total execution time of the pipeline on a CPU-only runner, which must be $\le 6$ hours with $\le 7$ GB RAM usage (See US-2) [FR-004, FR-005].
- **SC-005**: The reliability metric validity is measured by the ability to rank the top 100 "True Novel" candidates by uncertainty and reporting the variance distribution relative to the training set's lower percentile (See US-3) [FR-007, FR-008].

## Assumptions

- The Materials Project and AFLOWlib APIs provide sufficient coverage of 5+ element HEA systems to train a robust model, and their data formats remain stable during the retrieval window.
- The study distinguishes between "unseen in training" (Hold-out Known) and "unmeasured in nature" (True Novel). The "Hold-out Known" set allows for direct error measurement ($R^2$) relative to the training manifold, while the "True Novel" set allows for uncertainty calibration analysis. "True Novel" is defined as unindexed in the queried databases (MP/AFLOW), not necessarily uncharacterized globally.
- Standard compositional descriptors (atomic radius, electronegativity, VEC) are sufficient to capture the majority of variance in the training set, even if they fail in the extrapolation regime.
- The GitHub Actions free-tier runner (standard CPU, ample RAM) is sufficient to process the dataset and train the Random Forest/Gradient Boosting models within the 6-hour limit, as these are CPU-tractable methods.
- The `pymatgen` library is available and correctly installed in the CI environment to calculate the required compositional descriptors.
- A Spearman correlation coefficient $\rho > 0.5$ between variance and distance from the convex hull is expected for the "True Novel" set, indicating that the model correctly identifies its own uncertainty in unexplored regions, though this is a hypothesis to be tested, not a pass/fail criterion.