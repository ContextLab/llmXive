# Analysis Guide

## Statistical Methods

### Repeated-Measures ANOVA
The primary analysis uses a repeated-measures ANOVA to compare false memory rates across conditions:
- Condition 1: Baseline images
- Condition 2: Enhanced detail images
- Condition 3: Reduced detail images

**Hypothesis**: Visual detail level significantly affects false memory susceptibility.

### Power Analysis
Prior to data collection, a power analysis was conducted:
- Alpha level: 0.05
- Power target: 0.80
- Effect size (Cohen's f): 0.25 (medium)
- Required sample size: [See data/processed/power_analysis.json]

### Multiple Comparison Correction
Post-hoc comparisons use Bonferroni correction to control family-wise error rate.

## Data Processing Pipeline

1. **Raw Responses**: Collected from participant sessions
2. **False Memory Calculation**: Rate of false "yes" responses to lure items
3. **Condition Aggregation**: Group by image manipulation condition
4. **Statistical Testing**: ANOVA and post-hoc tests
5. **Visualization**: Mean rates with 95% confidence intervals

## Output Files

- `data/processed/anova_results.json`: ANOVA statistics (F-value, p-value, degrees of freedom)
- `data/processed/bonferroni_results.json`: Corrected p-values for pairwise comparisons
- `figures/false_memory_rates.png`: Visualization of results
- `data/processed/dataset_fit_check.json`: Distribution comparison metrics

## Interpretation Guidelines

### Effect Size Interpretation
- Small: f = 0.10
- Medium: f = 0.25
- Large: f = 0.40

### Confidence Intervals
95% confidence intervals indicate the range within which the true population mean likely falls. Non-overlapping intervals suggest significant differences.

### Limitations
- Simulated participants may not fully capture human variability
- Image manipulation quality affects stimulus validity
- Sample size limitations in pilot studies

## Reproducibility
All analysis code is version-controlled. Random seeds are set for reproducibility:
- NumPy: `np.random.seed(42)`
- Python random: `random.seed(42)`

## Citation Format
When reporting results:
"A repeated-measures ANOVA revealed a significant effect of visual detail on false memory rates, F(df1, df2) = X.XX, p =.XXX, η² =.XX."
