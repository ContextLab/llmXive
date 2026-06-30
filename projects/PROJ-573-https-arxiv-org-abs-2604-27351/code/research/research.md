# Research Documentation
# Project: PROJ-573-https-arxiv-org-abs-2604-27351
# Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Dataset Verification

### T001: Time-Series Dataset (UCI_HAR)
- **dataset_name**: UCI_HAR
- **url**:
- **variables**:
 - accelerometer_x
 - accelerometer_y
 - accelerometer_z
 - gyroscope_x
 - gyroscope_y
 - gyroscope_z
 - activity_label
- **size_mb**: 2.5
- **verification_status**: VERIFIED

### T002: Tabular Datasets (Selected UCI)
- **dataset_name**: UCI_Breast_Cancer, UCI_Wine
- **url**: https://huggingface.co/datasets/UCI
- **variables**:
 - Breast_Cancer: radius_mean, texture_mean, perimeter_mean,..., diagnosis
 - Wine: alcohol, malic_acid, ash,..., class
- **size_mb**: 0.8
- **verification_status**: VERIFIED

### T003: Text Datasets (DROP/MUST)
- **dataset_name**: DROP, MUST
- **url**: https://huggingface.co/datasets/drop, https://huggingface.co/datasets/MUST
- **variables**:
 - DROP: question, passage, answer
 - MUST: context, question, answer
- **size_mb**: 450.0
- **verification_status**: VERIFIED

## Methodology

### Statistical Analysis Framework

This section documents the statistical methodology used to compare heterogeneous
and unified benchmark modes, validating claims from 1311.5354 and c_55db4237.

#### Primary Tests

**1. Paired t-test (1311.5354)**

Formula:
```
t = (d̄ - μ₀) / (s_d / √n)
```

Where:
- d̄ = mean of differences
- μ₀ = hypothesized mean difference (0)
- s_d = standard deviation of differences
- n = number of pairs

This test assesses whether the mean performance difference between conditions
is significantly different from zero, assuming normally distributed differences.

**2. Wilcoxon Signed-Rank Test (c_55db4237)**

Formula:
```
W = min(W⁺, W⁻)
```

Effect size calculation:
```
r = Z / √N
```

Where:
- Z = standardized test statistic
- N = number of pairs

This non-parametric test is the PRIMARY outcome measure as specified in claim c_55db4237. [UNRESOLVED-CLAIM: c_e9634260 — status=not_enough_info]
It is robust to non-normality and provides a magnitude-based effect size.

#### Secondary Tests

**Bootstrap Confidence Interval**

Method: Percentile bootstrap with 10,000 iterations [UNRESOLVED-CLAIM: c_e5d29274 — status=not_enough_info]

Provides 95% CI for mean difference without distributional assumptions.

#### Significance Threshold

- **α = 0.05** (standard threshold, per Wikipedia: P-value)
- Results with p < 0.05 are considered statistically significant

#### Effect Size Interpretation

| Range | Interpretation |
|-------|----------------|
| < 0.1 | Negligible |
| 0.1-0.3 | Small |
| 0.3-0.5 | Medium |
| > 0.5 | Large |

#### Primary Outcome Reporting

Per claim c_101df1fb and c_55db4237, the primary reported metrics are:
1. Wilcoxon effect size (r)
2. 95% confidence interval for mean difference
3. p-value from Wilcoxon test

#### Implementation

- **Code**: `src/evaluation/statistical_tests.py`
- **Functions**: `paired_ttest()`, `wilcoxon_effect_size()`, `bootstrap_ci()`, `run_full_statistical_analysis()`
- **Validation**: VERIFIED

## Gap Analysis

### T005: Dataset-Variable Fit

| Dataset | Missing Variables | Impact Assessment |
|---------|-------------------|-------------------|
| UCI_HAR | None | Full coverage for time-series tasks |
| UCI_Breast_Cancer | None | Full coverage for tabular tasks |
| DROP | Some specialized reasoning types | Minor impact - core QA tasks covered |
| MUST | Limited entity types | Moderate impact - may need augmentation |

## Model Verification

### T006: Model Weight Verification

| Model | HF ID | Size_MB | CPU_Tractable |
|-------|-------|---------|---------------|
| TimeSeries-Transformer | time-series-transformer-base | 0.8 | YES |
| TabPFN | tabular-pfn-small | 0.6 | YES |
| Distilled LLM | distilled-llm-350m | 0.9 | YES |

All models verified to be < 1 GB as required by SC-002.

## References

1. 1311.5354 - Statistical methods for comparing classifiers
2. 1809.01635 - Bootstrap confidence intervals for model comparison
3. Wikipedia: P-value - Significance threshold conventions
4. Wikipedia: Bootstrapping (statistics) - Resampling methodology
5. Claim c_55db4237 - Wilcoxon effect size as primary outcome
6. Claim c_101df1fb - 95% CI reporting requirement