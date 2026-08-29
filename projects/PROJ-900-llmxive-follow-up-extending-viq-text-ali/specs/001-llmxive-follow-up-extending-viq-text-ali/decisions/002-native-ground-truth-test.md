# Decision Record 002: Native Ground Truth and Paired Statistical Testing

## Status
Accepted

## Context
The original specification contained two methodological choices that were identified as scientifically unsound during the planning phase:

1. **FR-004 (Upsampled Ground Truth)**: The spec required comparing high-resolution reconstructions against an *upsampled* low-resolution ground truth. This introduces artificial smoothing and biases the fidelity metrics (PSNR/SSIM) in favor of the upsampling method, rather than measuring true reconstruction fidelity against the original high-resolution signal.
2. **SC-005 (One-Sample t-test)**: The spec proposed using a one-sample t-test to compare reconstruction errors. However, since we are comparing paired observations (the same image at low-res vs. high-res, or reconstruction vs. ground truth for the *same* image), a one-sample test is inappropriate. The observations are dependent, not independent.

## Decision
We hereby **reject** the original FR-004 and SC-005 and adopt the following corrections:

1. **Native Ground Truth**: All fidelity metrics (PSNR, SSIM) for high-resolution (1024x1024) evaluations will be calculated against the **native 1024x1024 ground truth** images available in the ImageNet-1K and COCO validation sets. No upsampling will be performed on the ground truth.
2. **Paired Statistical Testing**: All statistical comparisons of reconstruction errors between resolutions or against baselines will use **paired t-tests** (if normality assumptions hold, verified via Shapiro-Wilk) or **Wilcoxon signed-rank tests** (if normality is violated).

## Consequences
- **Positive**: The evaluation methodology is now statistically rigorous. Metrics reflect true reconstruction quality against the actual high-resolution signal.
- **Negative**: Fidelity scores may appear lower than the upsampled baseline would have suggested, as the metric is now harder.
- **Implementation**: T021 and T022 were updated to implement these corrected calculation and testing methods. T036c updates the spec to reflect these changes.
