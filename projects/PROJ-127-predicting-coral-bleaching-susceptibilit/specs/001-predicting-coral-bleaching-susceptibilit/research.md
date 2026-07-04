# Research: Predicting Coral Bleaching Susceptibility from Environmental Data

## 1. Problem Statement & Scientific Rationale

The objective is to determine if a machine learning model integrating oceanographic variables (SST, DHW) and species-level traits (thermal tolerance) can accurately predict bleaching susceptibility across reef locations. This is an **observational** study; findings will be framed as associational, not causal. The spatial generalization (training on Western Pacific, testing on Eastern Pacific) is critical to ensure the model learns robust environmental-trait interactions rather than region-specific noise.

**Critical Constraint**: This study **requires** real, verified data for the target variable (bleached) and key predictors (thermal tolerance). If verified sources for the Coral Trait Database or ReefBase are not available, the study **cannot proceed** to model training. Instead, a "Data Gap Report" will be generated. The use of synthetic data for training is **strictly prohibited** in the default scientific mode, as it renders the research question unanswerable and violates Constitution Principle VI.

## 2. Dataset Strategy

The following datasets are identified. **Only verified URLs from the project block are used.** If a required dataset is missing from the verified list, the pipeline halts.

| Dataset | Role | Source / Verified URL | Status / Notes |
|:--- |:--- |:--- |:--- |
| **NOAA SST/DHW** | Environmental Predictors | ` (NOAA) | **Verified**. Used for SST and DHW features. |
| **UNEP Reef Geometries** | Spatial Context | ` | **Verified**. Used for reef location mapping. |
| **DHW Specific** | Thermal Stress | ` | **Verified**. Supplemental DHW data if needed. |
| **Coral Trait Database** | Species Traits | **NO VERIFIED SOURCE** | **Critical Gap**: No verified URL exists. The pipeline will **HALT** and generate a Data Gap Report. |
| **ReefBase Bleaching Events** | Target Label | **NO VERIFIED SOURCE** | **Critical Gap**: No verified URL exists. The pipeline will **HALT** and generate a Data Gap Report. |
| **Independent Historical Reports** | Validation (SC-003) | **NO VERIFIED SOURCE** | **Limitation**: No verified URL for independent historical reports. If missing, SC-003 validation is marked "Not Applicable". |

**Potential Real Data Sources (for future acquisition)**:
- **Coral Trait Database**: Official site (e.g., `coraltraits.org`). Requires manual verification and URL submission to the project.
- **ReefBase**: Official site (e.g., `reefbase.org`). Requires manual verification and URL submission to the project.

**Dataset Variable Fit & Mismatch Handling**:
- **Critical Mismatch**: The spec requires "Species Thermal Tolerance" and "Bleaching Label". The verified list **does not** contain URLs for these.
- **Resolution Strategy**: The plan **will NOT** use synthetic data. Instead:
 1. Ingest verified NOAA/UNEP data.
 2. Check for required Coral Trait and ReefBase data.
 3. **If missing**: Generate `data_gap_report.md` and **HALT**. The model training step is skipped.
 4. **If present**: Proceed with real data analysis.
 5. **Simulation Mode**: An explicit, opt-in flag (`--simulation-mode`) can be set to use synthetic data for pipeline testing only. This mode is clearly labeled as "Simulation Only" and does not claim to predict real-world phenomena. Spatial hold-out and statistical validation are disabled in this mode.

## 3. Methodology & Statistical Rigor

### 3.1 Data Preprocessing
- **Imputation**: Missing SST/DHW values (cloud cover) will be imputed using the nearest valid temporal neighbor (max 30-day gap).
- **Feature Engineering**:
 - Lagged variables: 30-day rolling mean SST.
 - Interaction terms: `DHW * Thermal_Tolerance`.
- **Definitional Circularity Check**: Before modeling, verify if DHW is derived from SST. If so, flag the circularity and recommend dropping one or using a residual approach to prevent the model from learning a mathematical definition rather than an ecological signal.
- **Collinearity Check**: Variance Inflation Factor (VIF) calculated for all environmental predictors. Features with VIF > 5 are dropped (FR-009).

### 3.2 Modeling Strategy
- **Algorithm**: XGBoost (Gradient Boosting Machine).
- **Split Strategy**: Spatial hold-out (Train: West Pacific, Test: East Pacific). **Only performed if real data is available.**
- **Hyperparameter Tuning**: 5-fold cross-validation within the training set (max_depth, learning_rate, n_estimators).
- **Constraints**: CPU-only execution. Data subset to ~7 GB RAM.

### 3.3 Statistical Validation (FR-007)
- **Permutation Importance**: 1,000 permutations to calculate empirical p-values for feature importance.
- **Multiple Comparison Correction**: Benjamini-Hochberg FDR applied to all p-values to control the false discovery rate. **Justification**: Essential to prevent false-positive feature identification in high-dimensional data.
- **Bootstrap Stability (SC-002)**: Perform **100 bootstrap resamples** to measure the ranking stability of the top-3 predictors. This task is explicitly included to satisfy SC-002.
- **Collinearity Warning**: If predictors are definitionally related (e.g., SST and DHW), independent effects will not be claimed; descriptive relationships will be reported.

### 3.4 Evaluation Metrics
- **Primary**: ROC-AUC on the held-out geographic test set (SC-001). **Conditional**: Only calculated if real data is available.
- **Secondary**: Area Under the Precision-Recall Curve (AUPRC) for spatial risk map validation (SC-003). **Conditional**: Only calculated if independent historical reports are available.
- **Robustness**: Threshold sensitivity analysis at {0.3, 0.5, 0.7} reporting FP/FN rates and **the variation (delta/range) of these rates** (FR-008, SC-005). This variation metric is calculated as a distinct output.

## 4. Compute Feasibility & Risk

- **Hardware**: 2 CPU cores, ~7 GB RAM.
- **Strategy**:
 - Data is sampled/spatially subset to fit RAM.
 - XGBoost is used with `tree_method="exact"` or `approx` (CPU optimized).
 - No GPU libraries (CUDA, bitsandbytes) are used.
 - Runtime is capped at 6 hours; if exceeded, the spatial subset size is reduced.
- **Risk**: If the verified datasets lack the required "Species Traits" or "Bleaching Labels", the model **cannot be trained**. The plan mitigates this by generating a **Data Gap Report** and halting, rather than proceeding with invalid synthetic data.
