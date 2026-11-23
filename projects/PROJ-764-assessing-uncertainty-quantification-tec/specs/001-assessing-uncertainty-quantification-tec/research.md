# Research: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## 1. Research Question & Hypothesis

**Primary Question**: How accurately do Deep Ensembles, Monte-Carlo Dropout, and Sparse Gaussian Processes capture predictive uncertainty for material property prediction, and does the best-performing method improve downstream screening precision compared to random selection?

**Hypothesis**: Deep Ensembles will provide the most reliable epistemic uncertainty estimates (lowest ECE) due to diverse initialization, while Sparse GPs will offer the best calibration for aleatoric uncertainty in low-data regimes. Both will significantly outperform random selection in downstream screening tasks (US-3).

## 2. Dataset Strategy

### Verified Datasets
The project relies on the **OQMD (Open Quantum Materials Database)** subset, which contains compositional and structural features alongside target properties (formation energy, bulk modulus, band gap).

* **Source**: Hugging Face Datasets (verified via web search).
* **Access Method**: `datasets.load_dataset("kjappelbaum/chemnlp-oqmd")` (or specific parquet URLs provided in the verified block).
* **Variables Required**:
 * *Predictors*: Elemental composition (fractional), structural descriptors (atomic radius, packing fraction).
 * *Targets*: Formation energy, Bulk modulus, Band gap.
* **Feasibility Check**: The verified URLs point to parquet/CSV files that can be streamed or downloaded. The dataset size is estimated to be within the available RAM limit if sampled or streamed. If the full dataset exceeds memory, the plan uses `streaming=True` and a fixed random sample (e.g., a representative subset of rows) to ensure the 5-hour runtime.

**Critical Data Note**: The raw OQMD dataset does **not** contain pre-calculated "atomic radius" or "packing fraction". The `preprocess.py` script **must** parse the crystal structure (CIF) provided in the dataset and compute these descriptors using `pymatgen` before training.

**Dataset Strategy Table**:

| Dataset | Verified URL | Load Method | Variables Used | Feasibility Note |
|:--- |:--- |:--- |:--- |:--- |
| OQMD Subset | ` (and related parquet) | `datasets.load_dataset` (Hugging Face) or direct `pandas.read_parquet` | Formation Energy, Bulk Modulus, Band Gap, Composition, Structure | **Feasible**: Parquet format is efficient. Streaming enabled if >7GB. Missing structural descriptors will be computed via `pymatgen`; if CIF is missing, rows are excluded and logged in `validation_report.json` (FR-010). |
| *None* | *N/A* | *N/A* | *N/A* | *No other datasets required. All variables are present or derivable from OQMD.* |

**Data Availability Note**: The spec mentions "OQMD-Subset" but the verified block states "NO verified source found" for a specific "OQMD-Subset" URL. However, the verified block *does* list specific OQMD URLs (kjappelbaum, materials-toolkits, jablonkagroup). The plan will use the **kjappelbaum** or **jablonkagroup** URLs as they are verified and contain the necessary OQMD data. The plan does **not** invent a new URL.

## 3. Methodology & Statistical Rigor

### 3.1 Baseline Model (FR-002)
* **Architecture**: Feed-Forward Neural Network (FFNN).
* **Layers**: Input -> Hidden 1 (ReLU) -> Hidden 2 (ReLU) -> Output (Linear, 2 units: mean, log_var).
* **Parameter Constraint**: Total parameters ≤ 10,000.
 * *Calculation*: If input dim = 20, hidden1 = 100, hidden2 = 50, output = 2.
 * Params = (20*100 + 100) + (100*50 + 50) + (50*2 + 2) = 2100 + 5050 + 102 = 7252. (Fits).
* **Loss Function**: Heteroscedastic MSE: `L = 0.5 * (exp(-log_var) * (y - y_hat)^2 + log_var)`.
 * This allows the model to learn both the mean prediction and the aleatoric uncertainty (variance).
 * **Output**: `y_hat` (mean), `log_var` (log variance). Aleatoric variance = `exp(log_var)`.
* **Training**: 80/10/10 split (**Material-ID Stratified** by formation energy quantiles). Seed=42.
* **Output**: `y_hat` (mean), `log_var` (log variance). Aleatoric variance = `exp(log_var)`.

### 3.2 UQ Techniques
1. **Deep Ensembles (FR-003)**:
 * Train multiple independent models with different random seeds.
 * **Epistemic**: Variance of the 5 predicted means.
 * **Aleatoric**: Mean of the 5 predicted variances (`exp(log_var)`).
 * *Output*: Mean prediction, Total Variance (Epistemic + Aleatoric).

2. **Monte-Carlo Dropout (FR-004)**:
 * Enable dropout (p=0.2) during inference.
 * **Passes**: 10,000 stochastic forward passes per sample (per verified fact 2007.03293).
 * **Output**: Mean of 10,000 passes, Variance of 10,000 passes.
 * **Uncertainty Decomposition**:
 * Epistemic: Variance of the means.
 * Aleatoric: Mean of the predicted variances (`exp(log_var)`).
 * *Note*: With heteroscedastic loss, MC-Dropout captures both aleatoric and epistemic uncertainty.

3. **Sparse Gaussian Process (FR-005)**:
 * **Preprocessing**: PCA on training features to reduce dimensionality (retain >90% variance).
 * **Inducing Points**: 200 inducing points (random subset of training data).
 * **Kernel**: RBF (Matern 5/2 alternative if needed).
 * **Output**: Predictive mean and variance.
 * **Reconstruction Variance**: The variance explained by the PCA reconstruction is reported as a separate metric (FR-005).
 * *Uncertainty Type*: Total variance (aleatoric + epistemic).
 * **Fallback**: If Sparse GP fails to converge, the system falls back to a **Standard GP** on a smaller subset (N=2000) to ensure the GP baseline is retained. If even that fails, the run is marked "partial" but Ensemble/MC-Dropout results are still reported.

### 3.3 Calibration & Evaluation (FR-006, FR-008)
* **Metrics**:
 * **Expected Calibration Error (ECE)**: Binned reliability (bins). **Binning Strategy**: Samples are binned by their **predicted uncertainty quantiles** (interval width or standard deviation) to ensure fair comparison across methods.
 * **Interval Score**: Winkler score for 50% (alpha=0.5) and 90% (alpha=0.1) intervals.
 * **Sharpness**: Mean interval width.
 * **Robustness (SC-004)**: Coefficient of Variation (CV) of ECE scores across multiple seeds (42, 43, 44) for each method.
* **Uncertainty Separation**:
 * *Ensemble*: Explicitly calculate Epistemic (Var(E[μ])) and Aleatoric (E[σ²]).
 * *MC-Dropout*: Explicitly calculate Epistemic and Aleatoric using the heteroscedastic output.
 * *GP*: Report Total variance.
* **Multiple Comparisons**: Since we compare 3 methods on multiple metrics, we will report the metrics directly. If a statistical test is needed (e.g., for screening precision), we will apply Bonferroni correction if >1 test is run on the same data.

### 3.4 Downstream Screening (FR-007)
* **Task**: Select stable perovskites (threshold on formation energy).
* **Method**: Filter candidates where the 90% confidence interval is below the stability threshold.
* **Baseline**: Random selection of the same number of candidates.
* **Metric**: Precision at fixed recall (e.g., [deferred] of stable materials retained).
* **Significance**: **Bootstrap Permutation Test** (1000 iterations) on the precision difference. This is statistically valid for comparing continuous precision metrics. McNemar's test is rejected as it is for paired nominal data.
* **Hypothesis**: UQ-filtered precision > Random precision (p < 0.05).

## 4. Compute Feasibility & Runtime Strategy

* **CPU-First**: All models are small (≤10k params, 200 inducing points). Training will be done on CPU using `torch` (no CUDA).
* **Memory Management**:
 * Dataset streamed via `datasets` library.
 * PCA fitted on training set only.
 * Sparse GP uses inducing points to limit O(N^3) complexity.
* **Runtime Budget**:
 * Total limit: hours.
 * Deep Ensemble (multiple models): [deferred] (sequential).
 * MC-Dropout: ~ mins (10,000 passes * inference time).
 * Sparse GP: Moderate duration (optimization + inference).
 * Evaluation: A dedicated time slot is allocated for the evaluation phase.
 * **Buffer**: 2+ hours for retries and overhead.
* **GPU Escape Hatch**: Not required for this plan. If the Sparse GP fails to converge on CPU due to numerical instability, the fallback is a Standard GP on a smaller subset (N=2000) or proceeding with only Ensemble/MC-Dropout results, as per the "fallback" logic in the spec.

## 5. Risk Mitigation

* **Missing Data**: Rows with missing CIFs or structural descriptors are excluded; `validation_report.json` logs the count (FR-010).
* **GP Convergence**: If Sparse GP optimization fails, the system falls back to Standard GP (N=2000). If that fails, the run is marked "partial".
* **Timeout**: A hard timeout (5h) is enforced in `main.py`. If exceeded, the pipeline fails with a clear error code.
* **Fabrication Prevention**: No synthetic data. All results derived from the verified OQMD subset. All metrics are computed from real predictions.