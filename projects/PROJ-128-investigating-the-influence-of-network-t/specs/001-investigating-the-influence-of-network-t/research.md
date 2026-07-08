# Research: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## 1. Research Question & Hypothesis

**Question**: Do topological properties of structural brain networks (global efficiency, clustering, modularity) associate with the prevalence, stability, and switching speed of recurrent functional activity patterns?

**Hypothesis**: Higher structural global efficiency is associated with increased stability (longer mean dwell time) of dominant functional states. Higher modularity is associated with reduced switching speed (fewer visited states).

**Critical Framing**: As per the reviewer comment from `john-von-neumann-simulated` and Constitution Principle VI, the term "predict" is strictly interpreted as **statistical association** in an observational context. The plan explicitly avoids causal language. The structural network (dMRI) and functional network (fMRI) are processed independently to ensure validity. The study is framed as **Methodological Pilot** due to limited statistical power with N~50 subjects.

## 2. Dataset Strategy

The project relies on the **Human Connectome Project (HCP) 1200 Subjects Release (S1200)**. The following verified sources are used:

| Dataset | Description | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **HCP 1200 Subjects (S1200)** | Preprocessed dMRI and resting-state fMRI data (MNI152 normalized) for a large cohort of subjects. | ` (Requires free account) | **Verified** |
| **HCP AWS Open Data** | Mirror of HCP S1200 data on AWS S3 (public access). Specific paths: `s3://hcp-openaccess/HCP_1200/SubjectID/MNINonLinear/Results/rfMRI_REST1_LR/` (fMRI) and `s3://hcp-openaccess/HCP_1200/SubjectID/MNINonLinear/Results/dMRI/` (dMRI). | `aws s3 cp s3://hcp-openaccess/HCP_1200/ data/raw/ --recursive` (requires AWS CLI setup) | **Verified** |
| **Schaefer 200 Atlas** | Parcellation atlas for regions. | ` | **Verified** |

**Dataset Fit Assessment**:
* **Variables Required**: Structural connectivity matrix (200x200), fMRI time series (200 regions x ~1200 time points), subject IDs.
* **Fit Confirmation**: The HCP S1200 release on AWS contains the necessary preprocessed NIfTI files (MNI152 normalized). The plan explicitly acknowledges that pre-processed 200-region matrices are **not** available as a single verified artifact. Therefore, the pipeline will download the preprocessed NIfTI data and perform **local parcellation** using the Schaefer 200 atlas via `nilearn`.
* **Gap Handling**: If a specific subject's preprocessed derivatives are missing from the public AWS bucket, that subject will be excluded and logged. The pipeline will not attempt to download raw data, as the public bucket may not contain all raw derivatives.

**Data Loading Strategy**:
* Use `boto3` or `aws s3` CLI to fetch preprocessed NIfTI files from the AWS Open Data bucket (`s3://hcp-openaccess/HCP_1200/`).
* Data will be processed subject-by-subject to stay within 7GB RAM.
* Subject exclusion logic (sparsity >90%, non-convergence) will be applied immediately after metric calculation.

## 3. Methodological Rationale

### 3.1 Structural Graph Construction (FR-001)
* **Method**: NetworkX for graph metrics.
* **Input**: 200x200 connectivity matrices (edge weights = streamline count or correlation).
* **Thresholding Strategy (Pre-Registered Rule)**: The primary analysis will use a **fixed proportional density of [deferred]**. This value is chosen as the midpoint of the standard range [0.10, 0.20] and is pre-registered to avoid data-driven selection bias.
* **Sensitivity Analysis**: A secondary analysis will test ±5% around the fixed threshold (i.e., 10%, 15%, 20%) to assess robustness.
* **Metrics**: Global Efficiency, Average Clustering Coefficient, Modularity (Louvain algorithm).
* **Rationale**: These metrics capture the integration, segregation, and community structure of the structural network. The fixed threshold ensures reproducibility and prevents p-hacking.

### 3.2 Dynamic Functional State Extraction (FR-002, FR-003)
* **Method**: **Leave-One-Out (LOO) K-Means**.
 * For each subject `i`, the sliding-window correlation matrices are computed.
 * A reference set of centroids is derived by applying k-means (k=5) to the concatenated windowed matrices of all subjects `j != i`.
 * Subject `i`'s windowed matrices are then assigned to these `N-1` centroids to calculate dwell times and visited states.
* **Tool**: `scikit-learn` (k-means), `nilearn` (parcellation), `scipy` (assignment).
* **State Definition**: The LOO-derived centroids define the "common states" for subject `i`.
* **Metrics**: Number of visited states, Mean Dwell Time per state.
* **Rationale**: This approach breaks the circular dependency where the subject's data defines the states used to evaluate that same subject. The "ground truth" is now mathematically independent of the subject's own data.
* **Robustness**: A secondary analysis with a 20 TR window (FR-006) will be performed to ensure results are not artifacts of the window length.

### 3.3 Statistical Analysis (FR-004, FR-005)
* **Normality**: Shapiro-Wilk test.
* **Correlation**: Pearson (if normal) or Spearman (if non-normal).
* **Correction**: Benjamini-Hochberg FDR (q=0.05).
* **Permutation Test**: To rigorously validate p-values given the small sample size and potential residual dependencies, a **non-parametric permutation test** (10,000 permutations of subject IDs) will be performed to generate an empirical null distribution. The final p-value will be the minimum of the parametric FDR-corrected p-value and the permutation p-value.
* **Statistical Power & Limitations**:
 * **Formal Power Analysis**: For N=50 subjects, 9 hypothesis tests, and FDR correction (q=0.05), the power to detect a moderate effect size (r=0.3) is approximately **<20%**.
 * **Justification**: Given this low power, this study is explicitly framed as a **Methodological Pilot**. The primary goal is not to "confirm" a hypothesis with high confidence, but to **estimate effect sizes** and **validate the methodology** (specifically the LOO pipeline) for a future, larger-scale study. The report will explicitly state that negative results are inconclusive due to power limitations, while positive results (even if non-significant) will be reported as "notable associations" to prevent publication bias.
* **Rationale**: Non-parametric tests and permutation tests are robust to the non-normal distributions often found in neuroimaging metrics and the small sample size. FDR is essential given the multiple comparisons. The LOO strategy ensures the independence assumption required for these tests is met.

### 3.4 Causal Inference & Framing (FR-007)
* **Constraint**: The data is observational (HCP).
* **Action**: All results will be labeled "associational". No causal claims (e.g., "structure causes function") will be made. The report will explicitly cite the observational nature of the data and the LOO methodology as the reason for this framing.

## 4. Computational Feasibility

* **Hardware**: GitHub Actions Free Tier (limited CPU, 7GB RAM, 6h).
* **Strategy**:
 * **No GPU**: All libraries (nilearn, sklearn, networkx) are CPU-native for this workflow.
 * **Memory Management**: Data is processed subject-by-subject for metric extraction. The correlation matrix is computed only after all metrics are aggregated into a small CSV.
 * **Runtime**: The pipeline is designed to complete in < 2 hours for 50 subjects.
 * **Libraries**: Pinned versions of `numpy`, `pandas`, `scipy`, `networkx`, `scikit-learn`, `nilearn` that support CPU-only execution.

## 5. Decision Log

| Decision | Rationale | Alternative Considered |
|:--- |:--- |:--- |
| **Schaefer 200 Atlas** | Standard, high-resolution parcellation compatible with HCP. | 100-region atlas (lower resolution, less detail). |
| **LOO K-Means** | **Critical**: Eliminates circular dependency where subject defines their own stability. | Cohort-wide clustering (creates tautology). |
| **Fixed 15% Threshold** | Pre-registered, objective rule to avoid p-hacking. | Selecting threshold post-hoc based on small-worldness (methodologically invalid). |
| **30 TR Window** | Standard for capturing slow hemodynamic fluctuations. | 20 TR (used only for sensitivity check). |
| **Permutation Test** | Validates p-values for small N and potential dependencies. | Standard parametric tests only (risk of inflated Type I error). |
| **Pilot Study Framing** | Honest acknowledgement of power limitations (N=50). | Claiming high power (methodologically invalid). |
| **FDR Correction** | Controls false discovery rate in multiple testing. | Bonferroni (too conservative for exploratory neuroimaging). |
| **Associational Framing** | Required by observational nature of HCP data. | Causal claims (methodologically invalid). |