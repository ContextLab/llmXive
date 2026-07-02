# Research: The Impact of Simulated Social Exclusion on Neural Responses to Reward

## Problem Statement

Does brief simulated social exclusion (via Cyberball) modulate neural activity in reward-related brain regions (ventral striatum, orbitofrontal cortex) during subsequent monetary reward anticipation and receipt?

## Dataset Strategy

The analysis requires a dataset containing:
1. **Social Exclusion Paradigm**: Cyberball or similar ostracism task with explicit "Excluded" vs. "Included" conditions.
2. **Reward Task**: Monetary Incentive Delay (MID) or similar task with distinct "Anticipation" and "Receipt" events.
3. **fMRI Data**: BIDS-compliant NIfTI images and JSON metadata.
4. **Behavioral Data**: Condition labels for each participant.

### Verified Datasets

Based on the provided "Verified datasets" block, **NO single verified dataset currently listed contains the specific combination of Social Exclusion (Cyberball) + Reward Task fMRI data required for this study.**

- **OpenNeuro (parquet)**: `
 - *Status*: This is a processed/parquet representation of OpenNeuro data. It does not explicitly confirm the presence of both Cyberball and MID tasks in the same subjects with group labels.
- **NIfTI (gzip)**: `
 - *Status*: Contains lung cancer radiomics data, not social neuroscience.
- **MNI (parquet)**: `
 - *Status*: MNIST digit recognition, irrelevant.
- **Other datasets**: BOLD, GLM, FWHM, MID, etc., listed in the block are either text-based, generic embeddings, or unrelated to the specific fMRI paradigm required.

### Critical Gap & Mitigation: Merged Dataset Strategy

**Gap**: The "Verified datasets" block does **not** contain a verified source for a dataset with both Cyberball and MID tasks in the same subjects. The spec assumes `ds000246` or `ds003195` are available, but these are **not** in the verified list as dual-task datasets.

**Mitigation Strategy**:
1. **Pivot to Merged Datasets**: The plan will attempt to merge two separate, verified datasets:
 - **Exclusion Dataset**: e.g., `ds000246` (if verified to contain Cyberball) or another verified exclusion dataset.
 - **Reward Dataset**: e.g., `ds004738` (or similar verified reward dataset).
2. **Confound Control**: To address inter-dataset variability (scanners, populations), the analysis will:
 - Include 'Dataset ID' as a **random effect** in the second-level mixed-effects model.
 - Match demographics (age, sex) between datasets where possible.
 - Explicitly acknowledge the limitations of this approach in the final report.
3. **No Synthetic Data**: **Synthetic data is NOT used** for primary analysis or validation. Generating synthetic data to mimic the hypothesis would be tautological and scientifically invalid. If no compatible real datasets are found, the study is paused or pivots to a meta-analysis of separate studies.

*Note: If the implementation agent finds a valid OpenNeuro dataset ID (e.g., ds000246) via external search not captured in this block, it must update the `research.md` and `plan.md` before execution. For this plan, we assume the "Verified datasets" block is the sole source of truth and proceed with the Merged Dataset Strategy.*

## Methodological Approach

### 1. Preprocessing (CPU-Tractable)
- **Tool**: `fmriprep` (CPU-only mode) or `nipype` wrappers for FSL/SPM equivalents if `fmriprep` fails memory constraints.
- **Steps**:
 1. Slice Timing Correction.
 2. Realignment (Motion Correction).
 3. Coregistration to T1.
 4. Normalization to MNI152 space (non-linear).
 5. Smoothing: Gaussian kernel with a primary full-width at half-maximum (FWHM) suitable for the expected spatial scale, with sensitivity analysis at narrower and wider kernel widths.
- **Constraint**: Process participants in batches of 5 to stay within 7 GB RAM. Use `--nthreads <N> --mem-mb 6000` flags, where N represents a configurable number of threads.

### 2. First-Level GLM
- **Model**: Standard GLM with regressors for:
 - Reward Anticipation (cue).
 - Reward Receipt (outcome).
 - Motion parameters (6).
 - **Temporal Autocorrelation**: AR(1) pre-whitening to account for fMRI noise structure.
 - High-pass filter.
- **Output**: Beta maps for Anticipation and Receipt per participant.

### 3. ROI Extraction
- **ROIs**:
 - Ventral Striatum (VS): AAL atlas mask.
 - Orbitofrontal Cortex (OFC): Harvard-Oxford atlas mask.
- **Method**: Extract mean beta value within the mask for each event type.

### 4. Second-Level Analysis
- **Test**: Two-sample t-test (Excluded vs. Included) for each ROI × Event combination.
- **Correction**: Bonferroni correction ($\alpha = 0.05 / 4 = 0.0125$).
- **Effect Size**: Cohen's $d$.
- **Framing**: Associational ("Exclusion is associated with reduced activation").
- **Confound Control**: Include 'Dataset ID' as a random effect if datasets are merged.

### 5. Sensitivity Analysis
- **Variables**: Smoothing (4, 6, 8mm); ROI mask probability thresholds (if applicable).
- **Metric**: Consistency of direction and significance of the primary finding across threshold combinations.

## Statistical Rigor & Power

- **Multiple Comparisons**: Bonferroni correction explicitly applied for 4 tests (2 ROIs × 2 events).
- **Power**: Target $N \ge 20$ per group for [deferred] power to detect medium effect ($d=0.5$). If $N < 20$, results are exploratory and a 'Power Limitations Report' is generated.
- **Causal Inference**: Since the data is observational (public dataset) or merged, claims are framed as **associational**. The experimental manipulation (Cyberball) is acknowledged, but the neural outcome is treated as an association.
- **Collinearity**: Motion parameters included as nuisance regressors. Temporal autocorrelation modeled via AR(1).

## Risks & Assumptions

- **Risk**: No compatible datasets found. **Mitigation**: Study paused or pivots to meta-analysis. No synthetic data.
- **Risk**: Inter-dataset variability swamps effect. **Mitigation**: Random effects model; explicit limitation reporting.
- **Risk**: Memory overflow on CPU. **Mitigation**: Batch processing, downsampled resolution if necessary.
- **Assumption**: OpenNeuro datasets (if found) are BIDS-compliant.
- **Assumption**: 6mm smoothing is appropriate for ROI analysis.
- **Assumption**: Merging separate datasets is methodologically valid with appropriate confound controls.