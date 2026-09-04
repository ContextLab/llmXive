# Research: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Dataset Strategy

The project relies on a publicly available EEG dataset that contains **both** "simple oddball" and "complex auditory scene" conditions as *independent* experimental variables.

### Verified Datasets
Based on the `# Verified datasets` block provided in the project context:

| Dataset Name | Verified URL | Status | Notes |
|--------------|--------------|--------|-------|
| EEG (Resting/Events) | `https://huggingface.co/datasets/neurofusion/eeg-restingstate/resolve/main/events.csv` | **Verified** | Contains event markers; **UNSUITABLE** for MMN (lacks structured oddball/complex paradigm). **Excluded from valid data path.** |
| Seizure EEG (Train/Eval) | `https://huggingface.co/datasets/JLB-JLB/seizure_eeg_train/...` | **Verified** | Focused on seizures; **UNSUITABLE** for MMN. |
| OpenNeuro (fSLR64k) | `https://huggingface.co/datasets/clane9/openneuro-fslr64k/...` | **Verified** | Structural/functional MRI data; **NOT EEG**. |
| OpenNeuro ds000246 | **NO verified source in block** | **Reference Only** | Canonical Auditory Oddball dataset. **Lacks "complex" condition.** **Excluded from primary hypothesis path.** |

**Critical Gap Analysis**:
The spec requires a dataset with **both** "simple oddball" and "complex auditory scene" conditions.
- The **neurofusion/eeg-restingstate** dataset is resting-state; it lacks the structured stimulus events (standard/deviant) required to calculate MMN. **It is excluded from the valid data path.**
- The **OpenNeuro ds000246** is a standard oddball dataset. It typically contains only "simple" conditions (standard vs. deviant). It **does not** contain a "complex" auditory scene condition.
- **Decision**: The plan **cannot** proceed with ds000246 as the primary source for the *complexity* hypothesis.
- **Action**: The implementation MUST attempt to find an alternative open dataset with both conditions (e.g., a specific complex auditory scene dataset on OpenNeuro or Zenodo).
- **Fallback**: If no such dataset is found, the pipeline **HALTS** with the error: "Dataset lacks required 'complex' condition; research question untestable with current data."
- **No Synthetic Fallback**: Synthetic data is **NOT** permitted for scientific results. It may only be used to unit-test the *code logic* (mocking) in `tests/`.

### Data Acquisition Plan
1.  **Search**: Attempt to locate a dataset with both "simple" and "complex" conditions via OpenNeuro/Zenodo search (manual or script).
2.  **Verify**: Check `participants.tsv` and `events.tsv` for `condition_label` (simple/complex) and `stimulus_type` (standard/deviant).
3.  **Validate**: Ensure `condition_label` is an independent experimental variable, not a heuristic mapping of `stimulus_type`.
4.  **Halt**: If "complex" is missing or derived heuristically from "deviant", halt.

## Statistical Methodology

### MMN Quantification (FR-004)
- **Metric**: Mean amplitude difference (Deviant - Standard) in the **150–250 ms** window.
- **Latency**: Peak time of the difference waveform in the same window.
- **Electrodes**: Fronto-central cluster (e.g., Fz, FCz, Cz, F3, F4, FC3, FC4).
- **Baseline Correction**: Pre-stimulus period (-200 to 0 ms).
- **Signal Validity (SC-001)**: Calculate the baseline noise floor (standard deviation of pre-stimulus period). Compute SNR = `|mean_amplitude| / std_baseline`. Signal is valid if SNR ≥ 2.0.

### Statistical Testing (FR-005, SC-002, SC-003)
- **Design**: **Two-Way ANOVA** or **Linear Mixed Model (LMM)** with factors: `Condition` (Simple, Complex) and `Stimulus` (Standard, Deviant).
- **Primary Hypothesis**: Test for the **Interaction Effect** (`Condition * Stimulus`). This tests if the MMN (Deviant-Standard) differs between Simple and Complex conditions.
- **Correction**: **FDR (Benjamini-Hochberg)** across all tested electrodes.
- **Effect Size**: Cohen's *d* calculated for the interaction effect.
- **Benchmark (SC-003)**: Compare Cohen's *d* against a literature benchmark (e.g., **d ≥ 0.5** from Näätänen et al., 2007) to determine practical significance.
- **Validity**: If "complex" condition is not an independent experimental variable, the test is invalid and the pipeline halts.

### Topographic Consistency (SC-004)
- **Metric**: Pearson correlation coefficient (r) between the observed topography and a **canonical MMN topography template**.
- **Template Source**: A pre-computed template from a verified literature source or a canonical dataset (separate from ds000246 for the complex condition).
- **Threshold**: r ≥ 0.8 indicates high consistency.
- **Fallback**: If no template exists for the "complex" condition, report "N/A" and do not calculate.

## Compute Feasibility & Resource Management

- **Environment**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM, 6h limit).
- **Strategy**: **CPU-First**.
  - MNE-Python and statsmodels are optimized for CPU.
  - Data will be processed in **chunks** or **streamed** if the dataset > 7 GB.
  - No GPU required for MMN analysis.

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Dataset Mismatch** | HALT if "complex" condition is missing or derived heuristically. No synthetic data for results. |
| **Circular Logic** | Explicit check: If `condition_label` == `stimulus_type`, HALT. |
| **Excessive Artifacts** | Exclude subjects with >50% rejected epochs; log exclusion count. |
| **Missing Channels** | Interpolate <10% missing channels using spherical splines. |
| **Multiple Comparisons** | Mandatory FDR correction. |
| **Template Missing** | Report "N/A" for SC-004 if no canonical template is available. |