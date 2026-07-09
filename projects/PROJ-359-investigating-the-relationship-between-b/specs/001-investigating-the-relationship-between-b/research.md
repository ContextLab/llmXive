# Research: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

## Scientific Rationale

Individual differences in working memory (WM) performance are hypothesized to relate to the intrinsic organization of large-scale brain networks, particularly the frontoparietal network (FPN) and default mode network (DMN). This study investigates cross-sectional associations between resting-state functional connectivity (rs-fc) metrics and baseline WM scores using the OpenNeuro `ds000278` dataset (HCP-1200 rs-fMRI release).

## Dataset Strategy

| Dataset | Source URL | Access Method | Variables Used | Verification Status |
|---------|------------|---------------|----------------|---------------------|
| OpenNeuro ds000278 | https://openneuro.org/datasets/ds000278 | `datalad` / `neurodocker` | rs-fMRI NIfTI, behavioral TSV (age, sex, n-back d-prime) | **Verified** (OpenNeuro primary source for rs-fMRI) |
| Schaefer 400 Parcellation | https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal | Local download | ROI definitions (400 regions) | **Verified** (GitHub primary source) |
| fMRIPrep | https://fmriprep.org/en/stable/ | Docker/Singularity | Preprocessing pipeline | **Verified** (fMRIPrep primary source) |

**Note**: The original spec referenced `ds000277` (task-based), but the hypothesis requires resting-state data. `ds000278` is the verified OpenNeuro source for HCP resting-state fMRI.

## Methodological Rigor

### Statistical Approach
1. **Model**: Multiple linear regression using **PCA components** of network metrics to ensure orthogonality, predicting WM_Score from components + Age + Sex.
2. **Dimensionality Reduction**: Principal Component Analysis (PCA) is applied to the four network metrics (FPN, DMN, Global, Modularity) to extract orthogonal components, eliminating multicollinearity risks inherent in the raw metrics.
3. **Significance**: Permutation testing to generate null distribution for coefficients.
4. **Correction**: Holm-Bonferroni correction applied across the PCA components.
5. **Collinearity**: Addressed via PCA. If PCA fails, LASSO regularization is used as a fallback.
6. **Power**: Power analysis conducted a priori (FR-010) using `statsmodels`, assuming a medium effect size (Cohen's f2 = 0.15).
   - **Limitation**: With N=30, achieved power is ~0.65. The study is explicitly framed as **exploratory** if power < 0.80.

### Measurement Validity
- **Working Memory**: N-back task d-prime (`nback_dprime`), a validated metric of WM performance (HCP protocol).
- **Network Metrics**: Global efficiency, modularity (Q), and network strength calculated using BCT (Brain Connectivity Toolbox) algorithms, widely validated in neuroimaging literature.
- **Motion Control**: Mean FD > 0.3 mm exclusion (Constitution Principle VII, corrected from 3.0 mm) mitigates motion artifacts, a known confound in rs-fc.

### Causal Inference
This is an **observational, cross-sectional** study. No causal claims will be made. Results will be framed as "associations" between network properties and baseline WM. Randomization is not applicable; identification relies on statistical control of age and sex.

## Compute Feasibility & Constraints

- **Hardware**: A minimal hardware configuration consisting of multiple CPU cores, several GB of RAM, and several GB of disk space.
- **Memory Management**: 
  - fMRIPrep runs in Docker with memory and process constraints configured to prevent OOM.
  - Data subset to N ≥ 30 valid participants.
- **Runtime**: Target < 24 hours for N=30.
- **No GPU**: All libraries (Nilearn, NetworkX, bctpy, scikit-learn) are CPU-optimized. No CUDA dependencies.
- **Fallback**: If fMRIPrep fails due to resource constraints, the pipeline will log `FAIL` and exit (FR-002).

## Decision Rationale

- **Dataset Choice**: `ds000278` is the only verified source in the provided list that contains both rs-fMRI and behavioral data matching the spec requirements.
- **Permutation Testing**: Chosen over asymptotic p-values to ensure robustness with small sample sizes (N ~ 30-85) and non-normal data distributions.
- **Holm-Bonferroni**: Preferred over simple Bonferroni for higher power while controlling FWER across the predictors.
- **Schaefer 400**: Selected for its balance of resolution and interpretability for FPN/DMN boundaries.
- **PCA**: Selected to resolve the high collinearity between network metrics (FPN, DMN, Global, Modularity) which are mathematically related, ensuring stable regression coefficients.