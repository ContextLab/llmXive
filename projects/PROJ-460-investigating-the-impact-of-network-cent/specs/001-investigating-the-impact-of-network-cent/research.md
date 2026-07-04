# Research: Investigating Network Centrality in ASD Resting-State fMRI

## 1. Dataset Strategy

### Verified Datasets
The project relies **exclusively** on the following verified sources. No other URLs are used.

| Dataset Name | Verified URL(s) | Usage |
| :--- | :--- | :--- |
| **ABIDE Preprocessed Connectomes (fcon_1000)** | `https://fcon_1000.projects.nitrc.org/indi/abide/` (Primary Source) | **Primary Source**. Contains raw NIfTI files, diagnosis labels, age, sex, and motion parameters. Accessed via the `abide` Python package or direct download from the verified fcon_1000 repository. |
| **ABIDE Metadata (HuggingFace)** | `https://huggingface.co/datasets/neurodata/abide` (Verified Neuroimaging Dataset) | **Supplementary**. Contains structured metadata (phenotypes) for participants. Used to cross-reference diagnosis and covariates. |

**Note**: The previous references to LLM benchmark parquet files (e.g., `open-llm-leaderboard-old/details_abideen...`) and placeholder JSON sources (e.g., `huggingartists/asdfgfa`) were incorrect and have been removed. These sources do not contain neuroimaging data and would result in data unavailability.

### Dataset Fit & Variable Verification
**Critical Check**: The spec requires fMRI time-series data, diagnosis labels, age, sex, and motion parameters.
- **Diagnosis, Age, Sex**: Verified present in the ABIDE Preprocessed Connectomes Project and the `abide` package metadata.
- **fMRI Time-Series**: The ABIDE repository provides direct links to raw NIfTI files. The pipeline (`01_download.py`) will use the `abide` package to fetch these files.
- **Motion Parameters**: The ABIDE dataset includes motion parameters (FD, DVARS) derived from the preprocessing logs or raw data. The pipeline will calculate FD if not directly available, using the standard formula.
- **Action**: The pipeline will download a **sampled subset** (e.g., 10 ASD, 10 Control) first to verify the pipeline runs within 6 hours. If the full N=200+ is required by spec but exceeds time limits, the plan will document the **Power Limitation** (SC-002) and proceed with the maximum feasible sample size that fits the 6-hour window.

**Variable Mismatch Handling**:
- If the verified dataset lacks specific motion parameters (e.g., FD > 3mm flag), the system will calculate FD from the raw fMRI data if available, or exclude the participant if motion cannot be assessed.
- If the dataset lacks a specific ROI (e.g., specific parcellation), the Schaefer atlas will be applied to the available data. If the data resolution is insufficient, the analysis will be skipped for that participant.

## 2. Methodological Approach

### Preprocessing (US-1)
- **Tool**: fMRIPrep (Docker container, specific version tag).
- **Constraint**: GitHub Actions free-tier has no GPU. fMRIPrep is CPU-intensive.
- **Strategy**:
  1. Download a **sampled subset** (e.g., 10 ASD, 10 Control) first to verify the pipeline runs within 6 hours.
  2. If the full N=200+ is required by spec but exceeds time limits, the plan will document the **Power Limitation** (SC-002) and proceed with the maximum feasible sample size that fits the 6-hour window.
  3. **Motion Correction**: Realignment and unwarping.
  4. **Nuisance Regression**: Global signal regression (GSR), white matter, CSF, and 24 motion parameters. **Motion Scrubbing**: Volumes with Framewise Displacement (FD) > 0.5mm will be censored (removed) from the time series to mitigate motion-induced spurious correlations.
  5. **Normalization**: MNI space (2mm).

### Centrality Computation (US-2)
- **Parcellation**: Schaefer 400-region atlas (17-network).
- **Time-series**: Extract mean signal per ROI per participant from the preprocessed, scrubbed data.
- **Connectivity Matrix**: Pearson correlation of time-series (400x400).
- **Thresholding**: Top percentile of edges (e.g., [deferred], [deferred], [deferred]) to create binary adjacency matrices (FR-006).
- **Metrics**: Degree, Betweenness, Eigenvector centrality (NetworkX).
- **Collinearity**: Calculate VIF (Variance Inflation Factor) for the three metrics. Report correlations descriptively (FR-010).

### Statistical Analysis (US-2)
- **Test**: **Network-Based Statistic (NBS)** or permutation testing with spatial constraints to account for spatial autocorrelation and the high collinearity between centrality metrics. This replaces the simple univariate t-test approach to avoid false positives.
- **Correction**: FDR correction (q < 0.05) applied to the results of the NBS/permutation test.
- **Sensitivity**: Sweep thresholds (e.g., 5%, 10%, 15%, [deferred]). Report Jaccard similarity of significant node sets (FR-009).

### Classification (US-3)
- **Model**: Logistic Regression (scikit-learn).
- **Features**: Centrality metrics of **all** nodes (with L1 regularization) or features selected via **Nested Cross-Validation**.
- **Validation**: **Nested Cross-Validation**. The inner loop performs feature selection (if used) and hyperparameter tuning, while the outer loop evaluates the model. This prevents data leakage and double-dipping.
- **Metrics**: Accuracy, AUC, Confusion Matrix.
- **Baseline**: [deferred] (to be determined by class imbalance in the actual dataset).

## 3. Statistical Rigor & Limitations

- **Multiple Comparisons**: NBS/permutation testing with FDR correction applied to account for spatial autocorrelation and metric collinearity.
- **Power**: Sample size [deferred]. If N < 50 per group, the report will explicitly state low power and interpret findings as preliminary.
- **Causality**: Observational. All claims framed as "associational".
- **Collinearity**: Degree, Betweenness, and Eigenvector are highly correlated. The plan will **not** claim independent effects. Instead, it will report the joint pattern and VIF values.
- **Measurement Validity**: fMRIPrep is the gold standard for preprocessing. Schaefer atlas is standard for parcellation. Motion scrubbing and GSR are implemented to mitigate motion artifacts.

## 4. Compute Feasibility

- **Hardware**: 2 CPU, 7GB RAM.
- **Bottleneck**: fMRIPrep preprocessing.
- **Mitigation**: 
  - Run preprocessing in parallel batches (if memory allows) or sequentially.
  - If fMRIPrep exceeds 6h for full dataset, the pipeline will process the maximum number of participants possible within the time limit and report the "Effective N" and "Power Limitation".
  - No GPU training. Logistic Regression is CPU-efficient.

## 5. Decision Rationale

- **Why ABIDE?** It is the largest public dataset for ASD resting-state fMRI.
- **Why fMRIPrep?** Ensures reproducibility (Constitution I) and standardized preprocessing.
- **Why Schaefer 400?** Balances resolution and computational cost for centrality metrics.
- **Why Sensitivity Analysis?** Network topology is highly sensitive to threshold choice; robustness is required for scientific validity (FR-009).
- **Why NBS/Permutation?** To address spatial autocorrelation and metric collinearity, ensuring statistical validity (methodology concern).
- **Why Nested CV?** To prevent data leakage and double-dipping in classification (scientific soundness concern).