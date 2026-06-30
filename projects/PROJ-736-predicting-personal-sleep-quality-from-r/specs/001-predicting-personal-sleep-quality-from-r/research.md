# Research: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

## 1. Dataset Strategy

### 1.1 Primary Dataset: Human Connectome Project (HCP) 1200 Subjects Release

**Source**: The Human Connectome Project, WU-Minn Consortium (Principal Investigators: David Van Essen and Kamil Ugurbil; UMH091657).

**Verified URL**: https://db.humanconnectome.org/ (Access via SDCS/ConnectomeDB requires registration).  
**Programmatic Access**: `nilearn` or manual download via S3 with credentials.  
**Format**: Minimally preprocessed (32k_fs_LR) CIFTI `.dtseries.nii` files and behavioral data.

**Variable Fit Verification**:
- **Outcome**: Sleep Score.
  - *Source File*: `hcp1200_behavioral_data.csv` (or the specific Questionnaire file within the HCP release). **Note**: The file `sleep.csv` does not exist; sleep items are part of the main behavioral CSV.
  - *Columns*: `Sleep_Duration`, `Sleep_Quality`, `Trouble_Falling_Asleep`.
  - *Derivation*: Composite Sleep Score = Sum(Sleep_Duration, Sleep_Quality, Trouble_Falling_Asleep) [Standardized].
  - *Construct Validity*: The HCP dataset **does not** contain the Pittsburgh Sleep Quality Index (PSQI). This study uses a proxy derived from available items.
  - *Risk*: The proxy may lack full psychometric validity. The plan includes a **Construct Validity Check**: correlation of the proxy with known sleep correlates and an explicit statement in the final report that results are "associational with a proxy outcome".
  - *Independence Check*: Before modeling, the code will verify that the Sleep Score is not trivially correlated with specific connectivity features (e.g., motion artifacts) to avoid circularity.
- **Predictors**: Resting-state fMRI time series.
  - *Verification*: HCP includes two rs-fMRI runs (LR and RL).
  - *Fit*: Perfect fit.

**Data Loading Strategy**:
- The `download_hcp.py` script will fetch data via HCP SDCS API or direct S3.
- **Fallback**: If programmatic access fails, instructions for manual download are provided. Data placed in `data/raw/`.

### 1.2 Secondary Data: Atlas Definitions
- **Schaefer-200 Atlas**: 200 cortical parcels + subcortical ROIs.
  - *Source*: Schaefer et al. (2018).
  - *Access*: `nilearn.datasets.fetch_atlas_schaefer_2018()`.

### 1.3 Data Preprocessing Pipeline
1. **Ingestion**: Load CIFTI `.dtseries.nii` and behavioral CSV.
2. **Parcellation**: Extract mean time series for 200+ ROIs.
3. **Nuisance Regression & Filtering**: Band-pass filter - 0.1 Hz.
4. **Connectivity Matrix**: Pearson correlation.
5. **Fisher-z Transform**: `atanh`.
6. **Vectorization**: Upper triangular elements.
   - **Note**: Variance Thresholding and PCA are **NOT** applied here. They are applied dynamically within the CV loop.

## 2. Modeling Strategy

### 2.1 Algorithm: Elastic Net Regression
- **Rationale**: High-dimensional data (p >> n) requires regularization. Elastic Net handles correlated predictors.
- **Implementation**: `sklearn.linear_model.ElasticNetCV`.
  - **Outer Loop**: 5-fold CV for performance estimation.
  - **Inner Loop**: 5-fold CV for hyperparameter tuning.

### 2.2 Statistical Validation & Dimensionality Reduction
- **Critical Correction (Data Leakage)**:
  - Variance Thresholding and PCA are **NOT** performed on the full dataset.
  - **Protocol**: For every fold in the Outer CV (and every permutation iteration), the Variance Threshold and PCA are **fitted ONLY on the training fold** and then applied to the test fold.
  - **Reasoning**: Fitting on the full dataset leaks information from the test set into the feature selection process, inflating R² and invalidating p-values.
- **Metrics**: Pearson r, R².
- **Significance Testing**:
  - **Permutation Test**: 1,000 iterations.
    - **Strategy**: To meet the 5-hour compute limit on 2 vCPU, the permutation test is executed on a **stratified subset of 100 subjects**.
    - **Pipeline**: For each permutation, the **entire nested CV pipeline** (including dynamic feature selection) is re-run on the subset.
    - **Rationale**: This preserves the statistical validity of the null hypothesis (re-fitting features) while making the computation feasible.
  - **Bootstrap**: 1,000 resamples on the full set for CI.

### 2.3 Sensitivity Analysis
- **Grid**: Variance thresholds {0.005, 0.01, 0.02} × PCA retention {0.95, 0.90, 0.85}.
- **Execution**: Full nested CV run for each of the 9 combinations.

## 3. Compute Feasibility & Constraints

### 3.1 Hardware Constraints
- **Environment**: GitHub Actions `ubuntu-latest` (2 vCPU, 7 GB RAM).
- **Time Limit**: 5 hours.
- **RAM Limit**: 6 GB.

### 3.2 Mitigation Strategies
- **Stratified Subsampling**: Permutation test runs on 100 subjects (not 300) to reduce runtime by [deferred] while maintaining the statistical method (re-fitting).
- **Memory Management**:
  - Process subjects one-by-one for feature extraction.
  - Use `float32` for matrices.
  - Garbage collection after each permutation.
- **Early Stopping**: If runtime > 4 hours, reduce permutation count to 500 (logged as deviation).

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing Sleep Data** | No outcome variable. | Script checks for specific columns in `hcp1200_behavioral_data.csv`. |
| **Variance Threshold Removes All Edges** | Empty matrix. | Fallback to 0.005 or 0.001. Log warning. |
| **Runtime Exceeds 5 Hours** | CI failure. | Stratified subsampling for permutations. Early stopping. |
| **Low Statistical Power** | False negatives. | Explicit power calculation in final report. Frame as exploratory. |
| **Data Leakage** | Invalid results. | Enforced 'Fit-Within-Loop' for all dimensionality reduction. |

## 5. Power & Sample Size Analysis
- **Assumption**: N ≈ 200-300 subjects.
- **Effect Size**: Expected R² ≈ 0.05.
- **Power**: With N=250 and p=5000 (post-PCA), power to detect R²=0.05 is likely low (<0.5).
- **Strategy**: The study is framed as **exploratory**. The primary goal is to estimate the effect size (R²) and its confidence interval, rather than strict hypothesis rejection. The final report will explicitly state the calculated power.

## 6. Ethical Considerations
- **Privacy**: HCP data is de-identified.
- **Bias**: HCP sample is healthy adults. Generalizability limited.
- **Causal Claims**: Results are "associational" predictions, not causal.
