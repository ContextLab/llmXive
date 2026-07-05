# Research: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

## Scientific Background

Crystallographic texture (preferred orientation of grains) in rolled metals significantly influences mechanical properties like anisotropy, formability, and strength. The texture is determined by the deformation history, primarily governed by rolling speed, temperature, and reduction ratio. Traditional methods rely on physics-based simulations (e.g., crystal plasticity finite element methods), which are computationally expensive. This project investigates whether a data-driven regression model can accurately predict texture coefficients (ODF intensities) from processing parameters, offering a faster alternative for process optimization.

## Dataset Strategy

### Verified Sources Analysis
The project specification requires ingesting data from Materials Project, OMDB, and NIST. However, a review of the **Verified Datasets** block provided for this project reveals a critical mismatch:
- **OMDB (Open Materials Database)**: The verified URLs (`JARVIS_OMDB`, `OMD-Bench`) contain structural properties (formation energy, band gap) or unrelated benchmark data, not rolling process parameters or texture coefficients.
- **NIST**: The verified URLs contain medical conversations or LLM benchmark details, unrelated to materials science.
- **Materials Project**: No verified URL provided in the block.
- **ODF/MRD**: No verified source found.

**Conclusion**: No verified dataset in the provided list contains the required paired data (Rolling Speed, Temperature, Reduction Ratio, Texture Coefficients).

### Primary Strategy: Synthetic Data Generation (FR-011)
Given the absence of real-world paired data in the verified sources, the project will proceed using a **Physics-Based Synthetic Data Generator**.
- **Rationale**: This satisfies FR-001 and FR-008 by ensuring ≥50 samples per alloy family with known ground truth.
- **Method**: The generator will simulate the non-linear relationship between processing parameters and texture coefficients based on established metallurgical models (e.g., Taylor model approximations).
- **Validation**: The generator's output will be validated against the statistical distribution of known literature values (cited in `research.md` text, not as dataset URLs) and checked for internal consistency (ground truth).
- **Fallback**: If any real data becomes available in the future, the pipeline will seamlessly switch to ingestion mode.

### Generator Calibration Limitation
The generator is validated against "literature trends" but is **not** calibrated to a specific high-fidelity dataset of paired rolling/texture data (which is unavailable). Therefore, the "known ground truth" is a hypothesis. Training a model on this hypothesis and claiming it validates the hypothesis is tautological. **This project treats the synthetic run as a pipeline stress test, not a source of scientific discovery regarding real material correlations.**

### Dataset Summary Table

| Dataset Name | Source Type | Status | Variables Available | Action |
|--------------|-------------|--------|---------------------|--------|
| Real Rolling Data | Public Repos | **Unavailable** | Missing paired texture/process | Skip ingestion; use synthetic. |
| Synthetic Rolling Data | Internal Generator | **Active** | Speed, Temp, Reduction, ODF {100/110/111} | Generate ≥200 samples (≥50/alloy). |
| OMDB | HuggingFace | Verified URL | Structural properties | Exclude (mismatch). |
| NIST | HuggingFace | Verified URL | Medical/LLM data | Exclude (mismatch). |

## Statistical Methodology

### Model Selection: Multi-Output RandomForest
- **Rationale**: Texture prediction is a non-linear, multi-variate regression problem. RandomForest is robust to outliers, handles mixed feature scales well, and provides interpretable feature importances (FR-004, FR-009).
- **Multi-Output**: A single `MultiOutputRegressor` or native multi-output support will be used to predict ODF {100}, {110}, and {111} simultaneously, capturing correlations between texture components.
- **CPU Feasibility**: RandomForest is highly parallelizable on CPU and does not require GPU resources, fitting the 2-core/7GB RAM constraint.

### Feature Engineering (FR-002)
1.  **Standardization**: Convert all units to SI (m/s, °C, %).
2.  **Derived Features**:
    -   **Strain Rate**: Approximated from rolling speed and reduction.
    -   **Zener-Hollomon Parameter ($Z$)**: $Z = \dot{\epsilon} \exp(Q/RT)$, where $Q$ is activation energy, $R$ is gas constant, $T$ is temperature. This captures the combined effect of temperature and strain rate.
3.  **Confounding Variables**: If available (e.g., alloy composition), include as features. If not, log warning (FR-012).

### Validation & Metrics
-   **Cross-Validation**: 5-fold CV for hyperparameter tuning (n_estimators, max_depth).
-   **Metrics**: R², MAE, RMSE per coefficient (FR-005).
-   **Thresholds**: R² ≥ 0.10 (baseline for "better than random" in this noisy domain).
-   **Sensitivity Analysis**: Sweep thresholds to assess stability (FR-010).

### Statistical Rigor & Limitations
-   **Multiple Comparisons**: Not applicable for regression metrics, but feature importance thresholds will be adjusted for the number of features.
-   **Causal Inference**: This is an **observational/synthetic** study. Claims will be framed as **associational**. No randomization of physical processes is performed; the generator simulates the physics.
-   **Collinearity**: Rolling speed and strain rate are definitionally related. The plan will report their **Group Importance** (sum of scores) but acknowledge the collinearity in `research.md`. Individual feature importance scores will be reported but interpreted with caution.
-   **Power Analysis**: With ~200 synthetic samples, the power to detect moderate effect sizes (R² ~ 0.3) is high. For real data (if any), power may be low, but the synthetic baseline ensures the pipeline runs.

### Synthetic Data Expectations
-   **R²**: On synthetic data, a well-tuned model is expected to achieve R² >> 0.90. The R² ≥ 0.10 threshold is a **minimum sanity check**, not a scientific discovery threshold.
-   **Feature Importance**: High importance scores are expected for the generator's key parameters. This validates the pipeline's ability to learn the generator's logic, not necessarily real-world physics.

## Decision Rationale

| Decision | Alternative | Rationale |
|----------|-------------|-----------|
| **Synthetic Data** | Real Data Ingestion | Real data sources verified as mismatched (no texture/process pairs). Synthetic data ensures FR-001/008 compliance. |
| **RandomForest** | Neural Networks | Neural nets require GPU for efficient training and large datasets. RF is CPU-tractable and robust with small data. |
| **Multi-Output** | Separate Models | Texture components are physically coupled. Separate models lose this correlation and violate FR-004. |
| **Zener-Hollomon** | Raw Parameters | $Z$ captures the physics of hot deformation better than raw T and speed alone. |
| **Group Importance** | Individual Importance | Collinearity between raw and derived features makes individual importance meaningless. Group Importance provides a robust aggregate. |

## Generalization Risk

The synthetic generator assumes a simplified physics model (e.g., Taylor model). Real materials exhibit complex behaviors (grain boundary sliding, dynamic recrystallization) not captured by the generator. The model will likely fail on real data if these unmodeled factors dominate. This project explicitly treats the synthetic run as a **pipeline stress test**, not a discovery of real correlations.

## References (Verified Only)
- *No external dataset URLs are cited as data sources due to mismatch.*
- *General metallurgical principles (Zener-Hollomon, texture formation) are based on established literature (cited as text references, not dataset URLs).*
