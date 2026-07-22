# Feature Specification: Predicting the Impact of Composition on the Density of Metallic Glasses

**Feature Branch**: `001-predict-metallic-glass-density`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Impact of Composition on the Density of Metallic Glasses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download, parse, and clean a public dataset of metallic glass compositions and their corresponding bulk densities to create a ready-to-analyze tabular dataset.

**Why this priority**: Without a clean, structured dataset containing composition (mass fractions) and target (density), no modeling or analysis can occur. This is the foundational step for the entire research workflow.

**Independent Test**: The pipeline can be fully tested by running the data script against the target public repository and verifying the output CSV contains ≥100 rows with no missing values in the 'density' column and valid numeric types for all elemental mass fractions.

**Acceptance Scenarios**:

1. **Given** the public dataset URL is accessible, **When** the data ingestion script executes, **Then** a local `raw_data.csv` is generated containing at least 100 metallic glass records with columns for elemental mass fractions and bulk density.
2. **Given** the raw dataset contains missing density values, **When** the preprocessing step runs, **Then** those rows are either imputed with a documented method or filtered out, resulting in a `clean_data.csv` with zero missing values in the target column.
3. **Given** the dataset contains non-standard elemental symbols (e.g., "Fe" vs "IRON"), **When** the normalization step runs, **Then** all symbols are standardized to IUPAC 2-letter codes before feature engineering.

---

### User Story 2 - Compositional Feature Engineering and Model Training (Priority: P2)

The researcher needs to compute atomic-level descriptors (mean atomic mass, mean atomic radius, electronegativity variance) from the mass fractions and train a Gradient Boosting Regressor to predict density.

**Why this priority**: This implements the core scientific hypothesis: that composition-derived descriptors can predict bulk density. It transforms raw data into the predictive model.

**Independent Test**: The feature engineering and training can be tested by running the pipeline on a fixed random seed and verifying that the model object is saved and that feature importance scores are non-zero for at least the top 3 computed descriptors.

**Acceptance Scenarios**:

1. **Given** the `clean_data.csv` exists, **When** the feature engineering module runs, **Then** a new dataset is produced containing exactly 5 derived features: mean atomic mass, mean atomic radius, electronegativity variance, atomic radius mismatch, and packing efficiency proxy.
2. **Given** the training data is split 80/20, **When** the Gradient Boosting Regressor (LightGBM) trains, **Then** the model converges within 600 seconds on a standard CPU runner without GPU acceleration.
3. **Given** the trained model, **When** it predicts density on the held-out test set, **Then** the Mean Absolute Error (MAE) is calculated and logged, and the R-squared value is computed.

---

### User Story 3 - Interpretability and Validation Reporting (Priority: P3)

The researcher needs to generate a report visualizing the relationship between predicted and actual density, identifying the most influential elemental properties via SHAP values, and confirming the model's robustness.

**Why this priority**: This provides the scientific evidence required to answer the research question. It moves beyond "black box" prediction to explain *why* the model works, validating the hypothesis about atomic mass vs. packing efficiency.

**Independent Test**: The reporting module can be tested by generating the PDF/HTML report and verifying it contains a scatter plot of predicted vs. actual density and a bar chart of feature importances.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the visualization module runs, **Then** a scatter plot is generated showing predicted density vs. actual density with a correlation coefficient (R²) displayed in the title.
2. **Given** the model, **When** SHAP analysis is performed, **Then** a summary plot is generated ranking features by importance, explicitly showing whether mean atomic mass or atomic radius mismatch is the dominant predictor.
3. **Given** the initial results, **When** a sensitivity analysis is run (sweeping density thresholds or feature scales), **Then** the report includes a table showing how the MAE changes with small perturbations (e.g., ±0.05 g/cm³).

### Edge Cases

- What happens when the public dataset URL is temporarily unavailable or the repository structure changes? (System should retry 3 times with exponential backoff, then fail gracefully with a specific error code).
- How does the system handle metallic glass systems with rare or undefined elements not in the standard periodic table data source? (System should log a warning and exclude the row, or use a fallback average atomic mass if <1% of data is affected).
- What if the dataset is too small (<30 samples) to support a meaningful train/test split? (System should detect this and halt execution, prompting the user to acquire more data).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the metallic glass composition and density dataset from the specified public repository (e.g., Zenodo or GitHub) using `wget` and parse it into a structured DataFrame. (See US-1)
- **FR-002**: System MUST compute at least 5 compositional descriptors (mean atomic mass, mean atomic radius, electronegativity variance, atomic radius mismatch, packing efficiency proxy) for every alloy record using standard periodic table constants. (See US-2)
- **FR-003**: System MUST split the dataset into a training set and a test set using stratified sampling to ensure representation of different alloy families. (See US-2)
- **FR-004**: System MUST train a Gradient Boosting Regressor (LightGBM or XGBoost CPU version) to predict bulk density from the compositional descriptors, ensuring no GPU usage. (See US-2)
- **FR-005**: System MUST generate a comprehensive report including a scatter plot of predicted vs. actual density, a feature importance ranking (SHAP or permutation), and the final MAE and R² metrics. (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the target density prediction tolerance (e.g., ±0.01, ±0.05, ±0.1 g/cm³) and report the variation in false-positive/negative rates. (See US-3)

### Key Entities

- **MetallicGlassRecord**: Represents a single alloy entry; attributes include `composition` (map of element to mass fraction), `bulk_density` (float, g/cm³), and `derived_features` (map of computed descriptors).
- **PredictionModel**: Represents the trained regressor; attributes include `algorithm` (e.g., "LightGBM"), `hyperparameters`, and `feature_importance_map`.
- **AnalysisReport**: Represents the final output document; attributes include `metrics` (MAE, R²), `visualizations` (plots), and `interpretability_data` (SHAP values).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the density prediction is measured against a community-standard threshold for preliminary screening on the held-out test set. (See US-2, US-3)
- **SC-002**: The R-squared (R²) value is measured against the baseline of a simple linear mixing rule (weighted average of elemental densities) to determine if non-linear packing effects are significant. (See US-2, US-3)
- **SC-003**: The feature importance ranking is measured against the hypothesis that "mean atomic mass" is the dominant predictor, to confirm or refute the simple mixing rule assumption. (See US-3)
- **SC-004**: The model training time is measured against the 6-hour CI runner limit, ensuring the entire pipeline (data ingestion, feature engineering, training, evaluation) completes within ≤ 2 hours to allow for multiple hyperparameter tuning iterations. (See US-2)
- **SC-005**: The sensitivity analysis results are measured by the variance in MAE across the swept thresholds (±0.01, ±0.05, ±0.1 g/cm³), ensuring the model's performance is robust to small definition changes. (See US-3)

## Assumptions

- The public dataset (e.g., MGDB or similar) contains at least 100 valid records with both composition and density data, and the data is accessible via a direct URL without authentication.
- Standard periodic table constants (atomic mass, atomic radius, electronegativity) are available via a standard Python library (e.g., `mendeleev` or `pymatgen`) and do not require external network calls during runtime.
- The Gradient Boosting Regressor (LightGBM/XGBoost) can be installed and run in default precision on a CPU-only environment without requiring CUDA or GPU acceleration.
- The dataset size (after download and parsing) will fit within the available memory limit of the GitHub Actions free-tier runner.
- The relationship between composition and density is primarily governed by atomic properties, and any structural deviations (e.g., specific cooling rates) are either negligible or uniformly distributed in the dataset.
- The "packing efficiency proxy" can be approximated using the atomic radius mismatch and mean atomic radius without requiring complex molecular dynamics simulations.
