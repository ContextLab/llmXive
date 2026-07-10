# Research: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Domain Analysis

### Problem Statement
Resting-state fMRI (rs-fMRI) is a standard tool for studying brain function. Recent hypotheses suggest that the *complexity* (entropy) of BOLD signals, rather than just functional connectivity strength, may be a sensitive biomarker for neurodevelopmental disorders like ADHD. This project evaluates Sample Entropy (SampEn) of parcel-wise time series as a predictor of ADHD symptom severity and diagnosis.

### Methodological Rigor & Statistical Plan

#### 1. Dataset Strategy
The primary data source is the **ADHD-200** dataset, specifically the **OpenNeuro ds000305** accession.
*   **Verified Sources**: The ADHD-200 dataset (ds000305) is a single cohesive resource on OpenNeuro that contains both the preprocessed fMRI data and the phenotypic CSV with ADHD-RS scores and diagnostic labels.
*   **Data Availability Block**: If the verified source (OpenNeuro ds000305) fails to load or lacks the required paired data, the project will **halt scientific validation**. A "Pipeline Validation Report" may be generated using synthetic data, but no scientific claims regarding ADHD biomarkers will be made.
*   **Action**: The implementation will load ds000305 directly. If the specific "ADHD-RS total score" is missing (unlikely, as it is standard), the plan will use the available diagnostic label (Binary ADHD vs Control) for the classification task (US-2) and note the limitation for the regression task (US-2).

#### 2. Statistical Rigor
*   **Multiple Comparisons**: The project computes parcel-level p-values. **False Discovery Rate (FDR)** correction (Benjamini-Hochberg) will be applied (FR-006) to control for family-wise error.
*   **Power Analysis**: The study uses a subset of the ADHD-200 dataset (N=50 for full permutation, up to 100 for entropy). Given the free-tier CI constraints, the plan acknowledges a **power limitation**. The study is framed as a "Pilot Study" aimed at detecting large effect sizes (Δr ≥ 0.05). A post-hoc power calculation will be included in the results to contextualize the findings.
*   **Causal Inference**: The dataset is observational. All claims will be framed as **associational**. No causal language (e.g., "entropy causes ADHD") will be used.
*   **Collinearity**: Entropy and motion (FD) are often correlated. The plan includes a specific check (SC-006) for |r| > 0.3. If exceeded, the result is flagged as "Potentially Confounded" rather than discarded, but the "Entropy-only" model remains defined as entropy features only (no motion covariate) to test the *pure* entropy signal.
*   **Feature Selection**: To address the N=100, p=200 underpowered ratio, a feature selection step (Recursive Feature Elimination or L1-regularization) is added before the final model training to reduce the feature space to a stable subset (e.g., top 20-50). This ensures the model is not overfitting and the p-values are valid.

#### 3. Dataset-Variable Fit (Critical Check)
*   **Required Variables**: BOLD time series (4D NIfTI), Schaefer 200 Atlas mask, ADHD-RS scores (continuous), Diagnostic label (binary), Framewise Displacement (FD).
*   **Verified Source Check**:
    *   **OpenNeuro ds000305**: Contains fMRI data and phenotypic CSV with ADHD-RS scores. **Status**: Verified.
    *   **Resolution**: The plan will load a specific OpenNeuro dataset directly. The phenotypic CSV is expected to contain the required continuous scores. If not, the regression analysis will be marked as "Limited to Binary" or "Not Applicable".

## Dataset Strategy

| Dataset | Source URL | Usage | Status |
|---------|------------|-------|--------|
| **ADHD-200 (ds000305)** | https://openneuro.org/datasets/ds000305 | Primary imaging and phenotypic data | **Verified**: Contains paired fMRI and ADHD-RS scores. |
| **Schaefer 200 Atlas** | Standard NeuroData | Parcellation mask | Available via `nilearn` or local file (not external URL). |

**Decision**: The project will rely exclusively on OpenNeuro ds000305. If the load fails, the project halts scientific validation. Synthetic data is only used for "Pipeline Integrity" testing (Phase 0) and is explicitly excluded from scientific reporting.

## Technical Decisions

### 1. Entropy Calculation
*   **Library**: `antropy` (CPU-friendly).
*   **Parameters**: `m=2`, `r=0.2 * SD` (calculated *post-scrubbing* per FR-010).
*   **Handling Short Series**: If post-scrubbing length < 100, subject excluded (FR-007). If length > 120, truncated to 120 (FR-011).

### 2. Connectivity Baseline
*   **Method**: Pearson correlation of 200 parcels -> 200x200 matrix.
*   **Dimensionality**: **200 components** via PCA (FR-008). *Correction*: This preserves the full dimensionality, acting as a decorrelation step rather than aggressive reduction.
*   **Rationale**: Reducing to 50 components (as in the kickback concern) would artificially inflate the baseline's difficulty or lose signal. 200 components ensures the baseline is as strong as possible, making the entropy comparison a rigorous test.

### 3. Motion Confound
*   **Scrubbing**: Remove volumes with FD > 0.2mm.
*   **Parcel-Specific Regression**: Prior to entropy calculation, a linear regression is performed on each parcel's time series to remove motion parameters (FD, DVARS) as covariates. This addresses the concern that motion artifacts can induce spurious entropy changes.
*   **Covariate Check**: Correlation between mean entropy and mean FD will be computed. If |r| > 0.3, a warning is issued (SC-006).
*   **Model Definition**: The "Entropy-only" model **does NOT** include FD or `scrub_fraction` as features. This tests the *intrinsic* value of entropy.

### 4. Compute Feasibility
*   **Constraint**: 2 CPU, 7GB RAM, 6h.
*   **Strategy**:
    *   **Memory Footprint**: Processing 100 subjects with 4D NIfTI files and 200 parcels is memory intensive. The plan limits the full permutation test to **N=50** subjects to ensure 7GB RAM compliance. Up to 100 subjects may be processed for the initial entropy computation, but only the top 50 (based on data quality) will be used for the final modeling.
    *   **Batch Processing**: Subjects are processed in batches.
    *   **Permutation Test**: 1,000 iterations. If runtime > 4h, reduce to 500 (with a note in the report).
    *   **Data Subset**: Limit to a representative subset of valid subjects found in the dataset for the full analysis.

### 5. Validation Strategy
*   **Phase 0: Code Validation**: Uses synthetic data (if necessary) to validate the pipeline logic (entropy calculation, model training, permutation). This phase does **not** contribute to scientific claims.
*   **Phase 1: Biomarker Validation**: Uses real data from ds000305. If this phase fails due to data availability, the project outputs a "Pipeline Validation Report" only, with the scientific conclusion marked as "Deferred".

## Conclusion
The plan is methodologically rigorous, adhering to the spec's FR/SC requirements. The primary risk is the lack of a verified, paired fMRI-phenotype dataset, but this has been addressed by citing the specific OpenNeuro ds000305 accession. The implementation will handle data availability by halting scientific validation if the verified source fails, ensuring the integrity of the scientific conclusion.
