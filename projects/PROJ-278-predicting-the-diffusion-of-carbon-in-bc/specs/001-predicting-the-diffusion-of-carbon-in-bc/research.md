# Research: Predicting the Diffusion of Carbon in BCC Metals from Compositional Data

## Scientific Context

The diffusion of carbon in BCC metals (e.g., ferrite, $\alpha$-Fe) is a critical kinetic process in steel metallurgy. While temperature and composition are primary drivers, microstructural features (grain boundaries, dislocations) introduce significant variance. This project isolates the **compositional** component by strictly excluding microstructural descriptors, aiming to quantify the "upper bound" of predictability achievable from bulk chemistry alone.

## Dataset Strategy

The project relies on verified HuggingFace datasets that mirror the NIST and Materials Project data. Per the "Verified datasets" block, only the following URL is permissible.

| Dataset Name | Source Description | Verified URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **MeLiDC (BCC)** | Mirror of Materials Project / NIST diffusion data (BCC subset) | ` | Primary source for diffusion coefficients and composition. |

**Critical Note on Dataset Availability**:
The only verified, reachable dataset relevant to the scientific domain (BCC diffusion) is the `MeLiDC` parquet file. If this dataset lacks the necessary fields (temperature, structure tags, provenance flags), the pipeline will halt with a `DataInsufficientError`. No alternative URLs are used to maintain reproducibility (Constitution Principle I).

### Data Loading Strategy
1. **Download**: Fetch `MeLiDC` parquet directly via `pandas.read_parquet()` from the verified URL.
2. **Validation**: Immediately check for `BCC` structure tags, Carbon presence, and the existence of `microstructure_controlled` or `single_crystal` flags.
3. **Fallback**: If `MeLiDC` yields < 30 valid entries OR lacks required metadata fields, the pipeline halts with `DataInsufficientError` and logs the specific count and missing fields.

## Feature Engineering Strategy

To satisfy **FR-002**, the following descriptors will be computed from atomic fractions and temperature:
1. **Atomic Radius Variance**: $\sigma_r = \sqrt{\sum x_i (r_i - \bar{r})^2}$
2. **Valence Electron Concentration (VEC)**: $\sum x_i v_i$
3. **Electronegativity Spread**: $\sigma_\chi = \sqrt{\sum x_i (\chi_i - \bar{\chi})^2}$
4. **Mixing Entropy**: $-\sum x_i \ln x_i$
5. **Inverse Temperature**: $1/T$ (to capture Arrhenius behavior, addressing methodology concern c2f82964).

*Source of atomic properties*: `pymatgen` periodic table data (embedded in `pymatgen` library).

## Statistical Rigor & Methodology

### Model Selection (FR-004)
- **Random Forest**: Captures non-linear interactions.
- **XGBoost**: High performance gradient boosting.
- **Elastic Net**: Linear baseline with regularization.
- **Constraint**: Grid search limited to 15 combinations to fit CPU constraints.

### Hypothesis Testing (FR-005, SC-002)
- **Permutation Test**: 10,000 iterations to compare ML model $R^2$ vs. Linear Baseline (Elastic Net).
- **Null Hypothesis**: The ML model does not outperform a physically justified log-linear (Arrhenius) baseline.
- **Significance Level**: $\alpha = 0.05$.
- **Correction**: No multiple comparison correction needed for the primary $R^2$ comparison, but if multiple features are tested for significance, Bonferroni correction will be applied.

### Power & Sample Size
- **Assumption**: The dataset contains > 30 samples.
- **Action**: If $N < 30$, the system falls back to Leave-One-Out Cross-Validation (LOOCV) and uses Bootstrap resampling (1,000 iterations) to estimate confidence intervals for $R^2$ and RMSE, ensuring statistical robustness even with sparse data (addressing methodology concern 3047028a).

### Causal vs. Associational
- **Assumption**: The data is observational.
- **Interpretation**: All $R^2$ and feature importance results are interpreted as **associational**. No causal claims of "composition causes diffusion changes" will be made; rather, "composition predicts diffusion."

### Microstructural Gap Definition
The "microstructural gap" is defined as the residual variance ($1 - \text{adjusted } R^2$) of the composition-only model. **Crucially**, this residual includes measurement error, missing compositional descriptors, and microstructural effects. It is **not** a pure proxy for microstructure, but an upper bound on the variance explainable by composition alone (addressing scientific soundness concern 1a08de0b).

## Compute Feasibility

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM).
- **Memory**: Data subset to < 500MB. `pandas` operations are in-memory.
- **Time**: Grid search (15 combos) + SHAP (on test set) estimated at < 2 hours.
- **Libraries**: `scikit-learn`, `xgboost` (CPU build), `shap` (CPU mode). No CUDA dependencies.

## Risk Mitigation

| Risk | Mitigation |
|:--- |:--- |
| **Dataset Unreachable** | Only use `MeLiDC` URL. If it fails or lacks schema, raise `DataInsufficientError`. |
| **Insufficient Samples** | Check $N$ immediately after loading. If $N < 30$, switch to LOOCV + Bootstrap. |
| **Microstructural Contamination** | Strict exclusion of entries missing `microstructure_controlled` or `single_crystal` flags (fail-safe). |
| **Numerical Instability** | Log-transform $D$ immediately. Include `1/T` to handle Arrhenius scaling. |
| **Single Source Failure** | If `MeLiDC` is incomplete, the project halts. No unverified fallbacks are used to preserve reproducibility. |