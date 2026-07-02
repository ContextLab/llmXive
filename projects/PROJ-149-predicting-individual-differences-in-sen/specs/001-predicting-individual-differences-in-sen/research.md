# Research: Predicting Individual Differences in Sensory Processing Speed from Resting‑State EEG Power Spectra

## Dataset Strategy

The project relies on the following verified datasets. **No other datasets are used.**

| Dataset Name | Verified URL | Usage in Plan | Variable Fit Check |
|--------------|--------------|---------------|--------------------|
| EEG Motor Movement/Imagery (PhysioNet) | ` | Primary source for resting-state EEG. | **Critical Mismatch Risk**: The spec assumes this dataset contains both resting-state EEG and a simple reaction-time task. The verified URL points to a preprocessed PhysioNet dataset typically containing **motor imagery** data, not simple RT. <br><br> **Decision**: The plan will load EEG data from this link. It will attempt to load RT data from the 'RTs Cleaned' dataset below. <br><br> **Feasibility Gate**: If participant IDs do not align, or if the RT dataset lacks a simple RT task, the project **HALTS** with a feasibility report. We do not proceed with disjoint data. |
| RTs (Cleaned) | ` | Source for behavioral reaction times. | See above. |
| LASSO Results (Reference) | ` | Reference for LASSO implementation patterns (not data). | N/A |

**Dataset Fit Conclusion**: The spec assumes a single dataset with *both* EEG and RT. The verified sources provided are separate and likely contain different cognitive tasks (Motor Imagery vs. Simple RT). The plan **must** explicitly handle the case where the datasets are disjoint or incompatible.
* **Plan Adjustment**: The implementation script will first check for a "subject_id" column in both datasets. **Crucially, it will also verify demographic metadata (age/sex) and task type** (simple RT vs. motor imagery) to prevent spurious correlations from ID collisions (e.g., generic sequential IDs). If IDs do not match, or if demographic/task metadata cannot be verified to match, the script will output a "No Match" error and generate a report stating the hypothesis cannot be tested with the *currently available verified data*. This adheres to the "Dataset-variable fit" rule and prevents spurious correlations from ID collisions.

## Methodological Rationale

### Preprocessing (FR-002, FR-003)
- **Filtering**: Band-pass (low-frequency cutoff) removes slow drifts and high-frequency noise. Notch (line frequency) removes line noise.
- **ICA**: Applied to remove ocular artifacts. This is a standard requirement for resting-state analysis (Constitution Principle VI).
- **PSD**: Welch's method with **2-second windows** and **[deferred] overlap** (per Constitution Principle VI). The spec's "[deferred]" overlap is resolved here to [deferred] for standardization.
- **Channel Rejection**: Variance > 3 SD is a robust heuristic for bad channels. Excluding >30% of channels ensures data quality.

### Feature Engineering (FR-010)
- **Relative Power**: Calculating `band_power / total_power` controls for individual differences in skull thickness and overall signal amplitude.
- **Compositional Data Handling**: Relative powers sum to 1.0, creating perfect multicollinearity. The plan **mandates** a **Centered Log-Ratio (CLR) transformation** before modeling to handle this constraint, ensuring coefficients represent effects relative to the geometric mean of other bands. This resolves the compositional data constraint concern.

### Statistical Modeling (FR-005, FR-006, FR-007)
- **Linear & LASSO**: LASSO handles potential multicollinearity among frequency bands and performs feature selection.
- **Bonferroni Correction**: 6 bands tested → threshold = 0.05 / 6 ≈ 0.0083. This controls family-wise error rate.
- **Permutation Test**: A sufficient number of shuffles provide a non-parametric p-value for the R², following the method described in the research plan. () **Crucially**, this is performed on the **held-out test set** (shuffling test labels only) to validate predictive validity without data leakage. The small sample size of the test set is acknowledged as a limitation for permutation power.
- **MDES**: Instead of a tautological post-hoc power analysis, we calculate the **Minimum Detectable Effect Size (MDES)** for the observed N to contextualize null results (e.g., "With N=30, we could only detect R² > 0.15"). This is framed as a descriptive metric of study sensitivity, not a validation of the result.

### Robustness (FR-008, FR-009)
- **Window Size**: Testing varying window lengths ensures results aren't artifacts of the window length.
- **ICA Sensitivity**: Comparing with/without ICA quantifies the impact of artifact removal.
- **Threshold Sweep**: Visualizing significance across p-values (0.01 to 0.10) shows the stability of the finding.

## Computational Constraints & Mitigation
- **Memory**: The plan processes data participant-by-participant or in small batches to avoid loading the entire dataset into RAM at once if it exceeds available memory capacity.
- **Runtime**: Permutation tests (a large number of shuffles) are vectorized using NumPy to ensure they complete within a reasonable time limit.
- **No GPU**: All models (`LinearRegression`, `Lasso`) are from `scikit-learn`, which runs natively on CPU. No CUDA or mixed-precision libraries are used.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Mismatch** (EEG and RT from different subjects) | **Fatal** | Plan includes explicit ID and **demographic/task metadata alignment check** (Phase 0.5). If failed, report "No matched data" and halt. Do not fabricate links. |
| **Spurious Correlation** (ID collision in separate datasets) | **Fatal** | Verify demographic metadata (age/sex) and task type. If missing or mismatched, flag correlation as potentially spurious and halt. |
| **Small Sample Size** | Low Power | Report MDES and effect sizes with CIs. Frame results as exploratory if N is insufficient for R²=0.10. |
| **Non-Stationarity of EEG** | Feature Noise | Use epochs of sufficient duration to ensure stable PSD. and CLR-transformed relative power to normalize. |
| **Collinearity of Bands** | Model Instability | Use CLR transformation to handle compositional constraints; use LASSO for feature selection. |
| **Construct Validity** (Motor Imagery vs. Simple RT) | **Fatal** | Explicitly verify task type in RT dataset. If it is motor imagery, the hypothesis (sensory processing speed) is invalid for this data. Halt. |