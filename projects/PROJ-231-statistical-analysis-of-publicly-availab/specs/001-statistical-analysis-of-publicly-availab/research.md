# Research: Statistical Analysis of Publicly Available Climate Model Output Ensembles

## 1. Dataset Strategy

### 1.1 Verified Datasets
The project relies exclusively on the following verified sources. No other URLs are used.

| Dataset Name | Source URL | Format | Variable Coverage | Suitability |
|:--- |:--- |:--- |:--- |:--- |
| **CMIP6 Test Set** | ` | Parquet | Temperature/Precipitation (Sample) | **Primary Source**. Used for pipeline validation. |
| **CMIP6 Mini Test** | ` | Parquet | Single Model (ACCESS-CM2) | **Validation**. Ensures single-model ingestion works. |
| **CMIP6 Mini Test v2.1** | ` | Parquet | Single Model (ACCESS-CM2) | **Validation**. Consistency check. |

**Dataset Access Strategy**:
1. **Schema Verification**: Before processing, `ingestion.py` will explicitly verify that the dataset contains `tas` (temperature) and `pr` (precipitation) columns, monthly temporal resolution, and global land coverage. If the verified test shards fail this check, the pipeline halts with a specific error.
2. **Ingestion**: The `ingestion.py` script will use the `datasets` library (`load_dataset`) to fetch the full `sungduk/wip_cmip6` repository (if available) or the specific parquet shards listed above.
3. **Streaming**: To comply with **SC-003** (Compute Feasibility), data will be loaded in streaming mode (`streaming=True`) if the full ensemble is too large for 7 GB RAM. Statistics (means, variances) will be accumulated online.
4. **Stratified Sampling**: If the full ensemble cannot be processed within 6 hours, a **fixed-seed stratified random sample** of ensemble members (ensuring representation from all major model families/centers) will be selected. This sample serves as the fixed "full ensemble" baseline for the LOO Jackknife. This limitation will be explicitly reported in the final output.

**Synthetic/Multi-Model Test Strategy**:
To validate the bootstrap/Jackknife pipeline (which requires inter-model variance), the plan constructs a **synthetic multi-model test set** for the validation phase:
- Combine the verified single-model shard (ACCESS-CM2) with synthetic variations (e.g., adding controlled noise or phase shifts) to mimic a 10-model ensemble.
- This synthetic set is used to verify that the LOO Jackknife correctly identifies when a specific "model" is removed and that the stability metrics respond to heterogeneity.

## 2. Methodological Rigor

### 2.1 Functional Representation (B-Splines)
* **Method**: B-spline basis expansion.
* **Global Basis Dimension ($K$)**: To resolve the streaming vs. adaptive conflict:
 1. A **Pilot Subset** (stratified by model family) is loaded into memory.
 2. Global GCV/AIC is performed on the Pilot Subset to determine the optimal $K$.
 3. This fixed $K$ is then applied to the full streaming dataset.
* **Missing Data**: **Spline-based Imputation** is used. Missing values are estimated by fitting a preliminary B-spline to the available points and interpolating, preserving the derivative structure required for fPCA. This replaces linear interpolation to avoid biasing high-frequency modes.
* **Fallback**: If GCV/AIC fails on the pilot, a default range of $K \in [10, 20]$ is used (**FR-002**).

### 2.2 Functional Principal Component Analysis (fPCA)
* **Method**: fPCA on the functional data objects using `scikit-fda` (exclusive library).
* **Output**: Eigenfunctions (modes) and eigenvalues.
* **Variance**: Cumulative variance explained by the first 3-5 components will be calculated (**SC-001**).
* **Statistical Note**: Since this is an observational ensemble (no random assignment of models), all findings are **associational**. We do not claim causal effects of specific models on the climate system.

### 2.3 Robustness via Leave-One-Out (LOO) Jackknife
* **Protocol**: Instead of random bootstrap, the plan uses **Leave-One-Out (LOO) Jackknife** and **Block Jackknife** (by model family).
 1. **LOO**: Remove one model at a time from the ensemble, re-run fPCA, and compare the new modes to the full ensemble modes.
 2. **Block Jackknife**: Remove all models from one modeling center/family at a time.
* **Metric**: **Procrustean Alignment** (Procrustes distance or subspace correlation) between the eigenfunctions of the reduced ensemble and the full ensemble. This accounts for sign flipping and rotational ambiguity in fPCA.
* **Stability**: The standard deviation of the Procrustes distances across all LOO iterations is reported (**SC-002**).
* **Sensitivity**: Models or families whose removal causes a large shift in the dominant modes are flagged as "highly influential."

### 2.4 Multiple Comparisons & Power
* **Multiple Testing**: While fPCA itself is a dimension reduction technique, if multiple hypotheses are tested (e.g., "Is Component 1 significant?"), a family-wise error correction (e.g., Bonferroni) will be applied if formal hypothesis testing is performed on the eigenvalues.
* **Power Limitation**: If the ensemble size is small (< 10 models), the LOO Jackknife may be unstable. The system will halt and report a power limitation (**Edge Case**).

## 3. Compute Feasibility (CPU-First)

* **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
* **Strategy**:
 * **CPU-First**: `scikit-fda` and `numpy` are used. No GPU required.
 * **Memory Management**: Streaming data loading and in-place array operations to minimize memory footprint.
 * **Time Limit**: The pipeline is designed to complete within 6 hours. If the full ensemble is too large, a stratified sample is taken.
* **GPU Escape Hatch**: Not required. fPCA and B-splines are computationally tractable on CPU for the expected dataset sizes (even with streaming).

## 4. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **B-Splines over Fourier** | Climate data is non-stationary and has complex temporal structures; B-splines handle local variations and missing data better than global Fourier bases. |
| **LOO Jackknife over Bootstrap** | Random bootstrap creates circular validation (subset vs. subset of itself) and fails to test sensitivity to specific model families. LOO directly measures the impact of removing a model. |
| **Procrustean Alignment over Correlation** | fPCA eigenfunctions are unique only up to sign and rotation. Simple correlation fails to account for subspace rotation, leading to false instability signals. |
| **Spline-based Imputation over Linear** | Linear interpolation distorts the derivative structure required for fPCA, biasing high-frequency modes. Spline imputation preserves the functional nature of the data. |
| **Pilot-based Global Basis** | Streaming global GCV/AIC is impossible. A pilot subset provides a statistically valid estimate of the global basis dimension $K$ without memory overflow. |
| **scikit-fda Exclusive** | Eliminates contract ambiguity and complexity of `rpy2`/`refund` fallback. |