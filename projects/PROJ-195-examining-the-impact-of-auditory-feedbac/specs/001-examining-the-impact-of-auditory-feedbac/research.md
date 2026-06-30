# Research: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Dataset Strategy

The analysis relies on the **OpenNeuro `ds000115`** dataset.

**Dataset Verification**:
- **Source**: OpenNeuro `ds000115`.
- **Status**: The provided "Verified datasets" block for this project **does not contain a verified URL** for the `ds000115` NIfTI/BIDS data.
- **Action**: Per the plan rules, we **cannot fabricate a URL**. The implementation script (`download_data.py`) will use the official OpenNeuro API (`openneuro-py` or `curl` to `https://openneuro.org/datasets/ds000115/versions`) to fetch the data.
- **Variable Fit Check**:
  - **Required Variables**: fMRI BOLD data (3 conditions: normal, delayed, pitch-shifted), behavioral event logs (reaction time, accuracy), motion parameters.
  - **Dataset Availability**: `ds000115` is a motor sequence learning dataset. **CRITICAL WARNING**: Public documentation suggests this dataset typically involves visual feedback or standard motor tasks, and **may NOT contain the specific 'delayed' and 'pitch-shifted' auditory conditions** required by the research question.
  - **Risk**: If the official download fails or the dataset structure lacks the required conditions, the pipeline must **HALT** gracefully (Phase 0.5) and log "Critical Data Mismatch". The study cannot proceed if the independent variable is missing.

**Alternative Data Sources**:
- No alternative verified dataset URLs are available in the provided block that contain fMRI motor learning data with auditory perturbations.
- If `ds000115` lacks the required conditions, the project cannot proceed with the specified methodology.

## Methodological Approach

### 1. Preprocessing (FR-002)
- **Tool**: `fmriprep` (Docker image `nipreps/fmriprep:23.1.3`).
- **Parameters**:
  - Slice-time correction: Enabled.
  - Motion correction: Enabled.
  - Spatial Normalization: MNI152NLin2009cAsym (standard).
  - Smoothing: 6mm FWHM.
  - Output: Preprocessed BOLD images and confound regressors.
- **Compute Strategy**: To fit the 6-hour CPU limit, the pipeline will process **N≈10 subjects** sequentially.

### 2. First-Level GLM (FR-003)
- **Library**: `nilearn.glm.first_level`.
- **Design Matrix**:
  - Regressors: `normal`, `delayed`, `pitch_shifted` (convolved with HRF).
  - Confounds: Motion parameters (6 or 24), WM/CSF signals, high-pass filter.
- **Contrasts**:
  - `perturbed > normal` (combining delayed and pitch-shifted vs normal).
  - Output: Subject-level contrast maps (NIfTI) and t-statistics.

### 3. Group-Level Analysis (FR-004)
- **Method**: One-sample t-test on contrast maps (testing if mean difference > 0).
- **Correction**: **Voxel-wise FDR** (Benjamini-Hochberg, p < 0.05). 
  - *Rationale*: Cluster-wise FDR is unstable for N=10. Voxel-wise FDR is the standard, robust alternative for small samples.
- **Validation**: Null dataset generation (shuffling labels) to estimate false-positive rate (SC-002). 
  - *Limitation*: With N=10, permutation space is 1024. The empirical FPR will be reported with a caveat about low precision.

### 4. Brain-Behavior Correlation (FR-005)
- **ROIs**: Auditory Cortex, SMA, Cerebellum (defined **a priori** using Harvard-Oxford atlas, independent of the contrast maps to avoid double-dipping).
- **Metrics**: Mean contrast value in ROI vs. Mean Reaction Time/Accuracy.
- **Stat**: Pearson correlation (r, p-value).

### 5. Power Analysis (FR-008)
- **Method**: 
  1. **A priori estimation**: Based on literature estimates of effect sizes in motor learning.
  2. **Observed Power Limitation Report**: Calculate observed power based on the pilot N=10 and observed effect sizes.
  - *Rationale*: Post-hoc power analysis is statistically criticized. This approach provides a transparent limitation report rather than a misleading "power" metric.

## Study Framing & Limitations

- **Pilot Study**: This is explicitly a **feasibility/pilot study** (N≈10) to validate the pipeline and estimate effect sizes. It is **not** powered to detect medium effects or provide definitive generalizable conclusions.
- **Data Mismatch Risk**: If `ds000115` lacks the required auditory conditions, the study halts. This is a fundamental data mismatch, not a compute issue.
- **Statistical Limitations**: 
  - N=10 is underpowered for whole-brain inference.
  - Permutation test resolution is low (1024 permutations).
  - Results should be interpreted as preliminary.

## Compute Feasibility Assessment

- **Memory**: `fmriprep` on a single subject can peak at 4-6GB RAM. Processing N=10 sequentially ensures we stay under the 7GB limit.
- **Time**: `fmriprep` takes ~30-60 mins per subject on CPU. 10 subjects = 5-10 hours. **Mitigation**: The plan targets N≈8-10 to stay within the 6-hour limit, potentially using a highly optimized subset or parallelizing if the runner allows (but sequential is safer for RAM).
- **Disk**: 14GB disk is tight. The pipeline will delete raw data after preprocessing if necessary.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use `fmriprep:23.1.3` | Spec requirement (Constitution Principle VI). |
| Sequential processing | To prevent OOM on 7GB RAM runner. |
| Subset of subjects (N≈10) | To meet the 6-hour CI limit; full dataset processing is infeasible. |
| No GPU usage | Runner has no GPU; methods are CPU-tractable. |
| Voxel-wise FDR | More robust for N=10 than cluster-wise FDR. |
| A priori Power + Limitation Report | Avoids statistical fallacy of post-hoc power. |
| Halt on Data Mismatch | Fundamental requirement if data lacks independent variable. |