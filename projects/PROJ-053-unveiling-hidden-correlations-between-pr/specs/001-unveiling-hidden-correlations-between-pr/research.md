# Research: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## Summary
This research phase identifies valid data sources, validates the "Dataset-variable fit" for the required variables (Laser Power, Scan Speed, Layer Thickness, Yield Strength, Ductility), and selects the GPR methodology. It explicitly addresses the lack of a verified source for "AM-Machine-Learning" datasets and relies on available HuggingFace/UCI sources that match the feature requirements.

## Dataset Strategy

The plan prioritizes **OPEN, directly-downloadable datasets** that can be fetched via `datasets` library or direct CSV download on the CI runner.

| Dataset Name | Source Type | Verified URL (from block) | Variable Fit Check | Status |
|:--- |:--- |:--- |:--- |:--- |
| **HuggingFace: gproud/Cutout_Men_Standing** | HuggingFace (CSV) | ` | **FAIL**: Contains captioning data, not AM process parameters. | Rejected |
| **HuggingFace: guanine/gpra_c** | HuggingFace (CSV) | ` | **UNKNOWN**: Requires inspection. Likely unrelated to AM. | Rejected |
| **HuggingFace: guanine/gpra_d** | HuggingFace (CSV) | ` | **UNKNOWN**: Requires inspection. Likely unrelated to AM. | Rejected |
| **UCI: HAR / Shopper / DROP** | HuggingFace (CSV/Parquet) | ` (and others) | **FAIL**: Human Activity Recognition, Shopper, NLP. No AM parameters. | Rejected |
| **RBF: p2-rbf-kan-transformer** | HuggingFace (JSON) | ` | **FAIL**: Model results, not raw AM process data. | Rejected |
| **RBF: Digipad-dataset** | HuggingFace (CSV) | ` | **FAIL**: Synthetic DOE data, lacks empirical AM process logs (Laser Power, Yield Strength). | Rejected |
| **AM-Machine-Learning** | **NO VERIFIED SOURCE** | **N/A** | **FAIL**: Spec assumes existence, but "Verified datasets" block explicitly states "NO verified source found". | **Cannot be used** |

### Selected Dataset Strategy
Since the "AM-Machine-Learning" dataset has no verified source and the other listed datasets appear unrelated to Additive Manufacturing (AM) or lack the required physical variables, the implementation **MUST** rely on a **user-provided dataset**.

*Decision*: The `research.md` identifies that **no verified AM dataset exists in the provided list**.
*Action*: The implementation will:
1. Trigger the **Manual Fallback Protocol**:
 - Halt execution if no local file is found.
 - Require the user to provide a local CSV file (`data/raw/am_raw_data.csv`).
 - Require a `source_independence_log.txt` in `data/raw/` where the user manually confirms the separation of process and property data streams (Constitution VII).
 - Calculate a SHA256 checksum of the CSV and record it in `data/raw/checksum.txt`.
2. The spec's "Dataset-variable fit" assumption is addressed by this explicit check. If `fatigue_life` is missing (likely), the analysis is restricted to `yield_strength` and `ductility`.

**Revised Data Strategy for Implementation**:
The `code/data_loader.py` will be written to accept a **local path** or a **verified HuggingFace ID** as an argument. It will **not** attempt to download from an unverified Zenodo ID (as per the "Unresolved concerns" regarding T014B). The "Verified datasets" block serves as a whitelist for *automatic* attempts; if none match, manual input is required.

*Note*: If the user provides a local AM dataset (e.g., from a known repository like ` but not in the verified block), the system will load it locally. The "Verified datasets" block is strictly for *automated* CI downloads.

## Methodological Rigor

### Statistical Approach: Gaussian Process Regression (GPR)
- **Kernel**: Radial Basis Function (RBF) / Squared Exponential.
- **Justification**: Captures non-linear relationships between process parameters and mechanical properties (Constitution Principle VI).
- **Uncertainty**: Predictive variance (σ²) provides epistemic uncertainty estimates.
- **Multiple Comparisons**: Not applicable for regression R²/RMSE. For permutation importance (FR-006), p-values are not calculated; rankings are descriptive.
- **Sample Size**: GPR scales as O(N³). For N=500, CPU is feasible. For N>500, the plan includes a **Sparse GPR (FITC/VFE)** strategy to preserve information density, rejecting random subsampling.
- **Power Limitation**: Explicitly acknowledged that N=50 is the minimum (Spec Edge Case). Results for N<50 will not be generated. For N=50, the power to detect non-linear effects is low (<0.5 for medium effects), and results will be framed as **exploratory** with confidence intervals reported, rather than definitive claims.

### Power Analysis
- **Minimum Detectable Effect Size**: For N=50, the minimum detectable non-linear effect size (f²) with [deferred] power is approximately 0.4 (large). For N=100, it drops to ~0.2 (medium).
- **Implication**: With N=50, the model may fail to detect subtle non-linearities. Uncertainty estimates (σ) for small N may reflect model instability rather than true epistemic uncertainty. Results will be explicitly labeled "Exploratory" if N < 100.

### Causal Inference & Confounding
- **Observational Nature**: The datasets are observational (experimental records).
- **Associational Claims**: Claims will be framed as **associational**. "Higher laser power is associated with higher yield strength" rather than "causes". The project explicitly rejects causal claims.
- **Confounding**: Unmeasured variables (e.g., ambient temperature, specific machine calibration) may confound results. This is a limitation noted in the final report.

### Measurement Validity
- **Instruments**: Yield Strength and Ductility are standard mechanical test outputs (tensile testing).
- **Validation**: No specific instrument validation is needed as these are standard physical measurements. The focus is on data integrity (no leakage).

### Predictor Collinearity
- **Risk**: Laser Power and Scan Speed may be correlated in specific datasets (e.g., constant energy density).
- **Mitigation**: Variance Inflation Factor (VIF) will be calculated during preprocessing. If VIF > 5, the system will **automatically construct an "Energy Density" feature** (Power/Speed) and use it as the primary predictor, reducing collinearity while preserving the physical relationship.

### Hypothesis Testing & Null Results
- **Non-linearity Confirmation**: The plan does not treat the R² comparison as proof of non-linearity. Instead, it uses **Residual Analysis** (plotting residuals vs. fitted values) and a **Likelihood Ratio Test** between GPR and Linear models.
- **Null Result Definition**: If the GPR R² is not significantly better than the Linear Baseline (p > 0.05 via permutation test), the conclusion is explicitly "No significant non-linear correlation detected".
- **Baseline Validity**: If the user-provided baseline is identical to the model's ranking, the system flags this as "Circular Validation" and reports it as a limitation. **Updated**: SC-004 now uses internal stability analysis (re-sampling) instead of external literature baselines.

### Data Quality Protocol (User-Provided)
For user-provided datasets:
1. **Checksum Verification**: The system calculates SHA256 of the CSV and compares it to `data/raw/checksum.txt`.
2. **Source Independence Log**: The system checks for `data/raw/source_independence_log.txt`. If missing, the system halts with an error: "Source Independence Log missing. Please confirm separate data streams."
3. **Column Validation**: The system checks for required columns. If missing, it halts.
4. **Data Quality Checklist**: The system requires the user to confirm that the data is representative of the AM process being studied.

## Compute Feasibility

### CPU-First Strategy
- **Target**: 2 CPU cores, 7 GB RAM.
- **Method**:
 - Use `scikit-learn`'s `GaussianProcessRegressor` (optimized Cython backend).
 - Limit `n_restarts_optimizer` to 5 to reduce runtime.
 - Use `min_max` scaling to [0,1] to improve GPR convergence.
 - If N > 500, use **Sparse GPR (FITC/VFE)** to preserve information density. Random subsampling is explicitly rejected.
 - **Memory Check**: If `X` (N x P) requires > 4 GB RAM, the script will raise an error: "Dataset too large for CPU GPR. Please use Sparse GPR."

### GPU Escape Hatch
- **Trigger**: None. GPR is inherently CPU-bound for small N.
- **Method**: No GPU required. The "escape hatch" is **Sparse GPR** for N > 500.

## Risk Register

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No Verified AM Dataset** | High | System triggers Manual Fallback Protocol. User must provide local file and `source_independence_log.txt`. |
| **Dataset lacks Yield Strength** | High | Analysis restricted to available mechanical properties. Documented in report. |
| **GPR Memory Overflow (N>500)** | Medium | **Sparse GPR (FITC/VFE)** is used. Random subsampling is explicitly rejected. |
| **Collinearity** | Medium | VIF check. If high, construct "Energy Density" feature. |
| **Runtime > 6h** | High | Limit CV folds to a small number if N is small. Cap optimizer restarts. |
| **Memory Overflow** | High | `code/memory_profiling.py` runs before training. If memory > 7GB, system halts with recommendation to use Sparse GPR. |
