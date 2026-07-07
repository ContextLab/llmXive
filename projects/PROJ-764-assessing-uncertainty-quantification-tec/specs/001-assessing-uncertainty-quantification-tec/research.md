# Research: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## 1. Problem Statement
The goal is to evaluate the efficacy of three lightweight Uncertainty Quantification (UQ) techniques—Deep Ensembles, Monte-Carlo Dropout, and Sparse Gaussian Processes—in predicting material properties (formation energy) from the **Open Quantum Materials Database (OQMD)**. The evaluation focuses on calibration accuracy (ECE, Interval Score) and practical utility in downstream high-throughput screening (precision at fixed recall).

## 2. Dataset Strategy

### 2.1 Target Dataset
The project targets the **OQMD Formation Energy** dataset.
- **Source**: `oqmd/formation-energy` (HuggingFace Datasets).
- **Features**: Compositional features (element fractions, atomic properties).
- **Target**: Formation energy (eV/atom).
- **Rationale**: This dataset is publicly accessible via a verified programmatic loader, requires no API key, and provides the necessary target property for material stability analysis.

### 2.2 Verified Sources & Access
**Verified Source**:
- **Dataset**: `oqmd/formation-energy`
- **URL**: `https://huggingface.co/datasets/oqmd/formation-energy`
- **Loader**: `datasets.load_dataset("oqmd/formation-energy")`
- **Access**: Public, no authentication required.

**Constraint**: The pipeline will strictly use this verified source. If the source is unreachable, the pipeline will fail with error code `SOURCE_UNREACHABLE` and a clear message: "OQMD dataset source unreachable. Please check network connectivity." No local file fallback is permitted to ensure reproducibility (Constitution Principle I).

### 2.3 Data Preprocessing
- **Missing Data**: Rows with missing formation energy will be excluded. A `validation_report.json` will log the count and names of missing variables (FR-010).
- **Feature Engineering**:
  - Composition: Elemental property averages (e.g., atomic radius, electronegativity).
  - **Global PCA**: PCA will be applied to the full training set to reduce features to a lower-dimensional representation. **This reduced feature set will be used for ALL three methods (NN, Ensemble, GP)** to ensure a fair comparison and avoid confounding variables (dimensionality reduction).
  - **Standardization**: Features will be standardized (zero mean, unit variance) using the training set statistics.

## 3. Methodology

### 3.1 Baseline Model (FR-002)
- **Architecture**: Feed-forward Neural Network (FFNN).
- **Layers**: 2 hidden layers.
- **Parameter Limit**: ≤ 10,000 parameters.
- **Output**: **Heteroscedastic** (outputs two values: mean $\mu$ and log-variance $\log(\sigma^2)$).
- **Activation**: ReLU.
- **Loss Function**: Negative Log Likelihood (NLL) for Gaussian regression: $L = \frac{1}{2} \log(\sigma^2) + \frac{(y - \mu)^2}{2\sigma^2}$.
- **Split**: 80/10/10 (Train/Val/Test), seed=42.
- **Optimizer**: Adam (learning rate tuned via Val set).
- **Rationale**: Heteroscedastic loss is required to validly separate aleatoric uncertainty (modeled by $\sigma^2$) from epistemic uncertainty (modeled by ensemble variance).

### 3.2 UQ Techniques

#### A. Deep Ensembles (FR-003)
- **Method**: Train multiple independent models with different random initializations using the heteroscedastic loss.
- **Prediction**: Mean of 5 means ($\bar{\mu}$).
- **Epistemic Variance**: Variance of the 5 means.
- **Aleatoric Variance**: Mean of the 5 predicted variances ($\bar{\sigma^2}$).
- **Total Variance**: Epistemic + Aleatoric.
- **Rationale**: Proven to capture epistemic uncertainty effectively; computationally feasible for small networks on CPU.

#### B. Monte-Carlo Dropout (FR-004)
- **Method**: Enable dropout (p=0.2) during inference.
- **Sampling**: 30 stochastic forward passes per sample.
- **Prediction**: Mean of 30 predictions.
- **Variance**: Variance of the 30 predictions (Total Predictive Variance).
- **Decomposition**: Since standard MC-Dropout with homoscedastic loss does not output per-sample variance, this method will report **Total Predictive Variance** only. The aleatoric/epistemic split is marked as "N/A" for this method to avoid invalid decomposition.
- **Rationale**: Approximates Bayesian inference with minimal code changes; efficient on CPU.

#### C. Sparse Gaussian Process (FR-005)
- **Method**: Sparse Variational GP (SVGP) using GPyTorch.
- **Inducing Points**: 500.
- **Input**: PCA-reduced features (20 components, **same as NN**).
- **Variance**: Predictive variance from the GP posterior.
- **Decomposition**: Reports **Total Variance** (proxy).
- **Rationale**: Provides a non-parametric baseline; PCA ensures dimensionality is manageable for CPU-based GP inference.

### 3.3 Evaluation Metrics (FR-006, SC-001)
- **Expected Calibration Error (ECE)**:
  - **Binning Strategy**: Samples are binned by **predicted uncertainty quantiles** (equal-frequency bins of the predictive standard deviation).
 - **Calculation**: For each bin, compute the empirical coverage (fraction of true values within the predicted interval) vs. the nominal coverage ([deferred] or [deferred]). ECE is the weighted average of the absolute difference.
- **Interval Score**: Combines sharpness (width) and calibration (coverage penalty).
- **Sharpness**: Mean interval width.
- **Uncertainty Decomposition**:
  - Deep Ensemble: Valid split (Epistemic + Aleatoric).
  - MC-Dropout/GP: Total Variance only (no split).

### 3.4 Downstream Screening (FR-007, SC-003)
- **Task**: Select stable materials (low formation energy).
- **Metric**: Precision at fixed recall (e.g., [deferred] of stable materials).
- **Method**:
  - **Baseline**: Rank candidates by point prediction (lowest energy first).
  - **UQ Method**: Rank candidates by **Expected Loss** = Prediction + $k \times$ Variance (where $k$ is a risk-aversion parameter).
  - **Comparison**: Compare the precision of the top-K candidates selected by each method. This measures the utility of uncertainty in *ranking*, avoiding the tautology of interval thresholding.

## 4. Statistical Rigor & Feasibility

### 4.1 Computational Feasibility (CPU-Only)
- **Constraints**: 2 CPU cores, 7 GB RAM, 5-hour limit.
- **Mitigation**:
  - Small NN (≤10k params) ensures fast training (<30 mins).
  - Sparse GP with 500 inducing points reduces O(N^3) to O(N*M^2).
  - 5-ensemble training is parallelizable or sequential within the 5-hour budget.
  - **No GPU**: All libraries (PyTorch, GPyTorch) configured for CPU.

### 4.2 Statistical Considerations
- **Multiple Comparisons**: When comparing 3 methods across multiple metrics, a **Holm-Bonferroni correction** will be applied to all pairwise p-values to control the Family-Wise Error Rate (FWER).
- **Significance Testing for ECE**: To determine if the difference in ECE between methods is significant, a **bootstrap paired t-test** (1000 resamples) will be used to construct 95% confidence intervals for the difference in ECE. The null hypothesis is that the difference is zero.
- **Power Analysis**: Given the dataset size (N), the study will calculate the **Minimum Detectable Effect (MDE)** for a [deferred] precision improvement. If N is too small to detect this effect with 80% power at alpha=0.05, the study will report the MDE and frame the screening results as "exploratory" rather than confirmatory.
- **Causal Claims**: The study is observational (predictive modeling). Claims will be framed as "associational" or "predictive utility," not causal.
- **Collinearity**: Elemental features are often correlated. PCA (applied globally) and regularization (for NN) mitigate this. Independent effects of highly collinear features will not be claimed.

## 5. Risks & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Unavailable** | High (Pipeline fails) | Strict error handling; fail with `SOURCE_UNREACHABLE`; no URL fabrication. |
| **GP Non-Convergence** | Medium (One method fails) | Fallback: Log warning, exclude GP from ranking, proceed with Ensemble/MC-Dropout only. |
| **Runtime Exceeds 5h** | High (CI Failure) | Hard timeout in `main.py` for entire pipeline; aggressive parameter tuning. |
| **Memory Overflow** | High (Crash) | Batch processing; stream data; limit dataset size to fit 7 GB. |

## 6. References
- Gal, Y., & Ghahramani, Z. (2016). Dropout as a Bayesian Approximation.
- Lakshminarayanan, B., et al. (2017). Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles.
- Hensman, J., et al. (2015). Scalable Variational Gaussian Process Classification.
- OQMD Dataset: https://huggingface.co/datasets/oqmd/formation-energy