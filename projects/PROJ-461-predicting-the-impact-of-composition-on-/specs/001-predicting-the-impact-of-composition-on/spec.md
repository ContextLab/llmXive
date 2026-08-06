# Feature Specification: Predicting the Impact of Composition on the Density of Metallic Glasses

**Feature Branch**: `001-predict-metallic-glass-density`
**Created**: 2023-10-27
**Status**: Draft
**Input**: User description: "Predicting the Impact of Composition on the Density of Metallic Glasses"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The researcher needs to automatically download, parse, and clean a public dataset of metallic glass compositions and their corresponding bulk densities to create a ready-to-analyze tabular dataset. The system MUST attempt to download from the primary source (Zenodo). If the primary source fails, it MUST attempt the secondary source (Materials Cloud). If both sources fail or the combined dataset contains <50 valid rows, the system MUST switch to 'Pipeline Validation Mode' using a synthetic dataset generated from the linear mixing rule + random noise. The synthetic dataset MUST mimic the distribution of 'dominant elements' found in the real data (or a uniform distribution if real data is unavailable) to ensure compatibility with Stratified K-Fold splitting.

**Why this priority**: Without a clean, structured dataset containing composition (mass fractions) and target (density), no modeling or analysis can occur. This is the foundational step for the entire research workflow. The fallback ensures the pipeline can be validated even if real data is scarce.

**Independent Test**: The pipeline can be fully tested by running the data script against the target public repositories (Zenodo or Materials Cloud) and verifying the output CSV contains ≥50 rows with no missing values in the 'density' column and valid numeric types for all elemental mass fractions. If the dataset contains <50 rows or is unavailable, the system MUST switch to 'Pipeline Validation Mode' and generate a synthetic dataset with ≥100 rows, logging a warning `E_DATA_INSUFFICIENT`. The synthetic data generation MUST ensure the 'dominant element' distribution is preserved or uniformly distributed to support Stratified K-Fold.

**Acceptance Scenarios**:

1. **Given** the primary dataset URL (Zenodo) is accessible, **When** the data ingestion script executes, **Then** a local `raw_data.csv` is generated containing at least 50 metallic glass records with columns for elemental mass fractions and bulk density.
2. **Given** the primary dataset is unavailable, **When** the data ingestion script executes, **Then** it attempts the secondary source (Materials Cloud) and generates `raw_data.csv` if successful.
3. **Given** both sources are unavailable or the combined dataset contains <50 rows, **When** the data ingestion script executes, **Then** the system switches to 'Pipeline Validation Mode', generates a synthetic dataset with ≥100 rows based on the linear mixing rule + Gaussian noise (σ=0.05 g/cm³), and logs a warning `E_DATA_INSUFFICIENT`. The synthetic data MUST preserve the 'dominant element' distribution or use a uniform distribution if real data is unavailable.
4. **Given** the raw dataset contains missing density values, **When** the preprocessing step runs, **Then** those rows are either imputed with a documented method or filtered out, resulting in a `clean_data.csv` with zero missing values in the target column.
5. **Given** the dataset contains non-standard elemental symbols (e.g., "Fe" vs "IRON"), **When** the normalization step runs, **Then** all symbols are standardized to standard IUPAC elemental symbols (1 or 2 characters, e.g., 'Fe', 'U', 'H') before feature engineering.

---

### User Story 2 - Compositional Feature Engineering and Model Training (Priority: P2)

The researcher needs to compute atomic-level descriptors (mean atomic mass, mean atomic radius, electronegativity variance, packing efficiency proxy) from the composition and train a Gradient Boosting Regressor to predict the *residual* density (ρ_actual - ρ_baseline) to isolate non-linear packing effects. The system MUST use *atomic fractions* (not mass fractions) for radius-based calculations to mitigate inherent collinearity. The baseline (ρ_baseline) is defined as the Linear Mixing Rule: ρ_baseline = Σ(w_i × ρ_element_i).

**Why this priority**: This implements the core scientific hypothesis: that composition-derived descriptors can predict bulk density *beyond* the linear mixing rule. It transforms raw data into the predictive model.

**Independent Test**: The feature engineering and training can be tested by running the pipeline on a fixed random seed and verifying that the model object is saved and that the top 3 descriptors contribute > 5% to the R² score improvement over the baseline. The model MUST be trained on the *residual* density (ρ_actual - ρ_baseline).

**Acceptance Scenarios**:

1. **Given** the `clean_data.csv` exists, **When** the feature engineering module runs, **Then** a new dataset is produced containing at least 5 derived features: mean atomic mass, mean atomic radius, electronegativity variance, atomic radius mismatch, and packing efficiency proxy (calculated using the specific non-linear formula defined in FR-002).
2. **Given** the training data is split using Stratified K-Fold Cross-Validation (k=5) based on the dominant element (the element with the highest mass fraction), **When** the Gradient Boosting Regressor (LightGBM) trains on the *residual* density, **Then** the model converges within 600 seconds on a standard CPU runner without GPU acceleration.
3. **Given** the trained model, **When** it predicts residual density on the held-out test set, **Then** the Mean Absolute Error (MAE) is calculated and logged, and the R-squared value is computed.
4. **Given** the mass fractions sum to 1.0, **When** radius-based descriptors are computed, **Then** the system uses *atomic fractions* (not mass fractions) for radius calculations to mitigate inherent collinearity.

---

### User Story 3 - Interpretability and Validation Reporting (Priority: P3)

The researcher needs to generate a report visualizing the relationship between predicted and actual density, identifying the most influential elemental properties via SHAP values, and confirming the model's robustness. If MAE > 0.1, the report MUST explicitly analyze the variance explained by radius mismatch as a distinct finding, comparing it against the Mean Atomic Mass baseline.

**Why this priority**: This provides the scientific evidence required to answer the research question. It moves beyond "black box" prediction to explain *why* the model works, validating the hypothesis about atomic mass vs. packing efficiency.

**Independent Test**: The reporting module can be tested by generating the PDF/HTML report and verifying it contains a scatter plot of predicted vs. actual density and a bar chart of feature importances.

**Acceptance Scenarios**:

1. **Given** the trained model and test set, **When** the visualization module runs, **Then** a scatter plot is generated showing predicted density vs. actual density with a correlation coefficient (R²) displayed in the title.
2. **Given** the model, **When** SHAP analysis is performed, **Then** a summary plot is generated ranking features by importance, explicitly showing whether mean atomic mass or atomic radius mismatch is the dominant predictor, and comparing their contributions.
3. **Given** the initial results, **When** a sensitivity analysis is run (adding Gaussian noise σ ∈ {0.01, 0.05, 0.1} to the target variable), **Then** the report includes a table showing how the MAE changes with small perturbations.
4. **Given** MAE > 0.1, **When** the report is generated, **Then** it explicitly analyzes the variance explained by radius mismatch as a distinct finding, using SHAP comparison and partial dependence plots, satisfying Constitution Principle VII.

### Edge Cases

- What happens when the public dataset URLs are temporarily unavailable or the repository structure changes? (System should retry 3 times with exponential backoff, then attempt the secondary source; if both fail, switch to 'Pipeline Validation Mode' with synthetic data).
- How does the system handle metallic glass systems with rare or undefined elements not in the standard periodic table data source? (System should log a warning and exclude the row, or use a fallback average atomic mass if <1% of data is affected).
- What if the dataset is too small (<50 rows) to support a meaningful train/test split? (System MUST switch to 'Pipeline Validation Mode' and generate a synthetic dataset, logging `E_DATA_INSUFFICIENT`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the metallic glass composition and density dataset from the specified public repositories: Primary (Zenodo) or Secondary (Materials Cloud). If both fail or the combined dataset contains <50 rows, the system MUST switch to 'Pipeline Validation Mode' and generate a synthetic dataset with ≥100 rows, mimicking the 'dominant element' distribution of the real data (or uniform if unavailable). (See US-1)
- **FR-002**: System MUST compute at least 5 compositional descriptors (mean atomic mass, mean atomic radius, electronegativity variance, atomic radius mismatch, packing efficiency proxy) for every alloy record using standard periodic table constants from the `mendeleev` library (verified source per Constitution Principle II). For radius-based descriptors, the system MUST use *atomic fractions* (not mass fractions) to mitigate collinearity. The 'Packing Efficiency Proxy' MUST be calculated using the specific non-linear formula: PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2), where σ_r is the standard deviation of atomic radii, r_mean is the mean atomic radius, and Δr is (max(r) - min(r)). **Guard Clause**: If σ_r = 0 (single-element or zero variance), PE MUST be set to 1.0. (See US-2)
- **FR-003**: System MUST split the dataset using Stratified K-Fold Cross-Validation (k=5) based on the dominant element (the element with the highest mass fraction) to ensure representation of different alloy families. (See US-2)
- **FR-004**: System MUST train a Gradient Boosting Regressor (LightGBM or XGBoost CPU version) to predict the *residual* density (ρ_actual - ρ_baseline) from the compositional descriptors, ensuring no GPU usage. The baseline (ρ_baseline) is defined as the Linear Mixing Rule: ρ_baseline = Σ(w_i × ρ_element_i). This residual training serves as the statistical control for the dominant element confound. (See US-2)
- **FR-005**: System MUST generate a comprehensive report including a scatter plot of predicted vs. actual density, a feature importance ranking (SHAP or permutation), and the final MAE and R² metrics. If MAE > 0.1, the report MUST explicitly analyze the variance explained by radius mismatch using SHAP comparison and partial dependence plots. (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis by adding Gaussian noise (σ ∈ {0.01, 0.05, 0.1}) to the target variable (residual density) and reporting the variance in Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE). If the dataset is insufficient, this analysis proceeds on the synthetic dataset. (See US-3)
- **FR-007**: System MUST implement a 'data_discovery' step that attempts the primary source, then the secondary source, and finally triggers 'Pipeline Validation Mode' if both fail or the row count is <50. (See US-1)

### Key Entities

- **MetallicGlassRecord**: Represents a single alloy entry; attributes include `composition` (map of element to mass fraction), `bulk_density` (float, g/cm³), and `derived_features` (map of computed descriptors).
- **PredictionModel**: Represents the trained regressor; attributes include `algorithm` (e.g., "LightGBM"), `hyperparameters`, and `feature_importance_map`.
- **AnalysisReport**: Represents the final output document; attributes include `metrics` (MAE, R²), `visualizations` (plots), and `interpretability_data` (SHAP values).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Mean Absolute Error (MAE) of the density prediction is measured against a community-standard threshold of MAE ≤ 0.1 g/cm³ on the held-out test set, consistent with typical precision for bulk density measurements in metallic glass literature. **If the dataset is <50 rows or unavailable, SC-001 is ignored (not just N/A) and success is determined solely by SC-006.** (See US-1, US-2, US-3)
- **SC-002**: The R-squared (R²) value is measured against a baseline model defined by the simple linear mixing rule: ρ_baseline = Σ(w_i × ρ_element_i), where w_i is the mass fraction and ρ_element_i is the standard elemental density. This ensures the baseline is independent of the model's atomic mass predictors. (See US-2, US-3)
- **SC-003**: The model's performance is measured against the hypothesis that the inclusion of packing efficiency and radius descriptors significantly improves prediction accuracy over the linear mixing rule baseline, as determined by a paired t-test on the MAE residuals (p < 0.05). The test compares the *Model's MAE on Residuals* vs *Baseline's MAE on Residuals* (which is the MAE of the raw data vs the linear rule), thereby validating the role of non-linear atomic packing effects. (See US-2, US-3)
- **SC-004**: The model training time is measured against the 6-hour CI runner limit, ensuring the entire pipeline (data ingestion, feature engineering, training, evaluation) completes within ≤ 2 hours to allow for multiple hyperparameter tuning iterations. (See US-2)
- **SC-005**: The sensitivity analysis results are measured by the variance in MAE across the swept noise levels (σ ∈ {0.01, 0.05, 0.1}), ensuring the model's performance is robust to small definition changes. (See US-3)
- **SC-006**: If the dataset is <50 rows or unavailable, the 'Pipeline Validation Mode' is triggered, and the project is considered successful if the synthetic data pipeline runs without error, generates a valid report, and the synthetic data mimics the 'dominant element' distribution (or uses uniform distribution). (See US-1)

## Assumptions

- The public datasets (Zenodo and Materials Cloud) are accessible via direct URLs without authentication. If not, the system falls back to synthetic data.
- Standard periodic table constants (atomic mass, atomic radius, electronegativity) are available via the `mendeleev` library, which is the **verified source** for these constants (satisfying Constitution Principle II), and do not require external network calls during runtime.
- The Gradient Boosting Regressor (LightGBM/XGBoost) can be installed and run in default precision on a CPU-only environment without requiring CUDA or GPU acceleration.
- The dataset size (after download and parsing) will fit within the available memory limit of the GitHub Actions free-tier runner.
- The relationship between composition and density is primarily governed by atomic properties, and any structural deviations (e.g., specific cooling rates) are either negligible or uniformly distributed in the dataset.
- The "packing efficiency proxy" is approximated using the specific non-linear geometric formula: PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2), where σ_r is the standard deviation of atomic radii, r_mean is the mean atomic radius, and Δr is (max(r) - min(r)), derived from composition alone. **If σ_r = 0, PE is set to 1.0.**
- The 'mendeleev' library is the verified source for periodic table constants, satisfying Constitution Principle II.
- The baseline model (ρ_baseline) is the Linear Mixing Rule (density-based), distinct from the 'Mean Atomic Mass' feature (mass-based). The model predicts the *residual* (ρ_actual - ρ_baseline) to isolate non-linear effects.