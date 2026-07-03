# Research: Network Module Dynamics in Predicting Working Memory

## Summary

This research phase validates the feasibility of the proposed analysis pipeline, confirms dataset-variable fit, and details the methodological approach for computing dynamic network flexibility via Multilayer Modularity Optimization (MMO) and its association with working memory capacity.

## Dataset Strategy

| Dataset Name | Source URL | Variables Available | Fit for Purpose |
| :--- | :--- | :--- | :--- |
| **HCP (OpenNeuro ds001734)** | `https://openneuro.org/datasets/ds001734` | **Verified**: Contains resting-state fMRI time series and 2-back behavioral scores for the same subjects. | **PASS**: ds001734 is a public, no-auth dataset that matches the required variables (rs-fMRI + 2-back) for the study. It is the primary source for this project. |
| **HCP (OpenNeuro ds000224)** | *Not used* | *N/A* | **FAIL**: Requires authentication/DUA. Not accessible via standard CI tools without credentials. |

*Note: The project explicitly uses `ds001734` as the verified source. The ingestion script will abort if this dataset is not found in the verified list.*

## Methodological Approach

### 1. Data Ingestion & Preprocessing (FR-001, FR-008)
- **Source**: Load from verified HCP URL for `ds001734`. If unavailable, abort with "Dataset Mismatch Error".
- **Motion Scrubbing**:
  - Exclude subjects with mean FD > 0.2mm.
  - For included subjects, remove time points with FD > 0.2mm.
  - Regress out 6 rigid-body motion parameters, their derivatives, and mean FD using OLS.
  - **Non-Linear Control**: Retain the *original* motion parameters (pre-OLS) and reduce them via PCA to a selected number of principal components. These will be used as covariates in the final correlation to capture non-linear residual motion effects.
- **Memory Management**: Process subjects one-by-one or in small batches. Stream data where possible. Use `psutil` to monitor peak RSS. If RAM > 6 GB (buffer), reduce batch size or subject count.

### 2. Dynamic Flexibility Metric (FR-002, FR-003, FR-004)
- **Multilayer Modularity Optimization (MMO)**:
  - **Supra-Graph Construction**: Construct a single graph where nodes are (Region, Time Window) pairs.
  - **Intra-layer edges**: Weighted by functional connectivity within the window.
  - **Inter-layer edges**: Connect the same region across adjacent windows with a coupling parameter `omega` (default 1.0).
  - **Global Optimization**: Apply the Leiden algorithm (or multilayer Louvain) to the *entire supra-graph* to find a community trajectory. This replaces the "per-window consensus" approach, reducing computational cost and avoiding artificial smoothing.
  - **Flexibility Calculation**:
    - For each node, calculate the probability of switching communities across the optimized trajectory.
    - Average across all nodes to get a single "Whole-Brain Flexibility" score per subject.
    - Validate range [0, 1].
- **Sensitivity**: Repeat MMO with varying window lengths.

### 3. Statistical Analysis (FR-005, FR-006, FR-007, FR-009)
- **Primary Test**: Partial Spearman correlation (Flexibility vs. 2-back Accuracy), controlling for **top 5 motion principal components** (not just mean FD) to capture non-linear residual confounds.
- **Permutation Test**:
  - A large number of permutations of the working memory scores (shuffled).
  - Calculate p-value = (count of permuted correlations ≥ observed) / total number of permutations.
  - **Correction**: If p=0, set p = 1/(N+1) = 1/1001.
- **Sensitivity Analysis**:
  - Repeat correlation and permutation for window lengths s, 60s, 90s.
  - **Multiple Testing Correction**: Apply Bonferroni correction (alpha = 0.05/3 ≈ 0.0167) to the primary significance claim. If the result is not significant after correction, it is reported as "exploratory only".
- **Motion-Stratified Analysis**:
  - Stratify subjects into "Low Motion" (mean FD < 0.1mm) and "High Motion" groups.
  - Report correlation coefficients for both groups to assess robustness against motion artifacts.
- **Inference Framing**:
  - Explicitly state results are "associational" (FR-007).
  - Acknowledge observational nature (no randomization).
  - Acknowledge power limitation (N=100 is exploratory, not powered for definitive causal claims).

## Statistical Rigor & Limitations

- **Multiple Comparisons**: The sensitivity analysis (multiple window lengths) involves a series of tests. A Bonferroni correction (alpha = 0.05/3) is applied to the primary significance claim.
- **Sample Size / Power**: N=100 is a feasibility limit. No formal power calculation is performed. The study is exploratory. Results should be interpreted as preliminary associations.
- **Causal Inference**: The study is observational. **No causal claims** will be made. The correlation is framed as an association between dynamic network reconfiguration and working memory capacity.
- **Measurement Validity**: HCP 2-back task is a standard, validated measure of working memory. Resting-state fMRI is standard.
- **Collinearity**: Flexibility and WM are distinct constructs. Motion (FD) is controlled for via regression, scrubbing, and PCA-based covariates. No definitional collinearity is expected.
- **Non-Linear Motion Confounds**: The plan addresses the limitation of linear motion control by including motion PCs as covariates and stratifying by motion level.

## Compute Feasibility Plan

- **Runtime**: Estimated hours for 100 subjects with MMO (global optimization).
  - *Fallback*: If runtime > 5 hours, reduce subject count to 50 or window step size.
- **Memory**: Peak RAM < 7 GB.
  - *Strategy*: Process one subject at a time for flexibility calculation. Do not load all 100 subjects' time series into memory simultaneously.
- **No GPU**: All operations (correlation, permutation, MMO) are CPU-native.

## Conclusion

The proposed methodology is feasible within the compute constraints, provided the dataset-variable fit is confirmed. The use of `ds001734` (verified public source) and Multilayer Modularity Optimization (MMO) resolves the critical risks of authentication barriers and computational intractability. The statistical approach is robust to motion confounds and multiple testing.
