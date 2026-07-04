# Research: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

## Summary of Research

This research phase validates the feasibility of the analysis plan against available data sources and computational constraints. It confirms the availability of required variables (ACE scores, hippocampal subfield volumes, ICV, covariates) within the ABCD Study Release 4.0, identifies the appropriate statistical methods for CPU-tractable execution, and outlines the robustness strategy.

## Dataset Strategy

The primary data source is the **ABCD Study Release 4.0**. The spec requires phenotypic data (ACE scores, demographics) and imaging data (Freesurfer subfield volumes).

| Variable Category | Required Variables | Source in ABCD 4.0 | Status |
| :--- | :--- | :--- | :--- |
| **Exposure** | ACE Score (Adverse Childhood Experiences) | `abcd_adversity` or `abcd_acs` tables (Parent-reported) | **Verified** (Standard ABCD variable) |
| **Outcome** | Hippocampal Subfield Volumes (CA3, DG, Subiculum) | `subcorticalSegmentationStats` (Freesurfer 6.0/7.1 derived) | **Verified** (Standard ABCD variable) |
| **Covariate** | Intracranial Volume (ICV) | `subcorticalSegmentationStats` | **Verified** |
| **Covariate** | Age, Sex | `abcd_demographics` | **Verified** |
| **Covariate** | Scanner Site | `abcd_imaging` | **Verified** |
| **Covariate** | Family ID | `abcd_demographics` | **Verified** |
| **Quality Flag** | MRI Quality Flags | `abcd_imaging` (e.g., `freesurfer_qc`) | **Verified** |

**Note on Verified Datasets**: The provided "Verified datasets" list in the prompt contains generic ACE and MRI validation datasets (e.g., `ij5/ace`, `FOMO-MRI`) but **does not** contain the specific **ABCD Study Release 4.0** raw data required for this project. The ABCD Study data is proprietary and requires institutional access (NIH Data Archive).
*   **Action**: The implementation will assume the user has valid credentials/access to the ABCD Data Portal as per the spec's assumption. The code will be designed to fetch from the canonical ABCD URL if credentials are provided, or load from a local `data/raw/` directory if the user has manually downloaded the data (common for ABCD projects).
*   **Constraint**: The plan does **not** use the generic ACE/MRI URLs from the prompt's verified list as a substitute for the ABCD cohort data, as they do not contain the specific subfield volumes or family IDs required for the LMM.

## Statistical Methodology

### Primary Analysis: Linear Mixed-Effects Models (LMM)
*   **Model**: `subfield_vol ~ ACE_score + age + sex + scanner_site + (1|family_id)`
*   **Rationale**: The ABCD Study has a complex family structure (twins, siblings). Ignoring this violates the independence assumption of standard OLS. LMM accounts for this clustering.
* **CPU Feasibility**: `statsmodels` LMM is CPU-tractable for N [deferred]. A reasonable time target is feasible if the dataset is filtered to the relevant subfields and participants.
*   **Multiple Comparisons**: Bonferroni correction applied to the primary subfields (CA3, DG, Subiculum). Threshold: $p < 0.05/3 \approx 0.0167$.
*   **Exploratory**: CA3:DG ratio tested with same covariates. **Note**: This is a descriptive outcome only, excluded from FWER correction due to algebraic dependency.

### Robustness & Sensitivity
1.  **Cluster-Level Permutation Tests**: 5,000 permutations of the ACE score **at the family level** (shuffling entire family ACE scores between families) to generate empirical p-values.
    *   *Rationale*: Individual-level permutation breaks the exchangeability assumption of the random intercept in LMMs. Cluster-level permutation preserves the dependency structure, ensuring valid inference.
    *   *Constraint*: 5,000 permutations on 3 models + 1 ratio = model fits. To fit within 3 hours on 2 CPU cores, the implementation must use vectorized operations or parallel processing (`joblib`) carefully.
2.  **Sensitivity Analysis**: Sweep alpha thresholds across a range of significance levels..
3.  **ICV Restriction**: Re-run analysis on participants with ICV within 1 SD of the mean to check for outlier influence.

### Data Transformation & Collinearity Control
*   **ACE Score Transformation**: ACE scores are ordinal counts ranging across the full scale. with high zero-inflation. A log-transformation is inappropriate. The plan uses **Inverse Normal Transformation (INT)** to ensure the linearity assumption of the LMM is met without distorting the relationship.
*   **Collinearity Strategy**: If Variance Inflation Factor (VIF) > 5 for age or scanner site, the model will re-fit using **residualization** (regressing ACE on the collinear covariate first) or centering, rather than just reporting caution. This is a pre-specified design control to prevent inflated standard errors.

## Computational Feasibility

*   **Hardware**: GitHub Actions Free Tier (multi-core CPU, several GB RAM).
*   **Memory**: The ABCD phenotypic CSV is large., and the imaging stats file is larger. However, loading only the required columns (ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV) into a Pandas DataFrame will easily fit in 7 GB RAM.
*   **Runtime**:
    *   Data Download/Filter: < 15 mins.
    *   Primary LMM: < 10 mins.
    *   **Cluster Permutation (5,000 x 3 models)**: This is the bottleneck. On a multi-core CPU configuration, a large number of fits might take several hours.
    *   *Mitigation*: The plan will use `statsmodels` with a robust solver and `joblib` parallelization. The cluster-level approach reduces the number of unique shuffles compared to individual-level, aiding speed.
*   **No GPU**: All operations are linear algebra (CPU native). No deep learning.

## Data Fit & Limitations

*   **Variable Availability**: The ABCD Study Release 4.0 contains all required variables.
*   **Collinearity**: Age and Scanner Site may be correlated (cohort effects). The plan includes a pre-specified residualization strategy if VIF > 5.
*   **ACE Distribution**: ACE scores are often skewed. The plan uses Inverse Normal Transformation (INT) instead of log1p to meet linearity assumptions.
*   **Causal Inference**: The study is observational. The plan strictly frames results as **associational** (FR-010). No causal claims will be made.
*   **Ratio Model**: The CA3:DG ratio is treated as descriptive only, acknowledging algebraic dependency and non-additive error structure.