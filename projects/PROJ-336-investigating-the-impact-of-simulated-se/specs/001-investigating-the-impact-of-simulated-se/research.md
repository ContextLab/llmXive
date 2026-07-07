# Research: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

## Research Question

How does simulated sensory deprivation (1-hour dark/quiet condition) alter the topological organization of resting-state brain networks, specifically modularity, global efficiency, and node strength, compared to a pre-deprivation baseline?

## Dataset Strategy

**Dataset Gap Declaration**: The "Verified datasets" block provided in the spec does not contain a dataset with confirmed pre/post sensory deprivation scans.
-   **Primary Candidate**: OpenNeuro ds001770 (HCP 1200) - **NOT** a sensory deprivation study.
-   **Fallback Candidate**: OpenNeuro ds003820 - **NOT** a sensory deprivation study.
-   **Action**: The pipeline will attempt to verify the presence of 'task-rest' runs with 'deprivation' or 'control' labels. If no such labels are found in the available datasets, the system MUST halt with 'Dataset lacks required deprivation condition labels' error.

**Verified Dataset Sources**:
-   **Source**: OpenNeuro (https://openneuro.org).
-   **Verification**: The plan explicitly checks for the existence of the required experimental conditions before proceeding. No dataset is assumed to fit without verification.

**Dataset-Variable Fit**:
-   **Predictor**: Sensory deprivation condition (pre/post). **Required**. Must be present in dataset labels.
-   **Outcome**: Modularity, global efficiency, node strength. **Derivable** from fMRI data.
-   **Covariate**: Motion metrics (FD). **Required**. Must be derivable from motion parameters.
-   **Conclusion**: If a dataset is found with the required labels, it fits. If not, the study cannot proceed.

**Data Access Strategy**:
1.  Scan available datasets for 'deprivation' or 'control' task labels.
2.  If found, download raw data using `openneuro` CLI or `requests`.
3.  Validate the dataset structure using `bids-validator`.
4.  Preprocess the data (motion correction, normalization, bandpass filtering).
5.  Compute quality metrics (FD) and exclude subjects with excessive motion.
6.  Proceed with analysis only if ≥ 20 subjects pass quality checks.

## Methodology

### 1. Data Preprocessing
-   **Tools**: FSL (via Docker) or AFNI (via Docker) for motion correction, normalization, and bandpass filtering (low-frequency range). If Docker is not available or too large, lightweight Python alternatives (e.g., `nilearn`'s `clean_img`) will be used.
-   **Atlas**: Schaefer 400 ROI atlas (downloaded from GitHub with version pinning).
-   **Temporal/Spatial Handling**: No arbitrary downsampling. If TR > 2s, temporal subsampling is applied only if it maintains the Nyquist criterion for the 0.01-0.1 Hz bandpass. Spatial smoothing is applied only if native resolution > 3mm.
-   **Output**: Preprocessed BOLD time series for each ROI, stored in `.npy` format.

### 2. Functional Connectivity & Network Metrics
-   **Connectivity**: Pearson correlation between all ROI pairs to generate symmetric ROI×ROI matrices.
-   **Thresholding Strategy**: **Proportional Thresholding** (retaining the top X% of edges, e.g., 10-20%) is applied to ensure fixed graph density across subjects, making metrics comparable.
-   **Metrics**:
  - **Modularity**: Louvain algorithm (via `networkx` or `brainconn`).
  - **Global Efficiency**: Calculated using `networkx`.
  - **Node Strength**: Sum of edge weights for each node.
-   **Output**: Metrics for each subject and condition, stored in `.csv`.

### 3. Statistical Analysis
-   **Multivariate Approach**: **MANOVA** is performed first to test the joint effect of condition on (modularity, efficiency, node strength) to account for interdependence.
-   **Univariate Follow-up**: If MANOVA is significant, paired t-tests are performed on individual metrics.
-   **Multiple Comparison Correction**: FDR (Benjamini-Hochberg) is applied to the set of univariate tests.
-   **Permutation Testing**: 
    -   **Strategy**: Sign-flip of the *difference* (Post - Pre) for each subject.
 - **Iterations**: Exact permutation distribution (2^N) if N <= 20; otherwise [deferred] iterations.
    -   **P-value Calculation**: (r+1)/(N+1) where r is the number of permutations with a statistic as extreme as the observed.
-   **Effect Size**: Cohen's d reported for all significant findings.
-   **Power Consideration**: Sample size n ≥ 20 is acknowledged as a potential limitation for detecting small effects. Power analysis will be documented.

### 4. Covariate Independence Justification
-   **Motion Covariates**: Framewise Displacement (FD) is calculated from the *residual* motion parameters *after* the initial motion correction and nuisance regression steps.
-   **Rationale**: This ensures that FD captures variance in the BOLD signal not already removed by the preprocessing pipeline, mitigating collinearity between the covariate and the outcome. FD is included as a continuous covariate in an ANCOVA framework.

### 5. Visualization
-   **Degree Distribution**: Plots showing changes in node degree between pre/post conditions.
-   **Edge Weight Heatmaps**: Visualize changes in connectivity strength, particularly in sensory and default mode networks.

## Statistical Rigor & Assumptions

-   **Multiple Comparisons**: FDR correction applied to all hypothesis tests (modularity, efficiency, node strength) following the MANOVA omnibus test.
-   **Sample Size**: n ≥ 20 subjects. Power analysis will be conducted to assess sensitivity. If power is low, findings will be framed as exploratory.
-   **Causal Inference**: The study design is within-subject longitudinal. If the dataset is observational (no randomization), findings will be framed as **associational**. If randomization is confirmed, causal claims may be made. *Assumption*: The dataset implements a within-subject design where subjects serve as their own control.
-   **Measurement Validity**: The Schaefer atlas is a validated parcellation scheme. Motion parameters are standard.
-   **Collinearity**: Predictors (pre/post) are not definitionally related. FD covariates are derived from residuals to ensure independence from the outcome.

## Compute Feasibility

-   **Hardware**: GitHub Actions free-tier (CPU, 7GB RAM, 14GB disk, no GPU).
-   **Strategies**:
  - **Data Sampling**: If the full dataset exceeds memory/disk limits, a subset of subjects (n=20) will be used.
  - **Efficient Libraries**: `numpy`, `scipy`, `networkx` are CPU-optimized.
  - **Preprocessing**: Lightweight Python tools (e.g., `nilearn`) will be used if FSL/AFNI Docker images are too large.
  - **Runtime**: Pipeline designed to complete in ≤ 6 hours. Checkpointing will be implemented for intermediate results.
-   **No GPU/CUDA**: All methods are CPU-tractable.

## Sensitivity Analysis

To satisfy SC-005:
-   **Motion Threshold Sweep**: The pipeline will run the exclusion logic with thresholds at multiple predefined levels.
-   **Effect Size Sweep**: Statistical significance will be reported for Cohen's d thresholds of small, medium, and large effect sizes.
-   **Output**: A sensitivity report will be generated showing how the number of significant findings changes with these thresholds.

## Scope Note

**SC-006 (Questionnaires)**: The current project scope (User Stories 1-3, FRs 001-010) focuses exclusively on fMRI data, network metrics, and statistical analysis. There are no questionnaire-based measures mentioned in the User Stories or FRs. SC-006 is noted as not applicable to the current scope but the pipeline is designed to ingest them if added later.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use MANOVA for primary analysis | Addresses interdependence of network metrics (modularity, efficiency, node strength). |
| Use Proportional Thresholding | Ensures fixed graph density, making metrics comparable across subjects. |
| Use Exact Permutation (2^N) for N<=20 | Avoids discretization error in small sample sizes. |
| Calculate FD from residual motion | Ensures covariate independence from preprocessing noise removal. |
| Halt if no deprivation labels found | Prevents using incorrect datasets (e.g., HCP) for the sensory deprivation hypothesis. |
| Frame findings as associational if no randomization | Adheres to statistical rigor; causal claims require randomization. |
| Use CPU-only methods | Required for GitHub Actions free-tier execution. |