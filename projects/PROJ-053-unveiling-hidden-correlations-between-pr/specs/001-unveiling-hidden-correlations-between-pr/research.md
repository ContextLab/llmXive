# Research: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Executive Summary

This research phase validates the feasibility of using Gaussian Process Regression (GPR) to model the **associational** relationship between additive manufacturing (AM) process parameters and mechanical properties. The primary challenge identified is the **dataset-variable fit**: the project spec assumes the availability of datasets containing *laser power*, *scan speed*, *layer thickness*, *yield strength*, and *ductility*. However, the verified dataset list provided in the project inputs contains no source explicitly labeled as an "AM Machine Learning" dataset with these specific columns.

**Critical Finding**: The "AM-Machine-Learning" dataset mentioned in the spec has **NO verified source** in the provided list. The available verified datasets (GPR, UCI, CPU-only) do not appear to contain the required AM process parameters (laser power, scan speed) or mechanical properties.
- `gproud/Cutout_Men_Standing`: Image captioning data.
- `guanines/gpra_c/d`: Likely GPR benchmark data, but column names unknown; unlikely to be AM-specific.
- `udayl/UCI_HAR`: Human Activity Recognition.
- `jlh/uci-shopper`: Shopping behavior data.
- `ucinlp/drop`: Reading comprehension dataset.
- `AdityaMayukhSom/MixSub-LLaMA`: Text-only LLM overlap data.

**Decision**: The implementation plan must proceed with a **fallback strategy**. The code will be designed to accept *any* CSV with the required column structure, but the `download.py` script will fail gracefully if the specific AM dataset is not found. The research plan assumes that a valid AM dataset *will* be manually provided or discovered by the user before the pipeline runs, as the automated download from verified sources is currently impossible for the specific domain variables. The plan documents the *method* for handling AM data, but the *data source* remains a blocking gap until a verified URL is found.

## Dataset Strategy

| Dataset Name | Verified URL | Status | Usage Plan |
|:--- |:--- |:--- |:--- |
| **AM-Machine-Learning** | NO verified source found | **BLOCKING GAP** | **Fallback**: The code will include a `data/raw/am_data.csv` placeholder. The pipeline will assume the user manually places a valid CSV here. The automated downloader will skip this dataset and log a warning: "No verified source found for AM-Machine-Learning; expecting manual data placement." |
| **GPR (generic)** | ` | Verified | **Not Applicable**: Data does not match AM domain variables. |
| **UCI HAR** | ` | Verified | **Not Applicable**: Human activity data, not AM. |
| **CPU-only (LLM)** | `https://huggingface.co/datasets/AdityaMayukhSom/...` | Verified | **Not Applicable**: Text data. |

**Data Variable Fit Analysis**:
- **Required**: `laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`.
- **Available**: None of the verified datasets contain these columns.
- **Mitigation**: The `preprocess.py` script will validate the column presence. If missing, it will halt with a clear error: "Dataset missing required columns: [list]." The research assumes the user will supply a dataset that meets the spec's variable requirements, even if the download URL is not automated.

## Methodology & Statistical Rigor

### 1. Gaussian Process Regression (GPR)
- **Kernel**: Radial Basis Function (RBF) / Squared Exponential kernel.
- **Rationale**: GPR is non-parametric and provides a natural measure of uncertainty (predictive variance), satisfying Principle VI (Non-Linear Process-Property Mapping).
- **Hyperparameter Optimization**: 5-fold cross-validation to maximize log marginal likelihood (LML).
- **Multiple Comparison Correction**: Not applicable for regression (no hypothesis tests on multiple groups). However, **family-wise error** is managed by reporting the full posterior distribution rather than point estimates.
- **Sample Size**: Minimum 50 samples required (FR-001). If N < 50, the system halts.
- **Power Limitation**: Acknowledged. With N=50-500, the model may have high uncertainty in sparse regions. This is a feature, not a bug, as it highlights where more data is needed (FR-007).

### 2. Confounder Sensitivity Analysis (Addressing Methodology-a638afaf)
- **Risk**: Unmeasured confounders (e.g., room temperature, machine calibration) may drive spurious correlations.
- **Strategy**: The plan proposes **stratification by `alloy_type`** as a proxy for unmeasured environmental confounders. If the dataset contains alloy types, the model will be trained and evaluated separately for each type. This helps isolate whether the process-property relationship is consistent across materials or driven by specific machine/environmental conditions.
- **Limitation**: This is not a full causal adjustment but a sensitivity check.

### 3. Power & Simulation Strategy (Addressing Methodology-f8d1d9b4)
- **Concern**: N=50 may be insufficient to detect non-linearities in GPR.
- **Strategy**: The plan mandates a **Synthetic Data Simulation** (Task 2.6). Before running on real data, the system will generate synthetic non-linear data with known noise levels and sample size N=50.
- **Goal**: Empirically verify if GPR can recover the signal at N=50. If the synthetic test fails, the final report will explicitly flag the "High Uncertainty / Low Power" limitation. This replaces the missing theoretical power analysis with an empirical validation step.

### 4. Causal Inference & Assumptions
- **Observational Nature**: The data is observational (experimental logs, not randomized controlled trials).
- **Claim Framing**: All claims are framed as **associational** ("Laser Power is associated with Yield Strength") rather than causal ("Increasing Laser Power causes Yield Strength to increase").
- **Confounding**: The model assumes no unmeasured confounders (e.g., room temperature, machine calibration) affect the relationship. This is a limitation of the dataset.

### 5. Measurement Validity & Data Leakage (Addressing Scientific Soundness-c07614cf)
- **Normalization**: To prevent data leakage, normalization (Min-Max) is **fit ONLY on the training set** and then applied to the test set. Global normalization (fit on all data) is explicitly forbidden.
- **Regime Interpretability**: To address the concern that normalized data makes "parameter regimes" uninterpretable, the plan mandates recording the **physical min/max bounds** of the training set. Visualizations will be annotated with these physical units (e.g., "Laser Power: 100-500W"), ensuring the uncertainty heatmap is interpretable as a guide for absolute physical regimes, not just relative statistical outliers.

### 6. Predictor Collinearity (Addressing Scientific Soundness-d0e0d9a9)
- **Risk**: Process parameters (e.g., energy density = Power / (Speed * Thickness)) are mathematically derived.
- **Handling**: The plan will **explicitly exclude derived features** (like Energy Density) from the input set. Only raw, independent parameters (`laser_power`, `scan_speed`, `layer_thickness`) will be used. This prevents perfect multicollinearity which would destabilize the GPR kernel length-scales.

## Compute Feasibility

- **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, No GPU).
- **Model**: GPR with RBF kernel on N=500 samples.
- **Complexity**: GPR training is O(N^3). For N=500, N^3 = 125,000,000 operations. This is well within the 6-hour limit on 2 cores.
- **Memory**: The kernel matrix for N=500 is 500x500 floats (approx. 2 MB). Even with overhead, memory usage will be < 1 GB.
- **Libraries**: `scikit-learn` (CPU-only) is sufficient. No `torch`, `tensorflow`, or `bitsandbytes` required.
- **Strategy**: If N > 1000, the code will sample 1000 rows or use a sparse approximation (e.g., `GPR` with `optimizer="fmin_l_bfgs_b"` and `n_restarts_optimizer=5`), but the spec assumes N < 500.

## Decision Rationale

- **Why GPR?** It is the only standard library method in `scikit-learn` that provides both non-linear regression and uncertainty estimates (predictive variance) without requiring deep learning or GPU resources.
- **Why not Neural Networks?** NNs require large datasets (>10k) for stability and are overkill for N=50-500. They also lack native uncertainty quantification without complex Bayesian approximations.
- **Why not Linear Regression?** Fails to capture the non-linear microstructural evolution (Principle VI). (Note: Linear Regression is used ONLY as a baseline for SC-001).
- **Why not Random Forest?** Random Forests provide feature importance but do not provide a smooth uncertainty surface (predictive variance) required for the contour plots (US-3).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing AM Dataset** | High (Pipeline cannot run) | Code halts with clear error; user must manually provide `data/raw/am_data.csv`. |
| **Insufficient Samples (N < 50)** | High (Model fails) | Preprocessing script checks N and halts if < 50 (FR-001). |
| **Zero Variance Features** | Medium (Singularity) | `preprocess.py` detects zero-variance columns and excludes them with a warning. |
| **High Uncertainty Regions** | Low (Expected outcome) | These regions are the *output* of the analysis (FR-007), not a failure. |
| **Unverified Data Source** | High (Scientific validity) | Final report MUST include a "Data Provenance Acknowledgment" section detailing the manual data source and its limitations. |

## Conclusion

The methodology is statistically rigorous and computationally feasible for the target environment. The primary blocking risk is the **lack of a verified AM dataset** in the provided list. The implementation plan proceeds under the assumption that a valid CSV will be provided manually or discovered later, with the code robustly handling the missing data scenario. The GPR approach satisfies all functional requirements and the project constitution's demand for non-linear, uncertainty-aware modeling. **Crucially, all results are framed as associational, and the plan includes a synthetic data simulation to empirically validate the power of the model at low sample sizes.**