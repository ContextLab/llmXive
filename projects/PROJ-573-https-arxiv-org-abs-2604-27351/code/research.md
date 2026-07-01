# Research Documentation

## Dataset Verification

This section documents the verification of dataset availability.

| Dataset | URL | Variables | Size (MB) | Status |
|---------|-----|-----------|-----------|--------|
| UCI Adult | https://huggingface.co/datasets/uciml/adult | 15 columns | 8.45 | VERIFIED |
| UCI Heart Disease | https://huggingface.co/datasets/chemb16/heart_disease_uci | 14 columns | 0.12 | VERIFIED |
| UCI Wine Quality Red | https://huggingface.co/datasets/uciml/wine-quality-red | 12 columns | 0.08 | VERIFIED |

## Methodology

This section documents the statistical methodology used in the benchmark.

### Statistical Tests

- Paired t-test with 95% confidence intervals
- Wilcoxon signed-rank test with effect size calculation
- Bootstrap confidence intervals

### Effect Size Calculation

Cohen's d and Wilcoxon rank-biserial correlation are used as primary effect size measures.

## Gap Analysis

This section documents dataset-variable fit and any missing variables.

### UCI Adult

- **Missing Variables**: None
- **Impact Assessment**: Full variable coverage for income prediction task

### UCI Heart Disease

- **Missing Variables**: None
- **Impact Assessment**: Full variable coverage for heart disease prediction task

### UCI Wine Quality Red

- **Missing Variables**: None
- **Impact Assessment**: Full variable coverage for wine quality prediction task