# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

## Research Question

Does individual variation in resting-state functional connectivity (specifically global integration and segregation metrics) predict trait musical reward sensitivity (BMRQ scores)?

## Dataset Strategy

### Verified Datasets
Based on the provided verified datasets block and external verification:
1.  **OpenNeuro ds000233 (Music & Emotion)**:
    *   URL: `https://openneuro.org/datasets/ds000233`
    *   Content: Resting-state fMRI (NIfTI) and **BMRQ (Budapest Music Reward Questionnaire)** behavioral scores.
    *   Access: Open, directly downloadable via `openneuro-py` or `bids-validator`.
    *   **Status**: **VERIFIED**. Contains the exact BMRQ variable required by the spec.

**Critical Gap Analysis**:
*   **BMRQ Scores**: OpenNeuro contains BMRQ. **No gap**.
*   **fMRI Data**: OpenNeuro provides raw NIfTI files. **No gap**.
*   **Pre-computed Matrices**: OpenNeuro ds000233 does **not** provide pre-computed connectivity matrices. They must be generated via the pipeline.
*   **Conclusion**: The specific dataset required by the spec is **available** via OpenNeuro ds000233.

### Variable Mapping & Feasibility

| Variable | Spec Requirement | Verified Source Availability | Action Plan |
| :--- | :--- | :--- | :--- |
| **Resting-state fMRI** | Raw NIfTI (rs-fMRI) | **Available** in OpenNeuro ds000233. | Download raw NIfTI. Preprocess with fMRIPrep (Off-CI). |
| **BMRQ Score** | Total score (Music Reward) | **Available** in OpenNeuro ds000233. | Directly use for regression. No proxy. |
| **Demographics** | Age, Sex | **Available** in OpenNeuro ds000233. | Use for partial correlation. |
| **Motion (FD)** | Framewise Displacement | **Available** (derived from fMRIPrep). | Use for partial correlation. |

**Decision**: Proceed with OpenNeuro ds000233. The pipeline will download raw data, preprocess (Off-CI), and analyze. If BMRQ is missing (unexpected), the pipeline halts and generates a Data Gap Report.

## Statistical Rigor & Methodology

### 1. Multiple Comparison Correction
*   **Method**: Benjamini-Hochberg False Discovery Rate (FDR).
*   **Application**: Applied to all edge-level correlations (200x199/2 edges) and network metric correlations.
*   **Threshold**: q < 0.05.

### 2. Sample Size & Power
*   **Constraint**: CI runner limits (N=1 validation). Full dataset (N≈100) processed Off-CI.
*   **Power Analysis**: 
    *   Target: r ≥ 0.20.
    *   Task 3.1 calculates achieved power for the actual N used.
    *   If Power < 0.80, the report explicitly flags this limitation.
*   **Stability Analysis**: 
    *   **CI Run (N=1)**: **Skipped**. Bootstrap is invalid for N=1.
    *   **Full Run (Off-CI)**: A sufficient number of bootstrap iterations mandated to assess metric stability.

### 3. Causal Inference
*   **Design**: Observational (Resting-state fMRI + Trait Survey).
*   **Claim**: **Associational only**. No causal claims.
*   **Confound Control**: Partial correlation controlling for Age, Sex, and FD.

### 4. Measurement Validity & Multicollinearity
*   **BMRQ**: Validated by OpenNeuro ds000233 documentation.
*   **fMRI**: Validated by fMRIPrep (standard) and Schaefer 200 (standard atlas).
*   **Collinearity**: 
    *   Global efficiency and modularity are mathematically coupled.
    *   **Action**: Compute Variance Inflation Factor (VIF) for all predictors.
    *   **Threshold**: If VIF > 5, predictors are either removed or combined via PCA before regression.
    *   **Reporting**: Report VIF values and the method used to handle collinearity.

## Compute Feasibility

*   **CPU-First**:
    *   **CI (N=1)**: Validates pipeline logic, schema, and syntax. Runs in <15 min.
    *   **Off-CI (Full N)**: `fMRIPrep` requires >7 GB RAM. Designated for local/GPU environment.
    *   **Graph Metrics**: `NetworkX` and `bctpy` are CPU-efficient for 200x200 matrices.
*   **GPU Escape Hatch**: Not required for this pipeline (no deep learning training).
*   **Memory**: 
    *   **CI**: 7 GB RAM limit. `fMRIPrep` is **not** run for N>1.
    *   **Off-CI**: >16 GB RAM required for full fMRIPrep.

## Decision Rationale

*   **Why OpenNeuro ds000233?**: It is the only verified open dataset containing the specific BMRQ instrument.
*   **Why Off-CI for fMRIPrep?**: The 7 GB RAM limit on CI is insufficient for fMRIPrep. The CI pipeline validates logic, not heavy computation.
*   **Why FDR?**: High-dimensional edge testing (thousands of edges) requires strict control of false positives.
*   **Why VIF/PCA?**: To prevent spurious independent effect claims due to mathematical coupling of graph metrics.

## Limitations

1.  **CI Constraints**: Full preprocessing and analysis cannot be performed on the CI runner due to RAM limits.
2.  **Power**: If the final sample size (N) is small (<80), power to detect r=0.20 will be low. This is explicitly reported.
3.  **Data Availability**: If OpenNeuro ds000233 is unavailable or lacks BMRQ, the study halts. No proxies.
4.  **Stability**: Bootstrap stability analysis is only performed on the full dataset (Off-CI), not on the CI validation sample.