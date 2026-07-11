# Research: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

## 1. Dataset Strategy

### 1.1 Target Dataset Verification
The specification requires **OpenNeuro ds000030** (Schizophrenia vs. Healthy Controls, rs-fMRI).
**Critical Finding**: The verified dataset URLs provided in the project input do **not** explicitly confirm the presence of `ds000030` with the required diagnostic labels.
- **Verified URL 1**: ` (Generic OpenNeuro FSLR64k, likely not ds000030 specific).
- **Verified URL 2**: ` (Lung cancer data, **NOT** Schizophrenia).
- **Verified URL 3**: ` (Test data).

**Action Plan**:
1. The `preprocessing/pipeline.py` will first attempt to fetch `ds000030` via the `openneuro` Python client or direct HuggingFace `datasets` loader if a verified mirror exists.
2. **Stop Condition**: If `ds000030` (or a verified equivalent with Schizophrenia/Control labels) is not found in the verified list within the first 10 minutes of execution, the pipeline **aborts** with error code `DATA_GAP`.
3. **No Synthetic Hypothesis Testing**: Synthetic data is used **only** for unit testing the pipeline logic (e.g., verifying graph metric calculation). It is **not** used to validate the schizophrenia hypothesis.
4. **Data Availability Report**: If the dataset is missing, the pipeline generates a `data_availability_report.json` documenting the attempted URLs and the failure, rather than proceeding with invalid data.

*Note: For the purpose of this plan, we assume the `clane9/openneuro-fslr64k` or a similar verified source contains a subset of ds000030 or equivalent data. If not, the "Data Availability" section of the final paper will be the primary output, and the project will be marked as "Data Unavailable".*

### 1.2 Dataset Variables & Fit
- **Required**: rs-fMRI NIfTI files, Diagnostic Label (Schizophrenia/Control), Motion Parameters, Medication Status (if available).
- **Available**: Based on OpenNeuro standards, NIfTI and JSON sidecars are expected.
- **Gap**: Medication status is often missing in public datasets.
 - **Plan**: If missing, `FR-006` is satisfied by:
 1. Documenting this as a limitation.
 2. Performing a **Sensitivity Analysis** using a simulated covariate (Bernoulli distributed) to estimate the potential impact of unmeasured confounding. This is a sensitivity analysis, not data fabrication, and is explicitly allowed by FR-006.

### 1.3 Data Loading Strategy
- **Method**: `huggingface_hub` or `datasets` library to download specific parquet/NIfTI chunks.
- **Memory Management**: Process subjects one-by-one (streaming) to stay within 7GB RAM. Do not load all NIfTIs into memory simultaneously.
- **Preprocessing**: Use `nilearn` for standard pipeline (realignment, normalization to MNI, bandpass 0.01-0.1Hz).

## 2. Methodology & Statistical Rigor

### 2.1 Preprocessing (FR-001)
- **Tools**: `nilearn.image`, `nibabel`.
- **Steps**:
 1. **Motion Correction**: Realignment to mean image.
 2. **Normalization**: Warp to MNI152 space (standard for AAL).
 3. **Smoothing**: 6mm FWHM (standard).
 4. **Bandpass Filter**: 0.01–0.1 Hz (low-frequency fluctuations).
 5. **Nuisance Regression**: Remove motion parameters (6 or 24), white matter, CSF signals.
 6. **Masking**: Extract time series using AAL atlas (multiple ROIs).

### 2.2 Graph Metric Computation (FR-002, FR-003)
- **Connectivity**: Pearson correlation of ROI time series -> 90x90 matrix.
- **Thresholding**:
 - **Primary**: Proportional threshold (e.g., top %).
 - **Sensitivity Analysis**: Run with 10%, 20%, 30% thresholds. If results vary significantly, flag as "Threshold Sensitive".
 - **Global Signal Control**: Calculate mean connectivity strength for each subject and include it as a covariate in all downstream models to control for global signal differences.
- **Metrics** (using `bctpy` or `networkx`):
 - **Global Efficiency**: Inverse of average shortest path.
 - **Local Efficiency**: Efficiency of local subgraphs.
 - **Modularity**: Louvain algorithm (optimize Q).
 - **Betweenness Centrality**: Node importance.
 - **Regional**: Extract centrality for Prefrontal (e.g., ROIs 1-10) and Hippocampal regions.
- **Collinearity Mitigation**:
 - Compute correlation matrix of all features.
 - If Global and Local Efficiency are correlated (r > 0.8), apply PCA to create a single 'Efficiency' component or drop one feature.
 - Report the correlation matrix in the diagnostics.

### 2.3 Classification & Validation (FR-004, FR-005)
- **Split**: Stratified Train/Test (e.g., /20).
- **Model**: Logistic Regression (L1/Elastic Net) and SVM (RBF kernel).
- **Tuning**: Nested Cross-Validation (Outer: k-fold; Inner: k-fold for hyperparameters).
- **Feature Selection**: **Stability Selection** (Meinshausen & Bühlmann) inside the inner loop. Features retained only if selected in >60% of folds.
- **Performance Metrics**: Accuracy, Precision, Recall, AUC-ROC.
- **Significance**:
 - **Permutation Test**: 1000 iterations. Shuffle labels, retrain, build null distribution.
 - **p-value**: Proportion of permuted accuracies >= observed accuracy.
 - **FDR Correction**: Benjamini-Hochberg for group difference t-tests on individual metrics.
 - **Threshold Check**: Calculate 95% CI for accuracy. Report `meets_accuracy_threshold` (True if lower bound >= 0.65).
- **Effect Size**: Cohen's d for significant metrics.
- **Power Analysis**: Calculate and report Minimum Detectable Effect (MDE) for the observed sample size.

### 2.4 Compute Feasibility (Constraint Check)
- **Runtime**: A cohort of subjects will undergo a workflow comprising Preprocessing ([deferred]), Metrics ([deferred]), and CV ([deferred]), with total computational time scaled proportionally to the sample size.
 - **Mitigation**:
 - Use a **subset** of subjects (e.g., 30 per group = 60 total) if full dataset is larger.
 - **Optimize**: Use `nilearn`'s efficient masking.
 - **Simplify**: Reduce permutations to a computationally feasible subset if the full set exceeds a predefined time threshold. (document trade-off).
 - **CPU Only**: No GPU. Use `joblib` for parallel processing of subjects with a configurable number of cores.
 - **Memory**: Process subjects sequentially for NIfTI loading; store only the 90x90 matrices and feature vectors (tiny memory footprint).
- **Monitoring**: Runtime is tracked. If > 6h, `constraints_met` is set to `false`.

## 3. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **AAL Atlas** | Standard for 90 ROIs; matches spec and ensures reproducibility (Constitution VI). |
| **Nested CV + Stability Selection** | Mandatory to prevent overfitting and ensure robust feature selection in small N datasets (FR-004, Methodology concern). |
| **Permutation Test** | Non-parametric approach is robust for small sample sizes (N=60) and non-normal distributions. |
| **CPU-Only** | Free-tier CI constraint. `scikit-learn` and `nilearn` run efficiently on CPU for this scale. |
| **No Medication Covariate (Real)** | If data missing, forcing a covariate is impossible. Documenting the limitation and performing sensitivity analysis is the correct scientific response (FR-006). |
| **Stop Condition for Data** | Prevents invalid hypothesis testing on synthetic data; ensures the research question is only answered with real data. |
