# Decision Record 002: Native Ground Truth & Paired Statistical Tests

## Status
Accepted

## Context
The original specification contained two scientifically unsound requirements:
1. **FR-004**: Required the use of "upsampled ground truth" (interpolating low-res images to match high-res dimensions) as the baseline for fidelity measurement. This approach introduces artificial smoothing and fails to represent the true high-frequency information present in native high-resolution images, leading to biased metric calculations (PSNR/SSIM).
2. **SC-005**: Specified a "one-sample t-test" for comparing reconstruction errors. A one-sample test compares a sample mean against a known constant, which is inappropriate for comparing two related measurements (low-res vs. high-res reconstructions of the *same* image).

## Decision
1. **Native Ground Truth**: All fidelity metrics (PSNR, SSIM) will be calculated by comparing the model's reconstruction against the **native 1024x1024 ground truth** image, not an upsampled version of the low-resolution input. This ensures the metrics reflect the true loss of information due to the quantization and resolution shift process.

2. **Paired Statistical Tests**: The statistical analysis comparing texture complexity and reconstruction error will utilize **paired t-tests** (if normality assumptions hold) or **Wilcoxon signed-rank tests** (if assumptions fail). This correctly models the dependency between the two measurements taken on the same sample.

## Consequences
- **Positive**:
 - Metrics are scientifically valid and reflect true image fidelity.
 - Statistical tests correctly handle the paired nature of the data, increasing the power and validity of the hypothesis testing.
 - Aligns the implementation with rigorous scientific standards.

- **Negative**:
 - Requires access to the original high-resolution images in the dataset, which is available for ImageNet-1K and COCO but necessitates the exclusion of any dataset where only low-res versions are available.
 - The analysis pipeline must be updated to handle paired data structures instead of independent samples.

## References
- Plan.md: "FR-004 (upsampled baseline) and SC-005 (one-sample t-test) are amended per Decision Record 002."
- T021: Metric aggregation script calculates against native ground truth.
- T022: Correlation analysis script implements Shapiro-Wilk and paired tests.
