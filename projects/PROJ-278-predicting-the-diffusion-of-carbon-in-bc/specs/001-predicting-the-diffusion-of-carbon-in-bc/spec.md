# Feature Specification: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

**Feature Branch**: `001-predict-carbon-diffusion-bcc`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "Predicting the Diffusion of Carbon in BCC Metals from Compositional Data"

## User Scenarios & Testing

### User Story 1 - Construct and Validate Composition-Only Dataset (Priority: P1)

The researcher MUST be able to ingest raw diffusion data from NIST and Materials Project, filter for BCC structures, compute compositional descriptors (atomic radius, VEC, electronegativity), and log-transform diffusion coefficients into a clean, analysis-ready CSV.

**Why this priority**: Without a validated, microstructure-excluded dataset, no modeling can occur. This is the foundational data engineering step that isolates the specific scientific variable (composition) from the confounding variable (microstructure).

**Independent Test**: This story is complete when a `dataset_cleaned.csv` exists containing only BCC entries with computed descriptors, and a validation script confirms that no microstructural features (grain size, dislocation density) are present in the column list.

**Acceptance Scenarios**:

1. **Given** raw data files from NIST and Materials Project containing mixed crystal structures, **When** the preprocessing script filters for `structure == "BCC"` and removes entries with missing composition, **Then** the output dataset contains only BCC metal entries with valid atomic fractions.
2. **Given** a dataset with raw diffusion coefficients spanning orders of magnitude, **When** the script applies a base-10 log transformation to the target variable, **Then** the resulting `log_D` column has a reduced dynamic range suitable for linear regression without numerical overflow.
3. **Given** a list of input descriptors including atomic radius and valence electron count, **When** the script computes variance and spread metrics, **Then** the output includes `atomic_radius_variance`, `electronegativity_spread`, and `VEC` as distinct columns.

---

### User Story 2 - Train and Evaluate Composition-Only Regression Models (Priority: P2)

The researcher MUST be able to train Random Forest, XGBoost, and Elastic Net models on the composition-only dataset, perform constrained hyperparameter tuning, and generate performance metrics ($R^2$, RMSE) on a held-out test set.

**Why this priority**: This story delivers the core scientific analysis: quantifying the predictive power of composition alone. It directly addresses the research question regarding the fraction of variance explainable by composition.

**Independent Test**: This story is complete when the training pipeline produces a `model_results.json` containing $R^2$ scores for all three models on the test set, and the total runtime of the training job does not exceed 6 hours on a GitHub Actions `ubuntu-latest` runner.

**Acceptance Scenarios**:

1. **Given** a split dataset with a training set of [deferred] samples and a test set of [deferred] samples, **When** the Random Forest model is trained with a max depth constraint, **Then** the model achieves an $R^2$ score calculated on the held-out test set.
2. **Given** three candidate algorithms (RF, XGBoost, Elastic Net), **When** the grid search runs with 15 combinations, **Then** the system identifies the best-performing model based on cross-validated $R^2$ and records the optimal hyperparameters.
3. **Given** the best model and a linear baseline, **When** a permutation test (10,000 iterations) is performed on the prediction errors, **Then** the system outputs a p-value indicating whether the ML model significantly outperforms the linear baseline at $\alpha=0.05$.

---

### User Story 3 - Quantify Variance Partitioning and Feature Importance (Priority: P3)

The researcher MUST be able to extract SHAP values to rank compositional descriptors, generate partial dependence plots, and calculate the proportion of total variance in diffusion rates explained by the model (adjusted $R^2$) to serve as a proxy for the "microstructural gap."

**Why this priority**: This story provides the interpretability and scientific insight required to answer "which descriptors govern diffusion" and "what fraction of variance is explainable," fulfilling the ultimate research goal.

**Independent Test**: This story is complete when a `feature_importance.json` file ranks descriptors by SHAP magnitude, and a `variance_partition.csv` reports the adjusted $R^2$ as the estimated upper bound of composition-only predictive power.

**Acceptance Scenarios**:

1. **Given** the trained best model, **When** SHAP analysis is run on the test set, **Then** the system outputs a ranked list of features and explicitly identifies the top two descriptors regardless of their identity.
2. **Given** the top-ranked descriptor, **When** a partial dependence plot is generated, **Then** the plot visualizes the non-linear relationship between that descriptor and $\log_{10} D$.
3. **Given** the total variance of the target variable, **When** the model's explained variance is calculated, **Then** the system outputs the adjusted $R^2$ as a specific percentage (e.g., 0.45) representing the composition-explainable fraction, explicitly labeled as an upper bound on microstructural influence.

### Edge Cases

- What happens if the NIST/Materials Project repositories return zero entries matching the strict "BCC + Carbon Diffusion" criteria? The system MUST raise a specific `DataInsufficientError` halting the pipeline rather than training on an empty set.
- How does the system handle entries where atomic fractions do not sum to 1.0 due to rounding errors in the source data? The system MUST normalize fractions to sum to 1.0 before feature engineering.
- What happens if the dataset size is too small (<30 samples) for reliable 5-fold cross-validation? The system MUST fall back to a leave-one-out strategy or report a `PowerWarning` in the output log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST filter the raw dataset to include ONLY entries with Body-Centered Cubic (BCC) crystal structures and exclude all non-BCC phases to ensure microstructural isolation (See US-1).
- **FR-002**: System MUST compute compositional descriptors (atomic radius variance, valence electron concentration, electronegativity spread) using `pymatgen` or `matminer` without accessing any microstructural data (See US-1).
- **FR-003**: System MUST log-transform the diffusion coefficient target variable using base-10 logarithm to handle the wide dynamic range of kinetic data (See US-1).
- **FR-004**: System MUST train Random Forest, XGBoost, and Elastic Net regression models using `scikit-learn` with a constrained grid search of 15 combinations to prevent overfitting (See US-2).
- **FR-005**: System MUST calculate $R^2$, RMSE, and MAE on a held-out test set (size determined by 80/20 split if total N ≥ 30, otherwise [deferred] leave-one-out) and perform a permutation test (10,000 iterations) against a linear baseline at $\alpha=0.05$ (See US-2).
- **FR-006**: System MUST generate SHAP values to rank the contribution of each compositional descriptor and produce partial dependence plots for the top features (See US-3).
- **FR-007**: System MUST output the adjusted $R^2$ as the estimated upper bound of variance in diffusion rates explainable by composition alone, explicitly noting that the residual variance includes noise, measurement error, and missing compositional descriptors, not just microstructure (See US-3).
- **FR-008**: System MUST validate the source provenance of each data point to flag entries where microstructural factors (grain boundaries, dislocations) are known to be uncontrolled, and exclude or flag these for sensitivity analysis (See US-1).

### Key Entities

- **DiffusionEntry**: Represents a single data point containing the metal composition (atomic fractions), crystal structure (BCC), and measured diffusion coefficient ($D$).
- **CompositionalDescriptor**: A derived feature set including atomic radius variance, VEC, electronegativity spread, and mixing entropy, calculated from the composition.
- **ModelResult**: A record containing the algorithm type, hyperparameters, performance metrics ($R^2$, RMSE), and feature importance rankings.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The fraction of variance in $\log_{10} D$ explained by the best composition-only model is measured against the total variance of the target variable to quantify the "microstructural gap" (See US-3).
- **SC-002**: The predictive performance ($R^2$) of the best ML model is measured against the linear baseline using a permutation test to determine statistical significance (See US-2).
- **SC-003**: The runtime of the entire training and evaluation pipeline is measured against the 6-hour GitHub Actions `ubuntu-latest` free-tier limit to ensure compute feasibility (See US-2).
- **SC-004**: The feature importance ranking is measured against the system's ability to identify and report the top two descriptors regardless of their identity (See US-3).
- **SC-005**: The dataset completeness is measured against the requirement that [deferred] of training entries must have valid BCC structure tags and non-missing composition data, verified by counting entries with null BCC tags or missing composition and ensuring count is zero (See US-1).
- **SC-006**: The data provenance check is measured against the requirement that all entries used in the final model must have a 'single-crystal' or 'microstructure-controlled' flag in the source metadata, or be explicitly excluded (See US-1).

## Assumptions

- **Assumption on Data Availability**: The NIST Materials Data Repository and Materials Project contain a sufficient number of entries (>30) specifically for carbon diffusion in BCC metals to allow for a meaningful train/test split; if the count is lower, the project will report a "Data Scarcity" limitation rather than a failed model.
- **Assumption on Microstructural Exclusion**: The validity of the "composition-only" isolation is conditional on the success of FR-008; if the provenance check fails to confirm single-crystal or controlled conditions for the majority of the dataset, the results will be interpreted with the caveat that microstructural variance may be confounded with composition.
- **Assumption on Compute Constraints**: The dataset size, after filtering for BCC carbon diffusion, will fit within the ~7 GB RAM limit of a GitHub Actions `ubuntu-latest` runner, allowing the use of standard `scikit-learn` implementations without sampling or out-of-core processing.
- **Assumption on Variable Fit**: The compositional descriptors (atomic radius, VEC, electronegativity) available from the periodic table and stoichiometry are sufficient to capture the primary electronic and steric interactions governing carbon mobility in BCC lattices.
- **Assumption on Methodology**: Since the data is observational (no random assignment of composition), the resulting $R^2$ and feature importance are interpreted as **associational** relationships, not causal effects of composition on diffusion.