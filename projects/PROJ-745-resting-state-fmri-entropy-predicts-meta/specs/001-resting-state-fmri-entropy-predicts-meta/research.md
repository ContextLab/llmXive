# Research: Resting-State fMRI Entropy Predicts Metacognitive Accuracy

## Executive Summary

This research validates the feasibility of testing the **associative** hypothesis that whole-brain multiscale sample entropy (MSE) of resting-state fMRI is associated with metacognitive accuracy (meta-d′/d′). The study leverages the **Human Connectome Project (HCP) 1200 S1200 release**, focusing on the **Visual Grating** task (or equivalent visual perceptual decision-making task with confidence ratings) and associated resting-state scans. The analysis is constrained to CPU-only execution on GitHub Actions free-tier runners.

## Dataset Strategy

### Verified Datasets

The following datasets are verified and accessible. The plan restricts data ingestion to these sources to ensure reproducibility and accuracy.

| Dataset Name | Source URL | Format | Variables Available | Suitability |
|--------------|------------|--------|---------------------|-------------|
| HCP S1200 (Raw) | `https://db.humanconnectome.org/` (Requires Login/API) | NIfTI + CSV | Resting-state BOLD, Task CSV (Visual Grating), Demographics | **Primary Source**: Must contain specific task with confidence ratings. |
| HCP S1200 (Task) | `https://db.humanconnectome.org/` | CSV | Stimulus, Response, Confidence, Trial ID | **Critical**: Must verify presence of 'Visual Grating' task with confidence columns. |

**Critical Verification Step**: Before proceeding, the `download.py` script will inspect the schema of the HCP S1200 release to confirm the presence of:
1.  **Resting-state fMRI**: Time series data (NIfTI) or preprocessed minimally processed data.
2.  **Behavioral Task**: Specifically, the **Visual Grating** task (or equivalent) with columns for `stimulus`, `response`, and `confidence`.
3.  **Demographics**: `age`, `sex`.
4.  **Motion**: `mean_framewise_displacement`.

If the verified sources lack the specific behavioral task data (e.g., only contain resting-state or generic demographics), the plan will flag a **blocking mismatch** and halt, as the hypothesis cannot be tested without metacognitive metrics. The 'Visual Grating' task must be distinct from the resting-state acquisition to avoid tautology.

### Data Loading Strategy

- **Primary Loader**: `huggingface_hub` or HCP API (if authorized) for NIfTI/CSV.
- **Fallback**: Direct CSV parsing via `pandas.read_csv()` if Parquet schema is incompatible.
- **Caching**: All downloaded data is stored in `data/raw/` with checksums to ensure reproducibility (Constitution Principle III).

## Methodological Approach

### 1. Preprocessing Pipeline (FR-001, FR-002)

- **Input**: Raw NIfTI (if available) or preprocessed minimally processed data from HCP.
- **Steps**:
  1.  **Motion Correction**: If raw, apply rigid-body registration. (Assuming HCP minimally preprocessed data is used, which includes motion correction).
  2.  **Motion Scrubbing**: **Non-linear step**: Remove volumes with FD > 0.5mm to reduce motion-induced entropy bias.
  3.  **Nuisance Regression**: Regress out motion parameters (6 or 24), **FD derivatives**, **FD squared terms**, CSF, and white matter signals.
  4.  **Band-pass Filtering**: 0.009–0.08 Hz to isolate low-frequency fluctuations.
  5.  **Parcellation**: Apply Schaefer atlas to extract mean time series per parcel.
- **Output**: 400 time series per subject (1200 timepoints).

### 2. Metric Computation (FR-003, FR-004)

- **Multiscale Sample Entropy (MSE)**:
  - **Library**: `nolds` (CPU-compatible).
  - **Parameters**: Scales τ=1–5; tolerance r=0.15 (default); embedding dimension m=2.
  - **Aggregation**: **Arithmetic mean** of MSE across all 400 parcels to derive a **whole-brain entropy score** (Primary Metric).
  - **Exploratory**: PCA on parcel entropies may be performed to identify network-specific components, but these are **not** the primary predictor.
- **Metacognitive Efficiency (meta-d′/d′)**:
  - **Method**: Type 2 Signal Detection Theory (SDT).
  - **Inputs**: Confidence-rated trial data (stimulus, response, confidence).
  - **Validation**: Check for floor/ceiling effects in confidence ratings; exclude subjects with >10% missing confidence data.
  - **Bias Correction**: **Bootstrapping** (1000 iterations) to generate confidence intervals for the ratio, addressing non-linearity and heteroscedasticity.

### 3. Statistical Analysis (FR-005, FR-006)

- **Primary Model**: Linear regression: `meta_efficiency ~ whole_brain_entropy + age + sex + mean_framewise_displacement`.
- **Correction**: Bonferroni correction for multiple comparisons.
- **Bias Handling**: **Bootstrapping** (1000 iterations) used to generate robust confidence intervals and p-values for the regression coefficient.
- **Sensitivity Analysis**: Sweep tolerance parameter `r` across {0.1, 0.15, 0.2}. Report variation in beta and p-value.
- **Power Check**: **Formal Power Analysis**. For r ≈ 0.2, alpha = 0.05 (Bonferroni corrected), power = 0.8, the required N is approximately 194. The plan halts if n < 194.

## Decision Rationale

### Why CPU-Only?
The project is designed for GitHub Actions free-tier (no GPU). Deep learning models (e.g., CNNs for fMRI) are excluded. `nolds` and `scikit-learn` are computationally efficient on CPU and sufficient for MSE and linear regression.

### Why Arithmetic Mean (Primary)?
The Spec (FR-003) explicitly mandates aggregating into a single whole-brain entropy score by calculating the arithmetic mean. This is the primary metric. PCA is used only for exploratory network-specific analysis to avoid violating the primary metric definition.

### Why Sensitivity Analysis?
Sample entropy is sensitive to the tolerance parameter `r`. Sweeping `r` ensures the observed association is robust to this arbitrary choice, addressing methodological soundness (FR-006).

### Why Bootstrapping?
The meta-d'/d' ratio is non-linear and biased. Bootstrapping provides a robust method to handle heteroscedasticity and generate valid confidence intervals without relying on parametric assumptions that may not hold.

## Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing Behavioral Data** | Blocking: Cannot compute meta-d′. | Pre-check schema; halt with clear error if confidence ratings are absent. |
| **High Motion Subjects** | Bias in entropy estimates. | Include motion scrubbing (FD > 0.5mm) and non-linear motion terms (derivatives, squared) in preprocessing. |
| **Insufficient Sample Size** | Low power for regression. | **Formal Power Analysis** (N ≥ 194); halt if n < 194. |
| **Memory Overflow** | Crash on 7 GB RAM limit. | Stream data; process subjects in batches; use efficient data types (float32). |
| **Task Tautology** | Spurious association due to shared neural substrates. | Verify task independence; frame results as associative only. |

## References

- **HCP 1200**: Verified via HCP S1200 release (https://db.humanconnectome.org/).
- **MSE Method**: `nolds` library documentation.
- **Meta-d′**: Maniscalco, B., & Lau, H. (2012). A signal detection theoretic approach for estimating metacognitive sensitivity from confidence ratings. *Consciousness and Cognition*.
- **Schaefer Atlas**: Schaefer, A., et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex. *Cerebral Cortex*.