# Research: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Dataset Strategy

The project relies on the Open Quantum Materials Database (OQMD). The specification mentions an "OQMD-Subset" which has **no verified source** in the project metadata. To ensure feasibility on the GitHub Actions runner, this plan uses the **verified** OQMD sources available via Hugging Face.

| Dataset Name | Source URL (Verified) | Format | Usage |
|:--- |:--- |:--- |:--- |
| **OQMD Structural** | `https://huggingface.co/datasets/materials-toolkits/oqmd` | Parquet/CIF | Primary source for composition, structure (unit cell), and targets. |
| **OQMD Targets** | ` | CSV | Backup for targets if structural data is missing. |

**Dataset Variable Fit & Gap Analysis**:
- **Required Variables**: Formation Energy, Bulk Modulus, Band Gap, Composition (element fractions), Structural Descriptors (Atomic Radius, Packing Fraction).
- **Gap Handling**:
 - **Atomic Radius**: Computed from element properties if not present.
 - **Packing Fraction**: Computed from unit cell parameters (a, b, c, alpha, beta, gamma) and atomic radii. **Crucially**, if unit cell data is missing for a row, that row is **excluded** (cannot compute packing fraction from composition alone).
 - **Target Validity**: Rows with null values in *any* of the three target properties (formation energy, bulk modulus, band gap) are excluded.
- **Access**: All selected sources are public, programmatic, and do not require API keys or registration, satisfying the "open data" constraint for CI runners.
- **Streaming**: If the total dataset size exceeds ~5GB, `datasets.load_dataset(..., streaming=True)` will be used to iterate and filter rows on-the-fly, avoiding full RAM load.

## Methodology & Statistical Rigor

### 1. Baseline Model & UQ Techniques
- **Baseline NN**: 2 hidden layers, ReLU activation, total parameters ≤ 10,000.
 - **Output Head**: Dual output (Mean + Log-Variance) to support heteroscedastic regression.
 - **Loss Function**: Negative Log Likelihood (NLL) assuming Gaussian noise. This enables the decomposition of uncertainty.
- **Deep Ensembles (DE)**: 5 independently trained models.
 - **Epistemic**: Variance of the means across ensemble members.
 - **Aleatoric**: Mean of the predicted variances across ensemble members.
- **MC Dropout**: Dropout rate p=0.2 enabled during inference. 30 stochastic passes per sample.
- **Sparse GP**: Input features reduced to 20 components via PCA (fitted on train set). 500 inducing points. Kernel: RBF.

### 2. Calibration Metrics (FR-006)
- **Expected Calibration Error (ECE)**: For regression, defined as the weighted average of the absolute difference between the nominal confidence level (e.g., 0.9) and the empirical coverage rate (fraction of true values falling within the predicted interval) across 10 bins of predicted interval width.
- **Interval Score (Winkler)**: Penalizes both width (sharpness) and coverage errors.
 - $\alpha = 0.1$ (90% interval)
 - $\alpha = 0.5$ (50% interval)
- **Sharpness**: Mean interval width.

### 3. Downstream Screening (US-3)
- **Task**: Select stable materials (Formation Energy < Threshold).
- **Filter**: Select only candidates where the UQ interval is narrow (high confidence) and below threshold.
- **Baseline**: **Point Estimate Baseline** (selecting top-K candidates by predicted mean *without* uncertainty filtering). This isolates the value of the UQ intervals compared to a standard model.
- **Metric**: Precision at fixed Recall of **0.8**.
- **Statistical Test**: **Bootstrap Confidence Interval**. We will generate a sufficient number of bootstrap resamples of the test set to compute the difference in precision between the UQ-filtered method and the Point Estimate Baseline. If the 95% CI does not include 0, the difference is significant (p < 0.05).

### 4. Robustness & Power (SC-004)
- **Seeds**: 42, 43, 44.
- **Stability**: Coefficient of Variation (CV) of ECE across seeds. CV > 0.1 triggers instability flag.
- **Power**: If the full OQMD exceeds the 5h budget, a **stratified random sample of [deferred] rows** will be used. This sample is drawn by sorting the data by the target variable (formation energy) and selecting rows to match the distribution of the full set, avoiding the "first N" bias.

## Compute Feasibility & Escape Hatch

- **CPU-First Strategy**:
 - All models are designed for CPU execution.
 - NN: Small architecture (≤10k params) ensures fast training (<30 mins).
 - Sparse GP: 500 inducing points + PCA reduction ensures $O(M^3)$ cost is manageable ($500^3 \approx 1.25 \times 10^8$ ops, feasible in minutes).
 - MC Dropout: Multiple passes per sample is computationally cheap for a small NN.
- **No GPU Required**: The plan does **not** require the Kaggle GPU escape hatch. The "lightweight" constraints (FR-002, FR-005) are specifically chosen to fit the GitHub Actions free-tier (2 CPU, 7 GB RAM).
- **Timeout Enforcement**: `main.py` will wrap the entire pipeline in a `signal`-based timeout (5 hours). If exceeded, it logs a clear error and terminates.

## Decision/Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use Verified OQMD Sources** | Spec's "OQMD-Subset" has no verified URL. Using `materials-toolkits/oqmd` ensures the data is actually downloadable on CI. |
| **PCA before Sparse GP** | GPyTorch Sparse GP scales poorly with high dimensions. Reducing to 20 components ensures convergence within the 5h budget. |
| **3 Seeds for Robustness** | Required by SC-004 to distinguish method performance from random initialization artifacts. |
| **Strict 5h Timeout** | Required by FR-009 and Constitution Principle VI to ensure CI compatibility. |
| **No Synthetic Data** | The plan uses real OQMD data. If the full set is too large, a real stratified sample is taken, not a synthetic stand-in. |
| **Heteroscedastic NN** | Required to compute Aleatoric uncertainty as defined in FR-008. |
| **Bootstrap CI** | Required for valid statistical comparison of disjoint samples (UQ vs. Point Estimate). |
| **Fixed Recall 0.8** | Explicitly defined to resolve SC-003 ambiguity. |