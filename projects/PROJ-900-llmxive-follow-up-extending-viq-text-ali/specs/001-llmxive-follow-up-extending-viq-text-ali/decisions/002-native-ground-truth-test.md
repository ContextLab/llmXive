# Decision Record 002: Native Ground Truth & Paired Statistical Tests

**Status**: Accepted
**Date**: 2024-05-21
**Deciders**: Research Team, Engineering Lead
**Context**:
The original project specification (FR-004 and SC-005) defined the evaluation methodology for resolution invariance as follows:
- **FR-004 (Upsampled Ground Truth)**: Evaluate high-resolution (1024x1024) reconstructions by upsampling low-resolution (64x64) ground truth images to 1024x1024 using bicubic interpolation, then comparing against the model's high-res output.
- **SC-005 (One-Sample T-Test)**: Use a one-sample t-test to determine if the mean reconstruction error (e.g., PSNR) differs significantly from a fixed theoretical baseline value (e.g., 0 or a specific constant).

**Problem Statement**:
1. **Scientific Validity of Upsampled Ground Truth (FR-004)**:
 - Upsampling low-resolution ground truth (64x64) to 1024x1024 via bicubic interpolation creates a "pseudo-ground truth" that lacks high-frequency details present in the actual scene.
 - Comparing a model's output (which attempts to recover high-frequency details) against this interpolated baseline penalizes the model for "hallucinating" plausible details that are absent in the upsampled reference.
 - This introduces a systematic bias that conflates resolution invariance with super-resolution capability, invalidating the metric for the specific hypothesis of "invariance."
 - The correct baseline for a 1024x1024 input is the **native 1024x1024 ground truth** image, which contains the actual high-frequency information.

2. **Statistical Appropriateness of One-Sample T-Test (SC-005)**:
 - The one-sample t-test compares a sample mean against a known or hypothesized population mean (a fixed constant).
 - In this experiment, we are comparing two *paired* conditions: the reconstruction quality at native resolution vs. the reconstruction quality at downsampled/scaled resolution for the *same* image.
 - The samples are dependent (paired), not independent. Using a one-sample test ignores the correlation between the pairs, reducing statistical power and potentially leading to incorrect conclusions.
 - A **paired t-test** (for normally distributed differences) or **Wilcoxon signed-rank test** (for non-normal differences) is the statistically correct approach for within-subject (within-image) comparisons.

**Decision**:
We reject the original specifications FR-004 and SC-005 in favor of the following:

1. **Native Ground Truth Evaluation**:
 - All fidelity metrics (PSNR, SSIM) for high-resolution (1024x1024) images will be calculated against the **native 1024x1024 ground truth** images provided in the dataset (ImageNet-1K validation, COCO).
 - No upsampling of low-resolution images will be performed for the primary fidelity metric calculation.
 - If low-resolution inputs are used, the ground truth will be the corresponding low-resolution crop/downsample of the native image, not an upsampled version of the low-res input.

2. **Paired Statistical Testing**:
 - We will replace the one-sample t-test with a **paired t-test** or **Wilcoxon signed-rank test**.
 - The test will compare the distribution of error metrics (e.g., PSNR, SSIM, or reconstruction loss) between the "native resolution" condition and the "scaled/low-res" condition for the same set of images.
 - The specific test (parametric vs. non-parametric) will be determined by the Shapiro-Wilk test on the distribution of differences (paired t-test if p > 0.05, Wilcoxon if p <= 0.05).

**Consequences**:
- **Positive**:
 - The evaluation metric (PSNR/SSIM) now accurately reflects the model's ability to preserve information at high resolution without the confounding variable of interpolation artifacts.
 - The statistical analysis correctly accounts for the paired nature of the data, increasing the validity and power of the hypothesis test.
 - The results will be more comparable to standard computer vision literature which uses native ground truth.

- **Negative/Changes**:
 - The project requires access to the full-resolution (1024x1024) images in the dataset, which may increase memory/disk requirements during evaluation compared to using pre-downsampled versions.
 - The `code/analysis.py` and `code/eval_high_res.py` modules must be updated to implement the paired test logic and remove any upsampling logic used for ground truth generation.
 - The `spec.md` document must be updated to reflect these deviations from the original requirements.

**Implementation Tasks**:
- Update `code/eval_high_res.py` to load native 1024x1024 images and compute metrics against them.
- Update `code/analysis.py` to implement the Shapiro-Wilk check and select between paired t-test and Wilcoxon.
- Update `specs/001-viq-resolution-invariance/spec.md` to document these changes.
- Ensure `data/results/fidelity_metrics.json` includes a note confirming the use of native ground truth.

**References**:
- Original Spec: FR-004, SC-005
- Decision Record 001: ChestX-ray14 Exclusion
- Related Task: T036b (Decision Record Creation), T036c (Spec Update), T021 (Metric Aggregation), T022 (Correlation Analysis)