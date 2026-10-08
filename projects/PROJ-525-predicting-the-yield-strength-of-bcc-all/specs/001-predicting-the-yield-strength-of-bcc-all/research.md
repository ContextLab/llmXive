# Research: Predicting Yield Strength of BCC Alloys

## Overview

This research investigates the relationship between elemental composition and yield strength in BCC alloys using machine learning. The study leverages public datasets to engineer compositional descriptors and train regression models, adhering to strict data hygiene and reproducibility standards.

## Dataset Strategy

### Verified Datasets

The following datasets are the **only** sources permitted for this project. URLs are cited exclusively from the verified list provided in the prompt.

| Dataset Name | Verified URL | Status | Notes |
| :--- | :--- | :--- | :--- |
| **MPEA Database** | *NO verified source found* | **Critical Gap** | The spec requires the MPEA database (DOI: 10.1038/s41597-020-00768-9). No direct, open, programmatic download URL was verified. The implementation MUST attempt to fetch via DOI resolver or standard academic repository (e.g., Figshare/Scientific Data) and fail gracefully if not open. |

**Decision/Rationale**:
The primary source is the MPEA database. Since no verified direct URL exists, the `download.py` script will:
1. Attempt to resolve the DOI `10.1038/s41597-020-00768-9` using the `crossref` API or direct HTTP GET to the publisher's landing page to locate the data file.
2. **Yield Definition Verification**: Upon download, the script MUST inspect the raw data to confirm the specific definition of "Yield Strength" (e.g., [deferred] offset, strain rate). If the definition is missing, ambiguous, or non-standard, the pipeline MUST halt with a clear error message "YIELD_DEFINITION_INVALID: Source data lacks standard yield strength definition". This ensures construct validity.
3. If the data is behind a paywall or requires registration (a fatal feasibility flaw per the plan guidelines), the system MUST halt and report "DATA_UNAVAILABLE: MPEA requires access credentials".
4. **No Fallback**: No fallback to HuggingFace datasets is permitted. The fallback datasets listed in previous iterations (e.g., 'bccnf/MeLiDC', 'Francesco/bccd') were either NLP datasets or unverified community uploads with no guarantee of containing the required 'Yield Strength' and 'BCC' columns. Using them would violate construct validity. If MPEA is inaccessible, the research question cannot be answered with public data, and the pipeline halts.

**Dataset-Variable Fit**:
- **Required Variables**: Elemental composition (atomic %), Yield Strength (MPa), Crystal Structure (BCC).
- **MPEA**: Confirmed to contain these variables in the literature. The MPEA database specifically reports yield strength, but the *specific offset method* must be verified from the raw data to ensure construct validity.
- **Risk**: If no open dataset contains both composition and yield strength for BCC alloys, the research question cannot be answered with public data. This will be flagged as a "Data Scarcity" failure.

## Statistical Rigor

### Multiple Comparison Correction
- **Method**: Bonferroni correction applies to the family of pairwise model comparisons (RF vs GB, RF vs Ridge, GB vs Ridge) on the primary R² metric. Hyperparameter tuning is limited to a single best configuration per model type to avoid overfitting the validation set in small N scenarios. This approach prioritizes Family-Wise Error control over Type II error, which is acceptable for this exploratory study with limited N.

### Sample Size & Power
- **Justification**: The spec mandates a minimum of 80 samples (FR-004). This is a hard stop. If N < 80, the pipeline halts. This threshold is derived from the spec's requirement for stratified splitting and statistical validity.
- **Limitation**: The plan acknowledges that 80 samples is a small dataset for complex ML. The use of **Repeated 5-Fold CV** (n_repeats=10) is specifically chosen to stabilize the *mean* performance estimate and provide a bootstrap distribution for confidence intervals. However, the plan explicitly states that statistical power is limited and results are exploratory. Repeating the k-fold CV 10 times reduces the variance of the *mean* estimate, but does not reduce the variance of the *estimator* itself due to data sparsity. No false claims about variance reduction factors are made.

### Causal Inference
- **Assumption**: This is an **observational** study. The plan explicitly states that results are **associational**. No causal claims (e.g., "Element X causes higher strength") will be made.
- **Feature Importance**: Reported feature importance is strictly for predictive ranking and MUST NOT be interpreted as causal effect in observational data.

### Measurement Validity
- **Instruments**: Yield strength values are taken directly from the source dataset. The plan does NOT assume a standard offset but explicitly verifies the definition from the raw data. If the definition is not standard (e.g., [deferred] offset), the pipeline halts.
- **Descriptors**: Atomic radius, electronegativity, and valence are sourced from standard periodic table references (e.g., `periodictable` library) to ensure consistency and reproducibility.
- **Thermodynamic Parameters**: Binary interaction parameters (Ω_ij) are sourced from a local `data/raw/nist_janaf_params.json` file included in the repository, as no verified public URL exists. This local file is versioned and checksummed to ensure reproducibility.

### Predictor Collinearity
- **Issue**: Compositional data sums to 1.0 (closure), causing inherent multicollinearity.
- **Mitigation**: The plan mandates **ILR transformation** (FR-003.1) to map compositions to Euclidean space, addressing closure. Additionally, **L1/RFE feature selection** (FR-003.2) will be used to remove redundant features.
- **Reporting**: If scalar descriptors (e.g., mixing enthalpy) are highly correlated with ILR features, the plan will report the correlation matrix. If L1/RFE removes all ILR or all Scalar features, the pipeline **MUST HALT** (see ComplementarityFailureContract) to enforce FR-003.1's 'complement' requirement. Retraining with a single set is not permitted as it would violate the spec and obscure physical interpretability.

## Compute Feasibility

- **CPU-First Strategy**: All models (Random Forest, Gradient Boosting, Ridge) are available in `scikit-learn` and run efficiently on CPU.
- **Scaling**: The dataset is expected to be < 10k rows. Feature engineering (O(N*P)) and training (O(N*P*depth)) will fit within 7 GB RAM and 6 hours.
- **No GPU Required**: No deep learning (transformers) is planned. The "GPU escape hatch" is not needed for this specific methodology.

## Data Availability Plan

1. **Primary**: Attempt to download MPEA via DOI resolver.
2. **Verify**: Inspect raw data for yield strength definition. Halt if invalid.
3. **Halt**: If MPEA is inaccessible or yield definition is invalid, halt with "DATA_UNAVAILABLE" or "YIELD_DEFINITION_INVALID". No fallback datasets are used.
4. **Stream**: If the dataset is large (unlikely for this scope), use `datasets.load_dataset(..., streaming=True)` to avoid loading all into RAM.
5. **Sample**: If the full dataset exceeds compute limits, a fixed-seed random sample will be taken, with power limitations noted.
6. **No Synthesis**: No synthetic data will be generated. If data is missing, the pipeline halts.

## Contingency Plan

**Scenario**: MPEA database is inaccessible (paywall, broken DOI, missing data).
**Action**:
1. The `download.py` script will attempt to resolve the DOI.
2. If the data file cannot be retrieved, the script will log "DATA_UNAVAILABLE: MPEA requires access credentials" and exit with code 1.
3. **No Fallback**: The project will not proceed with alternative datasets (e.g., HuggingFace NLP datasets) as they lack the required physical definitions (Yield Strength, BCC phase).
4. **Report**: A final report will be generated stating that the research question could not be answered due to data inaccessibility.

This contingency ensures the project halts gracefully rather than failing silently or using invalid data, maintaining scientific integrity.