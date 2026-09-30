# Research: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Executive Summary

This research investigates the predictive power of thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance) on the critical cooling rate of ternary alloy systems. Using a curated subset of the **BMG (Bulk Metallic Glass) Database**, we employ a Random Forest regressor to model the relationship. The study is strictly associational, acknowledging the observational nature of the data.

## Dataset Strategy

We utilize the **BMG (Bulk Metallic Glass) Database**, specifically targeting entries with reported critical cooling rates for ternary alloys.

| Dataset Name | Source URL | Access Method | Suitability |
| :--- | :--- | :--- | :--- |
| BMG Targets | `https://huggingface.co/datasets/materials-project/bmg-glass-formers/resolve/main/bmg_ternary.csv` | Direct HTTP Download | **Primary**: Contains critical cooling rate targets and ternary alloy compositions. |

**Dataset Selection Rationale**: The BMG dataset is the only verified source in the input block containing the specific `critical_cooling_rate` field required for the target variable. **OQMD is explicitly excluded** as it is a DFT database of equilibrium formation energies and **does not** contain experimental cooling rates (a kinetic property). The BMG dataset contains experimental glass-forming ability data.

**Data Availability Check**:
- **Target Variable**: `critical_cooling_rate` (continuous, K/s).
- **Predictors**: Elemental composition (A, B, C) to derive thermodynamic descriptors.
- **Feasibility**: The dataset is publicly accessible via HuggingFace, allowing programmatic download on the GitHub Actions runner without credentials.
- **Size**: We anticipate >1000 entries; we will filter for N ≥ 500 valid ternary records.

## Thermodynamic Feature Engineering

The following descriptors will be computed for every alloy record using standard elemental properties from the `mendeleev` library (Periodic Table):

1.  **Mixing Enthalpy ($\Delta H_{mix}$)**:
    Calculated as the weighted sum of binary interaction enthalpies between constituent elements, based on the Miedema model or similar empirical databases embedded in the periodic table properties.
    Formula: $\Delta H_{mix} = \sum_{i \neq j} c_i c_j \Delta H_{ij}$
    *Where $c_i$ is the atomic fraction of element $i$.*

2.  **Atomic Size Mismatch ($\delta$)**:
    Measures the variance in atomic radii.
    Formula: $\delta = \sqrt{\sum_{i} c_i (1 - \frac{r_i}{\bar{r}})^2}$
    *Where $r_i$ is the atomic radius of element $i$ and $\bar{r}$ is the composition-weighted average radius.*

3.  **Electronegativity Variance ($\Delta \chi$)**:
    Measures the spread of electronegativity values.
    Formula: $\Delta \chi = \sqrt{\sum_{i} c_i (\chi_i - \bar{\chi})^2}$
    *Where $\chi_i$ is the electronegativity of element $i$.*

**Data Integrity**: All elemental properties (radius, electronegativity, binary enthalpies) will be sourced from a standard, versioned periodic table database (e.g., `mendeleev`) to ensure reproducibility (Constitution Principle VI).

## Methodology

### 1. Data Ingestion & Cleaning
- Download the BMG target CSV.
- Filter for ternary alloys (exactly 3 elements).
- Exclude entries with missing `critical_cooling_rate` or undefined elemental data.
- Log exclusions to `data/logs/exclusion_log.txt` and `data/logs/label_filtering_status.json`.
- **Validation**: If N < 500, raise `ValueError` and log to `data/logs/empty_dataset_error.log`.

### 2. Feature Engineering
- Compute $\Delta H_{mix}$, $\delta$, and $\Delta \chi$ for each record.
- Check for collinearity (Pearson correlation > 0.8). If detected, flag and re-run stability check.
- Save processed dataset to `data/processed/processed_alloys.csv`.

### 3. Model Training & Validation
- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Split**: 80/20 Train/Test split with `random_state=42`.
- **Cross-Validation**: 5-fold CV on the training set.
- **Metrics**: Mean RMSE, Fold Variance.
- **Baseline**: Compare against a Dummy Regressor (predicting mean) using a **two-sided t-test (p < 0.05)** to satisfy SC-002.

### 4. Feature Importance & Sensitivity
- **Permutation Importance**: 1000 permutations, `random_state=42`. Report p-values for top features (SC-004).
- **Sensitivity Analysis**: Sweep critical cooling rate thresholds **{50, 100, 150} K/s** (physically grounded based on literature values for glass formation, e.g., Inoue's rules) to assess RMSE stability (SC-003).
- **Associational Framing**: All results framed as correlations; no causal claims made (Constitution Principle VI, FR-006). A validation step will check for causal language in outputs.

## Compute Feasibility

- **Environment**: GitHub Actions CPU runner (2 cores, 7 GB RAM).
- **Strategy**:
    - **Data**: Stream or load the BMG subset directly. If the full dataset is too large, sample the first N rows or a fixed-seed random sample to fit memory, noting the power limitation.
    - **Model**: Random Forest is computationally efficient on CPU for moderate sample sizes and a small number of features.
    - **Time**: Expected runtime < 2 hours, well within the 6-hour limit (SC-005).
- **GPU**: Not required. No transformer or diffusion models are used.

## Statistical Rigor

- **Multiple Comparisons**: Not applicable for the primary regression (single target), but permutation p-values are corrected if multiple importance tests are run.
- **Power Analysis**: Target N ≥ 500 provides sufficient power for a Random Forest with ~3-5 predictors to detect non-trivial effects (effect size > 0.3).
- **Collinearity**: Explicitly checked; high correlation (>0.8) will trigger a stability re-run excluding one feature.
- **Measurement Validity**: Thermodynamic formulas are standard in materials science literature; citations will be provided in the final paper.

## Decision/Rationale

- **Why Random Forest?** Handles non-linear relationships between thermodynamics and cooling rates without requiring explicit functional forms. Robust to outliers.
- **Why BMG?** It is the only verified source with the specific `critical_cooling_rate` target variable required by the spec. OQMD is excluded as it lacks this kinetic property.
- **Why CPU?** The dataset size and model complexity are well within CPU capabilities, avoiding the need for GPU offloading and simplifying CI execution.

## Assumptions

- The data source (BMG dataset) is accessible and contains the `critical_cooling_rate` field for a sufficient number of ternary alloys (≥ 500) to support machine learning training.
- The Random Forest algorithm, as implemented in scikit-learn, is computationally feasible on a CPU-only environment with standard RAM for a dataset of moderate size and a standard number of features.
- The thermodynamic formulas for mixing enthalpy and atomic size mismatch are well-defined and can be calculated using standard elemental properties available in a local periodic table database.
- The relationship between thermodynamic parameters and glass-forming ability is non-linear, justifying the use of a Random Forest model over a linear regression model.
- No GPU or CUDA acceleration is available or required for the training and inference steps of this specific model size and dataset.
- The primary target variable is the continuous `critical_cooling_rate`. Binarization (if performed) is based on a physically-grounded threshold (e.g., 100 K/s).
- **The BMG dataset is the sole source of truth for the target variable; OQMD is explicitly excluded as it does not contain experimental cooling rates.**