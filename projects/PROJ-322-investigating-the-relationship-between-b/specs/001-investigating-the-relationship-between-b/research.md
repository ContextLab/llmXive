# Research: Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

## Dataset Strategy

The project relies on longitudinal resting-state fMRI data for mTBI patients with associated cognitive scores. The following datasets have been verified for source reachability and format compatibility.

| Dataset Name | Description | Verified URL / Loader | Relevance to Spec | Status |
|:--- |:--- |:--- |:--- |:--- |
| **OpenNeuro (Parquet)** | fMRI data in FSLR64k space, suitable for graph analysis. | ` | Primary source for resting-state data. Must be filtered for mTBI subjects and longitudinal time points. | **Verified (fMRI only)** |
| **AAL Atlas (CSV)** | Atlas parcellation data for defining ROIs. | ` | Used to define brain regions for connectivity matrix calculation (FR-002). | **Verified** |
| **PCS (CSV)** | Post-Concussion Symptom Scale data (proxy for cognitive scores). | ` | **CRITICAL MISMATCH**: This dataset contains "song-request" data, not clinical PCS scores for mTBI. | **UNUSABLE** |
| **NIfTI (Gzip)** | Generic NIfTI images (NSCLC, test-nifti). | ` | Format verified, but content is lung cancer or synthetic test data, not mTBI. | **UNUSABLE** |

### Dataset Selection Rationale & Gap Analysis

1. **Primary Data Source**: The `openneuro-fslr64k` dataset is the only verified source containing fMRI data in a format compatible with the spec. However, the spec assumes the dataset contains **mTBI patients**, **longitudinal time points** (acute/chronic), and **clinical cognitive scores** (e.g., PCS).
 * **Gap Identification**: The provided "Verified datasets" block does not contain a verified URL for an mTBI-specific longitudinal clinical dataset with cognitive scores. The `PCS (CSV)` link points to music request data, not clinical scores.
 * **Action Plan**: The implementation will attempt to load the `openneuro-fslr64k` data. If the metadata within that dataset does not explicitly label subjects as mTBI or include cognitive scores, the pipeline will trigger the **Contingency Plan (FR-009)**.
 * **Contingency**: If the dataset lacks the required variables (mTBI label, cognitive scores), the system will:
 1. **HALT** scientific analysis.
 2. Switch to **Methodology Validation Mode** using locally generated synthetic data (clearly marked as such).
 3. Log the "Variable Fit Gap" explicitly in `data/results/gaps.json`.
 4. **No Verified Alternative Found**: There is currently no verified alternative source for mTBI cognitive scores in the provided block. The project cannot proceed with scientific analysis until one is identified.

2. **Atlas Source**: The `Genius-Society/aal_stats_vol` CSV is verified for format. The code will parse this to define the AAL parcellation.

3. **Cognitive Scores**: Since no verified URL exists for mTBI cognitive scores in the "Verified datasets" block, the plan assumes the `openneuro-fslr64k` dataset *might* contain this in its metadata (as per the "Assumption about variable fit"). If not, FR-007 is triggered to report the limitation.

## Methodological Strategy

### 1. Data Preprocessing (FR-001)
* **Tool**: `nilearn` (CPU-only).
* **Process**:
 * Load NIfTI images from the verified OpenNeuro source.
 * Apply minimal confound regression (motion parameters, global signal) as full ICA-AROMA is too heavy for the 6GB RAM limit.
 * **Memory Management**: Process in batches of 5 subjects. Stream data rather than loading all into RAM.
 * **Check**: Ensure peak RAM ≤ 6GB. If exceeded, reduce batch size to 3 or 1.

### 2. Graph Metric Calculation (FR-002, FR-008)
* **Tool**: `networkx`, `numpy`.
* **Process**:
 * Parcellate preprocessed fMRI using the AAL atlas (from verified CSV).
 * Compute Pearson correlation matrix between ROIs.
 * **Sparsity Threshold**: Apply proportional sparsity (10-20%) to ensure the graph is not fully connected (FR-008).
 * Calculate: Global Efficiency, Local Efficiency, Modularity (Q).
 * **Collinearity Mitigation**: Calculate VIF for predictors. If VIF > 5, perform Principal Component Analysis (PCA) on the graph metrics and use the first principal component (PC1) as the predictor in the LMM to avoid multicollinearity. If PCA is not applicable, report the joint relationship descriptively.

### 3. Statistical Modeling (FR-003, SC-001)
* **Tool**: `statsmodels` (MixedLM).
* **Model**: `Cognitive_Score ~ Global_Eff + Local_Eff + Modularity + Time + (1|Subject_ID)` (or `PC1 + Time + (1|Subject_ID)` if collinearity is detected).
* **Constraints**:
 * **Sample Size**: If `n < 20`, switch to non-parametric bootstrapping (FR-009) OR report as a pilot study (FR-009). The decision logic will check for convergence failure first, then sample size.
 * **Convergence**: If LMM fails to converge, log warning and exclude subject (US-2).
 * **Causal Claim**: Claims are strictly **associational** due to the observational nature of the data (no randomization). The study cannot distinguish between reconfiguration causing recovery vs. recovery causing reconfiguration.

### 4. Robustness Validation (FR-004, FR-005, SC-002, SC-003)
* **Permutation Testing**:
 * Shuffle the `Cognitive_Score` labels [deferred] times.
 * Refit the model (or use a simplified statistic) for each permutation.
 * Calculate empirical p-value: `(count(null_stats >= observed_stat) +) / (1000 + 1)`.
 * **Note**: If running in "Methodology Validation Mode" with synthetic data, the resulting p-values are artifacts of the synthetic generation and will not be reported as scientific results.
* **Sensitivity Analysis**:
 * Sweep sparsity threshold (e.g., 5%, 10%, 15%, [deferred], [deferred]).
 * Record the variation in the primary correlation coefficient.
* **Runtime Control**: Log warning at 5h; hard stop at 6h (FR-003).

## Decision Log

| Decision | Rationale | Impact |
|:--- |:--- |:--- |
| **Use `nilearn` for minimal preprocessing** | Full pipelines (fMRIPrep) exceed 6GB RAM and 6h runtime on CPU. Minimal confound regression is sufficient for graph metrics per spec assumptions. | Reduces memory footprint; adheres to Constitution Principle VII. |
| **Batch size = 5 subjects** | Ensures RAM usage stays below 6GB. If a single subject's data is large, batch size reduces dynamically. | Prevents OOM errors on GitHub Actions. |
| **Permutation Testing (1,000 iters)** | Required by Constitution Principle VI for small cohorts. Parametric assumptions are weak for n < 20. | Increases computational time but ensures statistical robustness. |
| **Skip subjects with missing time points** | Longitudinal LMM requires paired data. Cross-sectional checks are secondary. | Reduces effective sample size; triggers FR-009 contingency if n < 20. |
| **No GPU usage** | Spec and Constitution prohibit GPU. | Ensures compatibility with free-tier CI. |
| **Methodology Validation Mode** | No verified source for cognitive scores exists. The pipeline must validate code correctness without making scientific claims. | Ensures code quality while acknowledging the data gap. |
