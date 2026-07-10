# Research: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## 1. Dataset Strategy

### Verified Sources & Alignment
The project relies exclusively on the verified OC20 dataset. Dependencies on unverified sources (Materials Project, 2025 CO₂ hydrogenation study) and the experimental `experimental_tof` target have been removed. The target variable is the DFT-calculated reaction energy (`energy_change`) available in OC20.

| Dataset | Description | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **OC20** | Catalyst structures, DFT energies, surface facets. | ` (Sample) | **Verified** |

**Critical Pivot**:
- **Target Variable**: Changed from `experimental_tof` (unavailable/verified) to `energy_change` (DFT reaction energy, available in OC20).
- **Descriptors**: `d_band_center` and `adsorption_energy` are NOT native to raw OC20 for all entries. They will be derived using structure-based proxies (e.g., adsorption energy scaling relations) or computed on-the-fly if resources permit. If derivation fails, structure-based KNN imputation will be used.
- **Alignment Key**: Changed to `composition`, `surface_facet` (as `synthesis_condition` is not available in OC20 and was part of the unverified experimental alignment).

### Data Volume & Feasibility
- **Target**: ≥3000 matched entries (power analysis target).
- **Constraint**: The free-tier runner has a limited disk capacity. The OC full dataset comprises approximately two million entries. (too large).
- **Strategy**: The plan will download a **stratified sample** of the OC20 dataset (e.g., 10k entries) based on composition families to ensure representativeness and meet the 3000-entry target. Stratified sampling minimizes selection bias compared to random sampling.

## 2. Statistical & Methodological Rigor

### Statistical Methods
- **Model**: Gradient-Boosted Regression Trees (XGBoost).
 - *Justification*: Handles non-linear relationships between electronic descriptors and reaction energy; robust to outliers; compatible with CPU-only execution.
- **Baseline**: Linear Regression (d-band + adsorption energy).
 - *Justification*: Tests the Sabatier principle baseline; allows direct comparison of added value from expanded descriptors.
- **Hypothesis Testing**:
 - **Primary**: Paired t-test on absolute errors (XGBoost vs. Linear) if Shapiro-Wilk indicates normality (α=0.05).
 - **Fallback**: Wilcoxon signed-rank test if normality is rejected.
 - **Bias Correction**: Nested cross-validation is used to prevent selection bias during hyperparameter tuning. The outer loop evaluates the model, while the inner loop selects hyperparameters. This ensures the final t-test is unbiased.
- **Power Analysis**:
 - Target n ≥ 3000 for α=0.05, power=0.8.
 - *Limitation*: If the stratified sample yields <500 entries, the plan will proceed with the available data but explicitly state the power limitation in the final report (SC-002).

### Causal & Validity Assumptions
- **Causal Claims**: The study is **observational**. Claims will be framed as **associational** (predictive), not causal. No randomization strategy exists for catalyst composition.
- **Measurement Validity**:
 - `d_band_center`: Standard descriptor in catalysis (Nørskov et al.).
 - `adsorption_energy`: Derived from DFT; assumed valid if sourced from OC20 proxies.
 - **Collinearity**: `d_band_center` and `adsorption_energy` may be correlated. The plan will compute Variance Inflation Factors (VIF) and report them. If VIF > 5, the linear model interpretation will be qualified.
- **Confounding**: `synthesis_condition` is removed from the alignment key. A sensitivity analysis on facet-specific models will be performed to check for facet-based confounding.

### Missing Data Handling
- **Strategy**: Structure-based k-Nearest Neighbors (k=5) imputation.
 - *Method*: Compute Morgan fingerprints (radius=2, 2048 bits) of the surface slab atoms. Use Euclidean distance in fingerprint space to find neighbors.
 - *Fallback*: If <5 neighbors exist, the entry is flagged and excluded from training (FR-003).
 - *Bias Check*: Compare distributions of imputed vs. non-imputed features to ensure no systematic bias.

## 3. Computational Feasibility (CPU/GPU)

- **Hardware**: 2 CPU cores, 7 GB RAM, 6h limit.
- **Library Choice**:
 - `xgboost`: CPU-optimized, supports early stopping.
 - `shap`: CPU-only `TreeExplainer` is efficient.
 - `scikit-learn`: Standard CPU implementation.
 - `rdkit`: For generating Morgan fingerprints.
- **Memory Management**:
 - Data will be loaded in chunks or sampled to ensure <6 GB RAM usage.
 - Intermediate DataFrames will be deleted explicitly (`del` + `gc.collect()`).
- **Runtime**:
 - Download: variable duration (network dependent).
 - Preprocessing: Moderate duration (Fingerprint generation and KNN on 10k rows is fast).
 - Training: Nested CV on 3k rows with 200 trees is <2 hours.
 - SHAP: ~ min for a moderate dataset size.
 - **Total**: Well within limits.

## 4. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Stratified Sampling** | Ensures representativeness of composition families, avoiding selection bias inherent in random sampling. |
| **OC20 Only** | Removes dependency on unverified sources, ensuring reproducibility and data availability. |
| **Structure-based KNN** | Captures local surface coordination better than stoichiometry-based KNN, improving imputation validity. |
| **Nested Cross-Validation** | Prevents selection bias in hyperparameter tuning, ensuring valid statistical comparison (FR-005). |
| **DFT Target** | Uses available ground truth (`energy_change`) instead of missing experimental data. |

## projects/PROJ-170-predicting-catalytic-activity-from-elect/specs/001-predicting-catalytic-activity-from-elect/data-model.md