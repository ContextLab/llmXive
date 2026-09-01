# Feature Specification: Machine Learning Prediction of Glass Transition Temperature from Composition

**Feature Branch**: `001-glass-transition-ml`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "Machine Learning Prediction of Glass Transition Temperature from Composition"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Compositional Featurization (Priority: P1)

The system must successfully ingest raw oxide glass composition data from the NIST repository and transform chemical formulas into a structured feature matrix containing network-former ratios, modifier content, and average electronegativity.

**Why this priority**: This is the foundational step; without a clean, featurized dataset, no modeling or analysis can occur. It directly addresses the core methodology of converting stoichiometry to descriptors.

**Independent Test**: The pipeline can be executed end-to-end on a sample CSV file, producing a `.csv` output with the specified feature columns (e.g., `avg_electronegativity`, `network_modifier_ratio`) and no missing values in the target variable ($T_g$).

**Acceptance Scenarios**:

1. **Given** a raw CSV file from the NIST Materials Data Repository containing chemical formulas and $T_g$ values, **When** the preprocessing script is executed, **Then** the output file contains a row for each glass with calculated columns for atomic fractions of Si/B/P, Na/K/Ca, average electronegativity, and total valence electron count.
2. **Given** a chemical formula with ambiguous stoichiometry (e.g., missing elements or invalid syntax), **When** the parser processes the row, **Then** the row is flagged and excluded from the training set, and a log entry is generated detailing the specific parsing error.
3. **Given** a dataset where $T_g$ is missing for a specific entry, **When** the cleaning step runs, **Then** that entry is removed, and the final dataset size is reported as (Original Count - Removed Count).

---

### User Story 2 - Model Training and Baseline Comparison (Priority: P2)

The system must train interpretable tree-based models (Random Forest and Gradient Boosting) on the featurized data and compare their performance against a physics-based linear mixing rule baseline model to determine if composition alone adds predictive value beyond simple additive rules.

**Why this priority**: This validates the core research hypothesis: that composition has non-trivial information content regarding $T_g$ beyond linear mixing. It establishes the "predictive ceiling" for composition-only models against a scientifically meaningful baseline.

**Independent Test**: The training script executes within the CPU constraints, produces a model artifact, and outputs a report showing R², MAE, and RMSE for both the ML model and the linear-mixing baseline, along with a statistical significance test (paired t-test on MAE values from the 5 cross-validation folds).

**Acceptance Scenarios**:

1. **Given** the featurized training dataset, **When** the model training module runs with a fixed random seed, **Then** the system outputs a `model_performance.json` file containing R², MAE, and RMSE for the best-performing model and the linear-mixing baseline.
2. **Given** the 5 cross-validation folds, **When** the statistical comparison is performed, **Then** the system calculates a p-value comparing the MAE of the ML model against the linear-mixing baseline MAE values from the 5 folds, and reports whether the improvement is statistically significant (p < 0.05).
3. **Given** a dataset size that exceeds 7 GB RAM (if applicable), **When** the data loading step occurs, **Then** the system either samples the data to fit memory or raises a clear error indicating the dataset is too large for the current configuration.

---

### User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

The system must extract feature importances from the best model to identify key compositional drivers and perform a sensitivity analysis on the model's hyperparameters to ensure robustness.

**Why this priority**: This addresses the "interpretability" and "methodological soundness" requirements, ensuring the findings are not artifacts of a specific dataset split or hyperparameter choice.

**Independent Test**: The analysis script generates a ranking of features by importance and a sensitivity report showing how MAE/R² varies across a defined set of hyperparameter configurations.

**Acceptance Scenarios**:

1. **Given** the trained best-performing model, **When** the interpretability module runs, **Then** it outputs a sorted list of features (e.g., "Network Modifier Fraction") with their relative importance scores, identifying the top 5 drivers.
2. **Given** a set of hyperparameters (e.g., `n_estimators` ∈ {100, 300}, `max_depth` ∈ {10, 20}), **When** the sensitivity analysis is executed, **Then** the system reports the variation in MAE across these configurations, confirming that performance does not fluctuate wildly with minor parameter changes.
3. **Given** the top 3 most important features, **When** a compositional-aware permutation importance test is run, **Then** the system confirms that shuffling these features results in a significant drop in model performance (R² < 0.5 of original), validating their predictive utility while respecting the sum-to-one constraint.

### Edge Cases

- **What happens when the dataset contains a glass composition with elements not present in the periodic table data used by `matminer`?** The system must catch the `KeyError`, log the specific element, exclude the row, and continue processing without crashing.
- **How does the system handle a scenario where the NIST dataset is sparse or the downloaded file is corrupted?** The system must verify the file integrity (e.g., via checksum or row count validation) and fail gracefully with a specific error message if the data is unusable, rather than proceeding with empty or malformed data.
- **What if the dataset size is too small for a meaningful 5-fold cross-validation (e.g., < 30 samples)?** The system must detect this condition, reduce the number of folds to 3 or 2, and log a warning that the statistical power of the cross-validation is limited.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw oxide glass composition data from the NIST Materials Data Repository (CSV format) and parse chemical formulas into elemental atomic fractions using `pymatgen` (See US-1).
- **FR-002**: System MUST generate a feature matrix including network-former ratios (Si, B, P), modifier content (Na, K, Ca), average electronegativity, average atomic mass, and total valence electron count (See US-1).
- **FR-003**: System MUST split the dataset into an [deferred] training set and a [deferred] test set using a fixed random seed for reproducibility (See US-2).
- **FR-004**: System MUST train a `RandomForestRegressor` and a `GradientBoostingRegressor` using `scikit-learn` with a grid search over `n_estimators` ∈ {100, 300} and `max_depth` ∈ {10, 20}, selecting the model with the highest R² on the validation fold (See US-2).
- **FR-005**: System MUST compute R², MAE, and RMSE on the held-out test set. Additionally, the system MUST perform a paired t-test comparing the ML model's MAE against the linear-mixing baseline model's MAE using the MAE values obtained from the 5 cross-validation folds (See US-2).
- **FR-006**: System MUST extract and rank feature importances from the best-performing model and validate them using compositional-aware permutation importance that respects the sum-to-one constraint (See US-3).
- **FR-007**: System MUST perform a post-training robustness analysis sweeping the `n_estimators` and `max_depth` parameters over the defined grid and report the resulting variance in MAE to ensure stability (See US-3).
- **FR-008**: System MUST ensure all computations run within the GitHub Actions free-tier constraints (≤ 7 GB RAM, ≤ 6 hours, no GPU) by sampling data if necessary (See US-2).

### Key Entities

- **GlassSample**: Represents a single glass composition. Attributes: `formula` (string), `Tg` (float, Kelvin), `atomic_fractions` (dict), `descriptors` (dict of floats).
- **ModelResult**: Represents the outcome of a model training run. Attributes: `model_type` (string), `hyperparameters` (dict), `metrics` (dict: R², MAE, RMSE), `feature_importance` (list).
- **Dataset**: The aggregated collection of `GlassSample` objects. Attributes: `source` (string), `total_samples` (int), `train_size` (int), `test_size` (int).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The predictive power of composition-only models is measured against the linear-mixing baseline model, specifically quantifying the improvement in R² and reduction in MAE (See FR-005).
- **SC-002**: The statistical significance of the ML model's improvement over the linear-mixing baseline is measured against a p-value threshold of 0.05 using a paired t-test on MAE values from 5 cross-validation folds (See FR-005).
- **SC-003**: The robustness of the model performance is measured against the variance in MAE across the defined hyperparameter grid (n_estimators: 100/300, max_depth: 10/20), requiring the standard deviation of MAE to be ≤ 5% of the mean MAE (See FR-007).
- **SC-004**: The interpretability of the model is measured against the consistency of feature importance rankings between the standard importance metric and compositional-aware permutation importance, requiring a Spearman rank correlation ≥ 0.8 (See FR-006).
- **SC-005**: The computational feasibility is measured against the constraint that the entire pipeline must complete within 6 hours on a 2-core CPU runner without exceeding 7 GB RAM (See FR-008).

## Assumptions

- The NIST Materials Data Repository glass dataset is accessible via `wget` from its DOI URL and contains valid chemical formulas and $T_g$ values in a CSV format compatible with `pymatgen` parsing.
- The `matminer` library's `ElementProperty` featurizer provides the necessary descriptors (electronegativity, atomic mass, etc.) for all elements present in the oxide glass dataset without requiring custom periodic table extensions.
- The relationship between compositional descriptors and $T_g$ is non-linear and sufficiently captured by tree-based models (Random Forest/Gradient Boosting) without requiring deep learning architectures or GPU acceleration.
- The system attempts a 5-fold cross-validation split; if the dataset is too small to support 5 folds, the system automatically reduces the number of folds to 3 or 2 as a fallback strategy.
- The "network formers" and "modifiers" are strictly defined as Si, B, P and Na, K, Ca respectively for the purpose of feature engineering, consistent with standard oxide glass literature.
- The GitHub Actions free-tier runner provides a stable Linux environment with the necessary Python packages (`pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`) pre-installed or installable via `requirements.txt`.
- A linear mixing rule baseline (weighted average of constituent oxide Tg values) is scientifically valid and available for comparison against the ML model.