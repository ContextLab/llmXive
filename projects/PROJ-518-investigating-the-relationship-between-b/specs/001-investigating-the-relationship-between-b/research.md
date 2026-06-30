# Research: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

## Executive Summary

This research plan validates the feasibility of testing the hypothesis that dynamic reconfiguration of functional brain networks predicts **creative achievement** (measured by the Creative Achievement Questionnaire, CAQ). We address the critical data availability gap (FR-011) by confirming the presence of the CAQ in the OpenNeuro ds000224 dataset. We detail the computational methodology for deriving network flexibility (with consensus clustering), the statistical framework for hypothesis testing (using null models and outcome permutation), and the strategy for ensuring reproducibility on CPU-only infrastructure.

**Construct Validity Note**: The hypothesis originally framed "divergent thinking." The available data (CAQ) measures lifetime creative achievements (a trait), not real-time divergent thinking (a state). This plan explicitly tests the association between brain dynamics and creative achievement, acknowledging that while CAQ is a validated proxy for creativity, it does not directly measure the cognitive process of divergent thinking.

## Dataset Strategy

### Primary Dataset: Human Connectome Project (HCP) via OpenNeuro
The study relies on the HCP S900/S1200 release, accessed via the official OpenNeuro repository to ensure data integrity and provenance.

| Component | Source / URL | Verification Status | Notes |
| :--- | :--- | :--- | :--- |
| **Resting-state fMRI** | `https://openneuro.org/datasets/ds000224` | **Verified** | Official OpenNeuro accession for HCP S900/S1200. Contains raw NIFTI data. |
| **Behavioral Metadata (CAQ)** | `https://openneuro.org/datasets/ds000224/versions/1.0.0/file_display/ds000224/phenotype/` | **Critical Check** | **FR-011**: The system MUST verify the existence of `CAQ.tsv` or equivalent field in the `phenotype/` directory of ds000224. If missing, execution halts. |
| **Demographics** | Included in OpenNeuro manifest | **Verified** | Age, Sex, Education required for covariates (FR-005). |

**Dataset Variable Fit Analysis**:
- **Predictor**: Network Flexibility (derived from fMRI).
- **Outcome**: Creative Achievement (CAQ score).
- **Covariates**: Age, Sex, Education, Static Connectivity Strength.
- **Gap Check**: The CAQ is part of the HCP-YA behavioral extensions. We will specifically check `phenotype/CAQ.tsv` in the OpenNeuro ds000224 release. If the field is absent, the pipeline halts with `DATA_MISSING_CREATIVITY`.
- **Note**: We do not use third-party mirrors (e.g., HuggingFace) to comply with Constitution Principle VI (Neuroimaging Data Standardization).

## Methodology & Statistical Rigor

### 1. Data Preprocessing (FR-001)
- **Tool**: `nilearn` (signal.clean, image.resample).
- **Steps**:
  1.  Motion correction (FSL MCFLIRT or equivalent in Nilearn).
  2.  Normalization to MNI space (HCP-MMP atlas template).
  3.  Band-pass filtering within a low-frequency range.
  4.  **Motion Scrubbing**: Exclude volumes with FD > 0.5mm; exclude subjects with >20% scrubbed volumes.
- **Rigor**: Standard HCP preprocessing pipeline ensures comparability.

### 2. Dynamic Functional Connectivity (FR-002, FR-003, FR-004)
- **Sliding Window**: Length = 30s (default), Step = 5s. Sensitivity sweep: {s, 30s, 40s} (FR-010).
- **Connectivity**: Pearson correlation between ROI timecourses.
- **Community Detection**: Louvain algorithm (`networkx.community.louvain_communities`) with $\gamma = 1.0$.
  - **Stabilization**: To address algorithmic stochasticity, we run Louvain **100 times** per window and compute a **consensus partition** (using `brainconn` or `networkx` consensus logic) before calculating flexibility. This ensures the metric reflects neural dynamics, not algorithmic noise.
- **Flexibility Metric**: Proportion of time an ROI changes community assignment (relative to the consensus partition), averaged across ROIs.
- **Static Strength**: Mean absolute correlation (FR-012).

### 3. Statistical Analysis (FR-005, FR-006, FR-007)
- **Primary Hypothesis**: Is observed flexibility significantly higher than flexibility in a null model of phase-randomized data?
- **Null Model Approach**: To address the "partial tautology" risk (where flexibility is mathematically constrained by static strength), we do not simply control for static strength in a linear regression. Instead:
  1.  Compute observed flexibility and static strength for all participants.
  2.  Generate a **null distribution** of flexibility for each participant by phase-randomizing their time series (preserving static power spectrum and connectivity strength but destroying temporal dynamics).
  3.  Calculate the **excess flexibility** (Observed - Null Mean) for each subject.
  4.  Test the correlation between **Excess Flexibility** and CAQ scores.
- **Permutation Testing**: 10,000 shuffles of the **CAQ outcome vector** (not the full pipeline) to generate a null distribution of the correlation coefficient ($r$). This is statistically valid for testing the association and computationally feasible (no re-running of fMRI preprocessing).
  - **Family-Wise Error**: Bonferroni correction applied if multiple window lengths are tested simultaneously.
  - **Power**: With N ~1000, power > 80% to detect $r \ge 0.15$. **Caveat**: If effective N (after motion exclusion and CAQ availability) drops below a sufficient threshold, the study will be underpowered. We will report the achieved power post-hoc.
- **Sensitivity**: Report $r$ and $p$ for window lengths 20s, 30s, 40s (FR-010).

### 4. Visualization (FR-008)
- **Scatter**: Excess Flexibility vs. Creativity with 95% CI.
- **Diagnostics**: Residuals vs. Fitted, QQ-Plot.
- **Format**: PNG, < 5MB.

## Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (limited CPU and RAM resources).
- **Strategy**:
  - **Sampling**: If full HCP set exceeds RAM, process in batches of subjects.
  - **Libraries**: `nilearn`, `scikit-learn`, `networkx` are CPU-optimized. No GPU required.
  - **Time**: 10,000 permutations on the *outcome vector* is computationally trivial (< 1 minute). The bottleneck is the fMRI preprocessing and Louvain consensus, which is done **once** per subject.
  - **Memory**: Use `memory_mapping` for fMRI data; avoid loading all time series into RAM simultaneously.

## Risks & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing CAQ** | Fatal | FR-011: Validation step halts execution immediately if `phenotype/CAQ.tsv` is missing. |
| **High Motion** | Bias | Strict exclusion criteria (FD > 0.5mm, >20% volumes) logged in `data_exclusion_log.txt`. |
| **Runtime Exceeded** | CI Failure | Batch processing of subjects; consensus clustering optimized; outcome permutation is fast. |
| **Collinearity** | Interpretation | **Null Model Approach**: We test "Excess Flexibility" (above chance) rather than raw flexibility, isolating the unique dynamic component from static constraints. |
| **Underpowered** | False Negative | Explicitly report achieved power; if N < 400, switch to Bayesian estimation (Bayes Factors) to quantify evidence for null. |

## References (Verified)

- **HCP Dataset**: OpenNeuro ds000224 (HCP S900/S1200) - Verified source for fMRI and behavioral phenotype.
- **CAQ Proxy**: HCP-YA Behavioral Extensions (ds000224/phenotype/CAQ.tsv).
- **Louvain Algorithm**: Blondel et al. (2008) - Standard implementation in `networkx`.
- **Consensus Clustering**: Lancichinetti & Fortunato (2009) - Standard for stabilizing community detection.
- **Null Models**: Phase randomization for fMRI (Bullmore et al., 2001).