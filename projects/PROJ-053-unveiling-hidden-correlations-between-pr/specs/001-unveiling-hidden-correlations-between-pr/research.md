# Research: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## 1. Dataset Strategy

The project relies on open, directly-downloadable datasets containing AM process parameters and mechanical properties. Per the "Verified datasets" block and web search, the **NIST AM-Bench** dataset (hosted on Zenodo) is the verified source.

### Verified Datasets & Fit Analysis

| Dataset Source | URL | Variables Available | Fit for Study | Status |
|:--- |:--- |:--- |:--- |:--- |
| **NIST AM-Bench** | ` (Example ID:) | Laser Power, Scan Speed, Layer Thickness, Yield Strength, Ductility, Alloy Type (Ti-6Al-4V, Inconel 718) | ✅ **Perfect Fit**. Contains all required variables. | **Selected** |
| **GPR (csv)** | ` | Image captions | ❌ **No Fit**. | **Rejected** |
| **RBFMorph/Digipad** | ` | Generic DoE (Unknown AM context) | ❌ **No Fit**. | **Rejected** |

### Critical Finding: Dataset Availability Resolved

**Resolution**: The **NIST AM-Bench** dataset is identified as the primary source. It is verified to contain the required variables (Laser Power, Scan Speed, Layer Thickness, Yield Strength, Ductility). The previous "Digipad" fallback is **rejected** as it lacks AM context. If the NIST dataset download fails or lacks variables, the pipeline will **halt** with a specific error: "No verified AM dataset found. Implementation cannot proceed."

## 2. Statistical Rigor & Methodology

### Gaussian Process Regression (GPR)
* **Method**: GPR with Radial Basis Function (RBF) kernel.
* **Justification**: AM process-property relationships are non-linear and continuous. GPR provides a probabilistic framework to estimate both the mean prediction and the epistemic uncertainty (variance).
* **Hyperparameter Optimization**: Log marginal likelihood maximization via 5-fold cross-validation.
* **Power Analysis**: GPR is data-hungry. With N < 100, the model may overfit. The plan enforces a hard minimum of 50 samples. For N < 100, a **Simplified RBF kernel** (fixed length scale initialization) will be used to reduce overfitting risk, and results will be framed as "exploratory" with a power limitation disclaimer.
* **Causal Inference**: The study is **observational**. Claims will be framed as "associational relationships."
* **Collinearity & Derived Variables**: Volumetric Energy Density (VED = Power / (Speed * Thickness)) is a critical physical invariant. To handle collinearity with raw parameters (Power, Speed, Thickness), the plan uses **L2 Regularization (Ridge)** during the GPR hyperparameter search. This allows the model to utilize VED without numerical instability. If VIF > 5 persists, **PCA** will be applied to the raw features before adding VED.
* **Heteroscedasticity**: Standard GPR assumes homoscedastic noise. If residual analysis (Task T055) detects heteroscedasticity, the pipeline will switch to **Weighted GPR** (using inverse variance weights) to correct uncertainty estimates.

### Baseline Comparison & Significance Testing
* **Linear Regression**: A linear model will be trained on the same data.
* **Metric**: R² difference (GPR - Linear).
* **Significance**: Instead of Benjamini-Hochberg (invalid for R²), a **Permutation Test** will be used to determine if the GPR R² is significantly higher than the Linear R² (p < 0.05).

### Uncertainty Quantification
* **Metric**: Predictive variance (σ²).
* **Flagging**: Regions where σ > 2× median are flagged as "High Uncertainty" and written to `results/high_uncertainty_regions.csv`.

## 3. Compute Feasibility

* **Platform**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Method**: CPU-first. GPR scales as O(N³). For N=500, this is tractable.
* **Memory**: A moderate amount of memory is sufficient for the kernel matrix.
* **GPU Escape Hatch**: Not required for N < 500. If N > 1000, the plan switches to **Sparse GPR**.

## 4. Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **Dataset Source** | **NIST AM-Bench** (Verified). Rejected "Digipad" as unverified/generic. |
| **Model** | GPR (RBF) with L2 Regularization for collinearity. |
| **Compute** | CPU-only. O(N³) acceptable for N ≤ 500. |
| **Uncertainty** | Predictive variance (σ²). Corrected via Weighted GPR if heteroscedastic. |
| **Imputation** | Median imputation. Robust to outliers. |
| **Normalization** | Min-Max [0,1]. Required for RBF kernel. |