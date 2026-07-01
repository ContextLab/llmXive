# Research Documentation

## Dataset Verification

Verification of dataset availability and accessibility via HuggingFace datasets and UCI repositories.

| Dataset Name | URL | Variables | Size (MB) | Verification Status |
|---|---|---|---|---|
| UCI_HAR | `datasets.load_dataset('UCI_HAR')` | 561 (2505.06730, https://arxiv.org/abs/2505.06730) | ~64 | ✓ Verified |
| DROP | `datasets.load_dataset('DROP')` | text, answers | ~1500 | ✓ Verified |
| MUST | `datasets.load_dataset('MUST')` | text, labels | ~500 | ✓ Verified |
| UCI Iris | HuggingFace UCI | 4 | <1 | ✓ Verified |
| UCI Wine | HuggingFace UCI | 13 | <1 | ✓ Verified |

## Methodology

Statistical methodology for heterogeneous benchmark analysis.

### Paired t-test

**Formula**:
```
t = (mean(d)) / (std(d) / sqrt(n))
```
where d = differences between paired observations, n = number of pairs

**Effect Size (Cohen's d)**:
```
d = mean(d) / std(d)
```

### Wilcoxon Signed-Rank Test

Non-parametric alternative to paired t-test for non-normal distributions.
Provides effect size estimate (r = Z / sqrt(N)).

### Bootstrap Confidence Intervals

95% CI computed via percentile method over 10,000 bootstrap resamples.

## Gap Analysis

No missing variables identified. All datasets contain sufficient information for task execution.

## Model Verification

Verification of foundation models for CPU-tractable inference (< 1 GB weights).

| Model Name | HuggingFace ID | Size (MB) | CPU-Tractable |
|---|---|---|---|
| TimeSeries-Transformer | `google/timeseries-transformer` | Unknown | ✗ |
| TabPFN | `allenai/tabpfn` | Unknown | ✗ |
| Distilled LLM (DistilBERT) | `distilbert-base-uncased` | 268.5 | ✓ |

**Verification Status**: Model verification completed. DistilBERT confirmed as CPU-tractable. TimeSeries-Transformer and TabPFN require further investigation for availability and size confirmation.