# Research: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## 1. Dataset Strategy

The project relies on verified, open-source datasets available via Hugging Face. No access-gated data (e.g., Materials Project API requiring tokens) is used directly in the CI pipeline to ensure reproducibility. Instead, pre-dumped parquet files from verified sources are used, **with a mandatory Live API Verification Module for final novelty confirmation.**

| Dataset Role | Source Name | Verified URL | Programmatic Loader | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Thermal Conductivity (AFLOW)** | `dataset_thermalcond_aflow` | `https://huggingface.co/datasets/foundry-ml/dataset_thermalcond_aflow/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset("parquet", data_files=...)` | Used for formation energy/mixing enthalpy if available; filtered for 5+ elements. **Fallback source if primary lacks columns.** |
| **Thermal Expansion (AFLOW)** | `dataset_thermalexp_aflow` | `https://huggingface.co/datasets/foundry-ml/dataset_thermalexp_aflow/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset("parquet", data_files=...)` | Secondary source for thermodynamic properties. |
| **API Derived Data** | `all_apis_for_multiapi` | `https://huggingface.co/datasets/hmao/all_apis_for_multiapi/resolve/main/data/train-00000-of-00001-bd8d5e4d08813d65.parquet` | `datasets.load_dataset("parquet", data_files=...)` | Contains aggregated data from multiple sources; primary candidate for "Known" HEA entries. **Schema validated for required columns.** |
| **VEC Data** | **N/A (pymatgen)** | **N/A** | **`pymatgen.core.Element`** | **VEC constants are derived directly from `pymatgen`'s `Element` class. No external dataset is used.** |

**Dataset Validation & Filtering**:
1.  **Ingestion**: Load all verified parquet files.
2.  **Schema Validation**: Verify that the dataset contains `formation_energy` and `mixing_enthalpy` columns for 5+ element systems. If not, **fall back to `dataset_thermalcond_aflow`**.
3.  **Filtering**: Filter for entries with $\ge 5$ unique elements (HEA definition).
4.  **Deduplication**: Remove exact composition duplicates.
5.  **Splitting**:
 * **Training Set**: Random [deferred] of filtered data.
 * **Hold-out Known**: [deferred] of filtered data (present in source, absent from training).
    *   **True Novel**: Generated via combinatorial enumeration of elemental sets. **Step 1: Apply Thermodynamic Stability Filter (surrogate model prediction < 0.1 eV/atom). Step 2: Check against loaded dataset. Step 3: Final API Check (query Materials Project/AFLOW APIs for 'Not Found').**

**Constraint**: If the verified sources lack sufficient 5+ element entries, the "True Novel" generation will rely on combinatorial enumeration of the Periodic Table (using `pymatgen` elements) and checking against the loaded dataset. This ensures the "True Novel" set is truly novel relative to the *available* data.

## 2. Methodology & Statistical Rigor

### 2.1 Feature Engineering (FR-003)
Descriptors are calculated using `pymatgen` to ensure reproducibility (Constitution Principle VII).
*   **Atomic Radius**: Weighted mean and variance of atomic radii.
*   **Electronegativity**: Weighted mean and variance.
*   **VEC (Valence Electron Count)**: Weighted mean and variance (derived from `pymatgen`).
*   **Melting Point**: Weighted mean and variance.
*   **Clamping**: Values with near-zero variance are clamped to a small positive constant to prevent numerical instability (Edge Case).

### 2.2 Model Training (FR-004)
*   **Algorithms**: `RandomForestRegressor` and `GradientBoostingRegressor`.
*   **Validation**: 5-fold Cross-Validation (validated by source [2604.10702]).
*   **Hyperparameters**: `max_depth` and `n_estimators` tuned via grid search (CPU-tractable).
*   **Reproducibility**: `random_state` pinned in `config.py`.

### 2.3 Extrapolation Evaluation (FR-005, FR-006, FR-007)
*   **Hold-out Known**: Predictions compared to ground truth. $R^2$ and MAE calculated.
    *   **Statistical Test**: **Mann-Whitney U test** (non-parametric) comparing error distributions of Training (CV) vs. Hold-out sets to check for significant degradation (SC-003). **Threshold: p < 0.05 enforced and reported.**
*   **True Novel**: No ground truth available.
    *   **Uncertainty Metric**: Ensemble variance (std dev of predictions across trees or bootstrap samples). **Fallback: Conformal Prediction intervals if variance-distance correlation is weak.**
    *   **Geometric Metric**: **Mahalanobis distance** from the training data centroid, calculated after **StandardScaler normalization**. **Fallback: PCA-reduced Euclidean distance if covariance matrix is singular.**
    *   **Correlation**: Spearman rank correlation between prediction variance and **predicted formation energy** (lower energy = more stable) and **distance to nearest known stable phase**. **This breaks the circularity of correlating with hull distance.**
    *   **Validation**: The validity of the Mahalanobis distance metric is empirically tested against extrapolation error on the Hold-out set before being applied to the True Novel set.

### 2.4 Multiple Comparison & Power
*   **Multiple Comparisons**: If multiple models or metrics are tested, Bonferroni correction is applied to p-values.
*   **Power**: Acknowledged limitation: Small sample sizes in "True Novel" generation may limit statistical power. Results reported with confidence intervals.

## 3. Compute Feasibility (CPU-First)

*   **Memory**: Dataset loaded via streaming (chunk size configurable) or chunked processing to stay under 7 GB RAM.
*   **Time**: Random Forest and Gradient Boosting are highly parallelizable on CPU. With $N < 50k$ samples and $D \approx 8$ features, training time is estimated $< 2$ hours.
*   **GPU Escape Hatch**: Not required. All methods (RF, GB, Mahalanobis, Conformal Prediction) are CPU-tractable. If a GPU were needed (e.g., for a Deep Learning baseline), the plan would switch to a scaled-down Kaggle GPU run, but this project explicitly avoids DL for baseline stability.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Insufficient 5+ Element Data** | High: Cannot train or generate novel sets. | Use combinatorial enumeration of elements to generate "True Novel" candidates and verify against the loaded dataset. **Fallback to `dataset_thermalcond_aflow` if primary source lacks columns.** |
| **API Rate Limiting** | Medium: Data ingestion fails. | Use verified static parquet files (no live API calls for ingestion). **Live API calls are only for final novelty verification of a small subset.** |
| **Convex Hull Failure** | Medium: High-dimensional hull calculation fails. | Use **Mahalanobis distance with StandardScaler** with fallback to **PCA-reduced Euclidean distance** if dimensionality is too high. |
| **Fabrication of Results** | Critical: Rejected by panel. | All metrics computed dynamically from `data/processed/`; no hardcoded values in `config.py`. **Thermodynamic stability filter ensures physical plausibility.** |
| **Circular Validation** | High: Invalid uncertainty calibration. | Use **predicted formation energy** and **distance to stable phase** as independent proxies for stability, breaking the circularity with hull distance. |
