# Research: Assessing Dataset Imbalance Effects on Materials Property Predictions

## 1. Problem Statement
Materials science datasets (OQMD, AFLOW) exhibit severe imbalance in both compositional space (certain elements/structures are over-represented) and target property distributions (formation energies cluster around stable values). This research quantifies how this imbalance degrades predictive accuracy for under-represented regions (minority subsets) and distorts feature importance rankings derived from SHAP analysis.

## 2. Dataset Strategy

### Verified Datasets
The implementation relies exclusively on the following verified sources. No other URLs are used.

| Dataset | Source URL (Verified) | Format | Usage |
| :--- | :--- | :--- | :--- |
| **OQMD** | `https://huggingface.co/datasets/oqmd/oqmd-structural/resolve/main/oqmd_structural.parquet` | Parquet | Primary source for formation energy, bulk modulus, and crystal structures (compositions). |
| **AFLOW** | `https://huggingface.co/datasets/aflow-ml/aflow-ml/resolve/main/aflow_structural.parquet` | Parquet | Primary source for bulk modulus, band gap, and formation energy (structural data). |
| **Materials Project** | *Not in verified list* | N/A | **Fallback Only**: If API keys are present, data is fetched via API. If not, scope restricts to OQMD+AFLOW (FR-008). |

### Data Acquisition & Feasibility
- **Download Strategy**: Use `huggingface_hub` or `requests` with exponential backoff (FR-007) to fetch files.
- **Size Management**: The spec caps total data at a finite limit. If the raw download exceeds this, the ingestion script will sample rows (random seed fixed) to fit the constraint while preserving distribution.
- **Feasibility**: OQMD and AFLOW are open-access via Hugging Face. No credentials are required for these specific verified URLs.
- **Gap Handling**: If a specific target property (e.g., bulk modulus) is missing from the merged dataset or has <100 samples, the system logs a warning and skips that property (Edge Case).

## 3. Methodology

### 3.1 Feature Engineering (FR-002)
- **Descriptors**: Magpie compositional descriptors computed for every entry.
- **Normalization**: L2-normalization applied.
- **Compositional Coverage Score (ImbalanceScore)**: Replaces the invalid Gini-of-K-Means metric. Calculated as the **Volume of the Convex Hull** of the dataset in the 14D Magpie space, normalized by the volume of the convex hull of the *full* OQMD/AFLOW reference space. Additionally, a **Nearest-Neighbor Density** metric is computed to capture local sparsity. This measures actual chemical diversity coverage.
- **TargetImbalanceScore**: Gini coefficient of the target property distribution (e.g., formation energy).

### 3.2 Baseline Modeling (FR-004)
- **Models**: Random Forest (RF) and Gradient Boosting (GB).
- **Training**: On native, skewed data.
- **Evaluation**: Stratified test set preserving original imbalance. Metrics: MAE, RMSE, R².
- **Minority Subset**: Defined as the bottom [deferred] (e.g., lowest [deferred] or [deferred]) of the target distribution. Performance is evaluated specifically here.

### 3.3 Resampling Strategy (FR-003)
- **Primary**: **Stratified Undersampling** using equal-frequency binning (20 bins) to reduce over-represented regions while preserving the natural thermodynamic distribution.
- **Constraint**: The goal is to reduce the majority class size, not force a uniform distribution (which violates physics).
- **Fallback**: If undersampling results in bins with <100 samples (Minimum Sample Check) or >20% data loss:
  1. Switch to **Cost-Sensitive Learning** (class weights) to penalize errors on minority regions without altering data distribution.
  2. **SMOTE is explicitly excluded** as it generates chemically impossible compositions via interpolation.
- **Re-training**: Models retrained on balanced (undersampled) or cost-sensitive weighted data.

### 3.4 Statistical Validation (FR-005, FR-015)
- **Power Analysis**: Determine minimum number of random seeds to detect medium effect size (Cohen's d = 0.5) with Power ≥ 0.8, α = 0.05.
- **Significance Test**: Paired t-test or Wilcoxon signed-rank test comparing MAE of skewed vs. balanced models on the minority subset.
- **Minimum Sample Check**: If the minority subset in the test set has <100 samples, the statistical test is skipped, and the result is reported as "Insufficient Power" to avoid Type II errors.
- **Correlation**: Pearson/Spearman correlation between Compositional Coverage Score and performance degradation (FR-012). *Note: This measures association, not causation.*

### 3.5 SHAP Distortion Audit (FR-006, FR-014)
- **Ground Truth**: Generate a **non-linear synthetic dataset** with known feature weights and **physical constraints** (charge balance, stoichiometry rules) to mimic real materials physics.
- **Comparison**: Rank top-10 features for skewed vs. balanced models.
- **Metric**: Mean rank shift. Validate against synthetic ground truth to distinguish "bias correction" from "distortion".

## 4. Compute Feasibility & Constraints

### CPU-First Strategy
- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Method**: All models (RF, GB) are CPU-tractable. SHAP (TreeExplainer) is optimized for CPU.
- **Data Streaming**: If the merged dataset exceeds RAM, `pandas` chunking or `datasets` streaming is used to compute statistics online, avoiding full load.
- **No GPU Needed**: No deep learning or large transformer models are planned.

### Memory Management
- **Limit**: 7 GB RAM.
- **Mitigation**: 
  - Sample large datasets to 5 GB cap.
  - Process SHAP on a subset of test data if full set is too large.
  - Use `joblib` for parallelism with `n_jobs=2` (matching runner cores).

## 5. Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **API Rate Limits** | Exponential backoff (5 retries) implemented in `ingestion.py`. |
| **Missing Target Properties** | System skips property if <100 samples; logs warning; excludes from ImbalanceScore. |
| **Resampling Failure** | Automatic fallback to Cost-Sensitive Learning if undersampling bins are too small. SMOTE is excluded. |
| **SHAP Instability** | Use `TreeExplainer` (exact) for RF/GB; validate against non-linear synthetic ground truth. |
| **Data Imbalance Too Severe** | If undersampling reduces data too much, report as "High Variance Risk" and rely on Cost-Sensitive Learning. |

## 6. Decision Rationale
- **Why Magpie?**: Standard in materials science; 14 features are sufficient for compositional descriptors without heavy dimensionality reduction.
- **Why RF/GB?**: Interpretable, CPU-efficient, and handle tabular data well. No need for GNNs which require GPU and complex preprocessing.
- **Why Convex Hull for Imbalance?**: Measures actual chemical space coverage (diversity) rather than clustering density, avoiding circular validation.
- **Why Cost-Sensitive over SMOTE?**: SMOTE generates chemically impossible compositions; Cost-Sensitive Learning preserves physical reality while correcting for imbalance.
- **Why Non-Linear Synthetic Data?**: Essential to prove that SHAP changes are due to data imbalance in a physics-like context, not just linear artifacts.