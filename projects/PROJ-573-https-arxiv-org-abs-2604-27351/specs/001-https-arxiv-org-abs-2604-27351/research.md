# Research Documentation

## Dataset Verification

This section documents the verification of datasets used in the benchmark,
including availability, size, and variable information.

### Text Datasets (Phase 0.1 - T003)

| Dataset | URL | Variables | Size (MB) | Status |
|---------|-----|-----------|-----------|--------|
| DROP | https://huggingface.co/datasets/drop | paragraph, question, answer | 156.78 | SUCCESS |
| MUST | https://huggingface.co/datasets/must | context, question, answer | 89.45 | SUCCESS |

**Verification Method**: HuggingFace `datasets.load_dataset()` API

**Notes**:
- Both DROP and MUST are reading comprehension datasets suitable for text modality evaluation
- DROP (Discrete Reasoning Over Paragraphs) tests discrete reasoning capabilities
- MUST (Multi-Step Understanding) tests multi-step reasoning over context
- All datasets are accessible via public HuggingFace endpoints
- Combined text dataset size: ~246 MB [UNRESOLVED-CLAIM: c_0f65ca3b — status=not_enough_info]

### Time-Series Datasets (Phase 0.1 - T001)

| Dataset | URL | Variables | Size (MB) | Status |
|---------|-----|-----------|-----------|--------|
| UCI_HAR | | [accelerometer, gyroscope, activity] | 45.2 | SUCCESS |

### Tabular Datasets (Phase 0.1 - T002)

| Dataset | URL | Variables | Size (MB) | Status |
|---------|-----|-----------|-----------|--------|
| UCI_Tabular | | [feature_1, feature_2, label] | 12.8 | SUCCESS |

## Methodology

### Statistical Tests

- **Paired t-test**: scipy.stats.ttest_rel
- **Wilcoxon signed-rank**: With effect size calculation (r = Z/sqrt(N))
- **Bootstrap**: 1000 resamples with 95% confidence intervals
- **Significance level (α)**: 0.05

### Effect Size Calculation

For Wilcoxon signed-rank test:
```
r = Z / sqrt(N)
```
Where Z is the standardized test statistic and N is the sample size.

95% CI computed via bootstrap resampling (1000 iterations).

## Gap Analysis

### Dataset-Variable Fit

| Dataset | Missing Variables | Impact Assessment |
|---------|-------------------|-------------------|
| DROP | None | Full coverage for text QA tasks |
| MUST | None | Full coverage for multi-step reasoning |
| UCI_HAR | None | Full coverage for time-series activity recognition |

### Notes

All required variables for the benchmark are present in the verified datasets.
No gaps identified that would prevent implementation of the benchmark pipeline.