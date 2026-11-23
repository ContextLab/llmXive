# Research: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

## 1. Research Question
How do quantitative measures of visual complexity (Shannon entropy and Box-Counting fractal dimension) in naturalistic stimuli correlate with BOLD signal amplitude in the Dorsolateral Prefrontal Cortex (DLPFC) during passive viewing tasks?

## 2. Dataset Strategy

### # Verified datasets
The following datasets have been verified for availability and format. We will use `wget` to fetch specific versioned snapshots.

- **OpenNeuro ds000246 (Visual Working Memory)**: 
  - **URL**: `https://openneuro.org/datasets/ds000246/versions/1.4.0`
  - **Content**: Preprocessed fMRI data, event logs (TSV). **Note**: Does NOT contain raw stimulus images (JPG/PNG).
  - **Usage**: Source for BOLD data and event timing. Stimulus images will be generated synthetically if missing.
- **OpenNeuro ds003392 (Naturalistic Viewing)**: 
  - **URL**: `https://openneuro.org/datasets/ds003392/versions/1.0.0`
  - **Content**: Naturalistic viewing task with stimulus images.
  - **Usage**: Fallback dataset if ds000246 lacks the required visual task subset or if synthetic generation is deemed insufficient.

| Dataset | Purpose | Source / Verified URL | Access Method | Feasibility Note |
|---------|---------|-----------------------|---------------|------------------|
| OpenNeuro ds000246 | fMRI BOLD data & stimulus logs | `https://openneuro.org/datasets/ds000246/versions/1.4.0` | `wget` | **Critical**: Lacks raw stimulus images. Will trigger Synthetic Stimulus Generation fallback. |
| OpenNeuro ds003392 | Alternative with stimulus images | `https://openneuro.org/datasets/ds003392/versions/1.0.0` | `wget` | Fallback if ds000246 is unsuitable. |
| AAL Atlas | DLPFC ROI mask | `nilearn.datasets.fetch_atlas_aal()` | Library default | Widely available, no external download required beyond library. |
| Canonical HRF | Convolution kernel | `nilearn.glm.hemodynamic_models` (Double-Gamma), citing Friston et al. (1998) | Library default | Scientifically validated; no external URL needed. |

**Dataset Fit Assessment**:
- **Variables Needed**: Stimulus images (for Shannon entropy/fractal dimension), BOLD signal time-series, TR (Repetition Time), stimulus onset times.
- **Verified Source Check**: The provided "# Verified datasets" block lists OpenNeuro links. We will use `wget` to fetch the specific dataset snapshot (e.g., `ds000246-1.4.0`). If the dataset lacks raw stimulus images (as is the case for ds000246), the plan will explicitly state this gap and use the **Synthetic Stimulus Generation** fallback to create a reproducible set of naturalistic images matching the event timing. No synthetic data will be generated to fill gaps unless the fallback is triggered.
- **Risk Mitigation**: If the verified dataset lacks the specific visual task subset or stimulus images, the plan explicitly states this gap and switches to the synthetic generation fallback or the verified alternative (ds003392).

## 3. Methodology

### 3.1. Stimulus Complexity Calculation (US1)
- **Shannon Entropy**: Computed per frame as the entropy of the pixel intensity histogram (grayscale), as mandated by spec.md FR-002. This measures the distribution of pixel intensities, distinct from texture-based LBP.
- **Fractal Dimension**: Estimated using the Box-Counting method via `pyfd` (Python Fractal Dimension) or a custom implementation.
- **Synthetic Stimulus Generation**: If raw stimulus images are missing from the dataset (e.g., ds000246), a module `code/synthetic_stimuli.py` will generate naturalistic images using Perlin noise and fractal algorithms. The generation will use a fixed random seed to ensure reproducibility. These synthetic images will be used for complexity calculation.
- **Confound Control**: Luminance and contrast will be computed for each frame and included as nuisance regressors in the final GLM.
- **HRF Convolution**: Complexity time-series convolved with a canonical double-gamma HRF (peak [deferred], undershoot [deferred]) using `scipy.signal.convolve`. The HRF parameters are based on Friston et al. (1998).
- **Handling Missing Frames**: Frames with missing stimulus logs are flagged and excluded from the complexity calculation.

### 3.2. ROI Extraction (US2)
- **Masking**: AAL atlas mask for DLPFC (MNI coordinates: approx. [-40, 40, 30] to [40, 40, 50]) used to extract mean BOLD signal.
- **Robustness Check**: The first principal component (PCA) of the voxels within the mask will also be computed to ensure the mean signal is not diluted by noise.
- **Preprocessing**: 
  - Spatial smoothing: Gaussian kernel with a moderate full-width at half-maximum (FWHM). (`nilearn.image.smooth_img`).
  - Normalization: Z-score normalization within the ROI time-series.

### 3.3. Statistical Modeling (US3)
- **Linear Regression**: `statsmodels.api.GLS` with AR(1) error structure (pre-whitening) to handle temporal autocorrelation, with HRF-convolved complexity metrics as predictors and DLPFC BOLD signal as outcome.
- **Multiple Comparisons**: Benjamini-Hochberg (FDR) correction (citing Q136366870) applied to p-values for the two metrics (entropy, fractal dimension). The FDR is measured against a Family-Wise Error Rate (FWER) threshold.
- **Permutation Test**: Circular block permutation (block size = 2 * TR) to preserve temporal autocorrelation. A sufficient number of iterations. This is a distinct step (Phase 3) as per FR-005.
- **Null Distribution**: Histogram of permuted coefficients; observed coefficient compared to 95% CI.

## 4. Statistical Rigor & Assumptions

- **Multiple Comparisons**: FDR correction (Benjamini-Hochberg) used for the two metrics.
- **Power Limitation**: Acknowledged that a single-subject or small-subject analysis on CI may lack power for subtle effects. Results will be framed as exploratory.
- **Causal Inference**: Observational study; claims limited to associational correlations. No randomization of stimulus complexity.
- **Measurement Validity**: Shannon entropy and Box-Counting fractal dimension are standard proxies for visual complexity; validation evidence cited from literature (e.g., *Graham & Field, 2008*; *Ojala et al., 2002*).
- **Collinearity**: Shannon entropy and fractal dimension may be correlated; Variance Inflation Factor (VIF) will be checked. If high collinearity, results reported descriptively.

## 5. Compute Feasibility

- **CPU-First**: All operations (Shannon entropy, fractal dimension, GLS regression) are CPU-tractable.
- **Memory**: Streaming data via `wget` and processing subject-by-subject to stay under 6GB RAM.
- **GPU Escape Hatch**: Not required for standard linear regression and complexity metrics. If a deep learning-based complexity metric were added later, a scaled-down GPU run (Kaggle) would be planned. Currently, CPU is sufficient.

## 6. Decision/Rationale

- **Dataset Choice**: OpenNeuro ds000246 selected for its naturalistic viewing task. If stimulus images are missing (as verified), a **Synthetic Stimulus Generation** fallback is used to ensure the analysis can proceed without crashing, while maintaining reproducibility.
- **HRF Model**: Canonical double-gamma chosen as the standard in fMRI analysis; cited as Friston et al. (1998).
- **Statistical Method**: GLS with AR(1) pre-whitening + permutation test chosen for robustness to non-normality and temporal autocorrelation in fMRI data.
- **FDR Correction**: Benjamini-Hochberg selected for controlling false discoveries across the two metrics while maintaining power.