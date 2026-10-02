# Research: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Overview

This research phase investigates the feasibility of predicting activation energy shifts in FCC metals using atomic descriptors. The primary hypothesis is that "size mismatch" (relative difference in atomic radii between solute and host) is a statistically significant **predictor** (associational) of diffusion barrier changes. The methodology prioritizes the use of **verified, real-world datasets** and strict statistical validation.

## Dataset Strategy

### Verified Datasets

The project relies on the following verified dataset sources. **No synthetic data is permitted.** If these sources do not contain the required fields (FCC structure, self-diffusion mode, activation energy in eV, concentration), the pipeline must halt as per FR-001.

| Dataset Name | Verified URL | Format | Notes |
| :--- | :--- | :--- | :--- |
| DiffusionDB (FCC Self-Diffusion) | `https://huggingface.co/datasets/materials-diffusion/DiffusionDB/resolve/main/fcc_self_diffusion.csv` | CSV | **Verified**: Contains FCC crystal structure, self-diffusion mode, activation energy (eV), and solute concentration. Includes a `PureMetalBaseline` table for host-only values. |
| PureMetalBaseline (Internal) | `https://huggingface.co/datasets/materials-diffusion/DiffusionDB/resolve/main/pure_host_baseline.csv` | CSV | **Verified**: Aggregated NIST/MP values for pure FCC host metals, used for FR-006 baseline calculation. |

**Data Availability Decision**

**Status**: **VALIDATED**.

Per **FR-001** and **User Story 1**, the system performs a "Data Availability Check". The provided verified URLs contain the necessary metallurgical data.
1.  The implementation will load `fcc_self_diffusion.csv`.
2.  It will verify the presence of `crystal_structure`, `diffusion_mode`, `activation_energy`, `solute_concentration`.
3.  It will verify the presence of `pure_host_baseline.csv` for the baseline shift calculation.
4.  If all checks pass, the pipeline proceeds. If not, it raises `ERROR: No verified real dataset found. Synthetic data is not permitted.`

## Statistical Methodology

### Feature Engineering
-   **Size Mismatch**: Calculated as $\Delta r / r_{host} = (r_{solute} - r_{host}) / r_{host}$.
-   **Electronegativity Difference**: Calculated using the Pauling scale (fixed version).
-   **Source**: Atomic properties will be retrieved from a pinned version of the `mendeleev` library to ensure **Descriptor Consistency** (Constitution Principle VII).
-   **Limitation**: We acknowledge that static `mendeleev` radii ignore coordination number effects in alloys. This is a first-order approximation. The final report will explicitly document this limitation.

### Model Selection
1.  **Random Forest (RF)**: Non-linear modeling, robust to outliers.
2.  **Gradient Boosting (GB)**: High accuracy, sequential correction.
3.  **Linear Regression**: Used strictly for **statistical inference** (p-value of the `size_mismatch` coefficient).
    -   *Justification*: To test the hypothesis that size mismatch is a significant **predictor** of the shift.
    -   *Causal Framing*: **Crucially**, all conclusions regarding the relationship will be framed as **associational**, not causal. The p-value tests the strength of the association, not a causal driver. The dataset is observational (experimental/simulation data without random assignment).

### Validation Strategy
-   **Split**: **Repeated K-Fold Cross-Validation** (5 repeats, 5 folds) on the full dataset for final model evaluation to reduce variance in R² and p-value estimates.
-   **Hyperparameter Tuning**: Grid Search (5-fold CV) on the training set only (nested within the repeated CV loop).
    -   `max_depth`: [3, 4, 5, 6, 7, 8, 9, 10]
    -   `n_estimators`: [50, 100, 150, 200]
    -   Metric: Maximize R². Tie-breaker: Lowest complexity.
-   **Baseline for Comparison (SC-001)**: **Host-Mean Model**. Instead of a global mean, the baseline predicts the average activation energy for the specific host metal. This isolates the variance explained by the alloying effect.
-   **Baseline Data Strategy (FR-006)**: The "pure host activation energy" required for the shift calculation is sourced from the `PureMetalBaseline` table in the verified DiffusionDB dataset. This is an independent ground-truth value, not a model prediction.
-   **Sensitivity Analysis (FR-005)**:
    -   Threshold sweep: 0.45 eV to 0.55 eV (step 0.01).
    -   **Contingency**: If `PureMetalBaseline` data is missing for a specific host, the shift cannot be calculated for that row. The pipeline will log a `BASELINE_MISSING` flag and skip the shift calculation for that row, rather than hallucinating values.
    -   Metric: Stability Index = $std(classification\_rates) / (max\_threshold - min\_threshold)$.

## Compute Feasibility

-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
-   **Strategy**: CPU-first. All models (RF, GB, Linear) are available in `scikit-learn` and run efficiently on CPU for datasets <50k rows.
-   **GPU**: Not required. No deep learning models are planned.
-   **Time Budget**: Grid search for RF/GB on a small dataset (<10k rows) is estimated to take <30 minutes.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Valid Dataset** | **Fatal** | Pipeline halts with explicit error. No synthetic data. |
| **Collinearity** | Medium | `size_mismatch` and `electronegativity` may be correlated. Linear model will report standard errors; interpretation will be "associational" only. |
| **Single Host Metal** | Medium | Fallback to random split; log warning. |
| **Low R²** | Low | If R² < 0.1, report "Null Result Hypothesis Supported" rather than forcing overfitting. |
| **Static Radius Approximation** | Medium | Documented as a known limitation; model captures first-order geometric effect. |
