# Implementation Guide: Robustness of Statistical Tests to Non-Independence

## Overview

This document details the implementation of the llmXive project evaluating the robustness of common statistical tests (t-test, ANOVA, Chi-squared) to non-independence in public datasets.

## Architecture

### Core Components

1. **Configuration (`code/config.py`)**
 - Loads `code/config.yaml` and validates against `contracts/simulation_config.schema.yaml`
 - Manages global parameters: seed, replication count, dependency strengths

2. **Data Management (`code/data_loader.py`)**
 - Fetches datasets from verified UCI URLs defined in `data/manifests/datasets.yaml`
 - Validates dataset structure (continuous/categorical variables)
 - Generates checksums for data integrity

3. **Dependency Injection (`code/dependency_injector.py`)**
 - **AR(1) Injection**: Vectorized autoregressive dependency with tunable strength $r \in \{0, 0.1, 0.2, 0.3, 0.5\}$
 - **Block Bootstrap**: Hierarchical dependency with block size $= \sqrt{N}$
 - **Spatial Proxy**: K-Means clustering (k=3) for feature-space coordinates when native coordinates absent
 - **Spatial Kernel Smoothing**: Gaussian kernel smoothing on proxy coordinates

4. **Simulation Engine (`code/simulation_runner.py`)**
 - **Synthetic Data Generation**: Generates null hypothesis data (independence)
 - **Null Construction (Real Data)**: "Inject-then-Permute" paradigm - inject dependency, then permute labels
 - **Test Execution**: Applies t-test, ANOVA, Chi-squared tests
 - **Edge Case Handling**: Detects and logs failures in null construction

5. **Metrics (`code/metrics.py`)**
 - **Type I Error Calculation**: Observed false-positive rates with Clopper-Pearson 95% CI
 - **Power Analysis**: Observed power under true effect injection
 - **Trend Verification**: Spearman correlation and Mann-Kendall tests for monotonicity
 - **Logistic Regression**: Models error rate vs. dependency strength

6. **Visualization (`code/visualizer.py`)**
 - Error rate curves with confidence intervals
 - Power comparison plots
 - Cross-test and cross-structure comparisons

7. **Performance Monitoring (`code/perf_monitor.py`)**
 - Memory usage tracking (peak RSS)
 - Execution time measurement
 - Performance logging to `results/perf_log.json`

## Execution Paradigms

### Synthetic Data: "Generate-then-Inject"
1. Generate independent synthetic data under true null hypothesis
2. Inject dependency structure (AR(1)/Block/Spatial) with strength $r$
3. Apply statistical test
4. Record p-value

### Real Data: "Inject-then-Permute"
1. Load real dataset
2. Inject dependency structure with strength $r$
3. Permute target labels (random shuffle) to break any existing effect
4. Apply statistical test
5. Record p-value

## Data Sources

All datasets are fetched from verified UCI URLs:
- **Wine Dataset**: Continuous variables, suitable for t-test/ANOVA
- **Car Evaluation**: Categorical variables, suitable for Chi-squared
- **Zoo Dataset**: Categorical variables, suitable for Chi-squared

URLs are defined in `data/manifests/datasets.yaml` with verification comments.

## Dependency Strengths

The sweep configuration uses the discrete set mandated by FR-007:
$$r \in \{0.0, 0.1, 0.2, 0.3, 0.5\}$$

## Statistical Methods

### Null Hypothesis Construction
- **Synthetic**: Pure generation under independence ($r=0$ baseline)
- **Real**: Permutation of labels after dependency injection

### Error Rate Calculation
- Observed Type I error = (Number of rejections) / (Total replications)
- 95% Confidence Interval: Clopper-Pearson exact method

### Trend Verification
- **Spearman Rank Correlation**: Tests monotonic increase of error rate with $r$
- **Mann-Kendall Test**: Non-parametric trend test robust to outliers

### Power Analysis
- **True Effect Injection**: Mean shift $\delta = 1.0\sigma$ before dependency injection
- **Power Reduction**: Percentage decrease in power from $r=0$ to $r=0.3$

## Edge Cases

The system handles:
- Datasets with $N < 50$: Skipped with validation report
- Highly correlated variables: Flagged in edge case report
- Normality violations (Shapiro-Wilk $p < 0.01$): Flagged for parametric test validity
- Failed spatial proxy generation (silhouette $< 0.25$): Spatial injection skipped

## Performance Targets

- **Replication Count**: 10,000 per configuration (FR-008)
- **Precision**: $\pm 0.5\%$ CI width (SC-003)
- **Execution Time**: < 6 hours for largest configuration on 2-core, 7GB RAM
- **Memory Limit**: < 6GB peak RSS per dataset

## Output Artifacts

### Results Directory (`results/`)
- `simulation_raw.csv`: Raw p-values from all replications
- `aggregated_unified.csv`: Aggregated error rates with CIs
- `type1_error_table.md`: Human-readable Markdown table
- `logistic_models.pkl`: Trained logistic regression models
- `precision_report.json`: CI width verification status
- `trend_status.json`: Monotonicity verification results
- `edge_case_report.json`: Logged edge case failures
- `perf_log.json`: Performance metrics and optimization details
- `config_audit.json`: Configuration traceability report

### Data Directory (`data/`)
- `raw/*.csv`: Fetched datasets
- `manifests/datasets.yaml`: Dataset definitions with verified URLs
- `manifests/checksums.json`: Data integrity checksums
- `manifests/spatial_proxy_report.json`: Proxy generation logs
- `manifests/spatial_proxy_validation.json`: Proxy validation results
- `dependency_manifest.yaml`: Per-dataset parameter choices

## Execution Flow

1. **Setup**: `python code/main.py` (entry point)
2. **Configuration**: Load and validate `code/config.yaml`
3. **Data Fetch**: Run `code/run_data_loader.py` to fetch datasets
4. **Spatial Proxy**: Generate and validate proxies for datasets without coordinates
5. **Simulation Sweep**: Run Monte Carlo simulations for all configurations
6. **Aggregation**: Merge results into unified CSV
7. **Metrics**: Calculate error rates, CIs, trends, and power
8. **Visualization**: Generate plots
9. **Reporting**: Output tables and audit reports

## Validation

- **Null Hypothesis Validity**: Under $r=0$, p-values should be uniform (verified via unit test)
- **Trend Monotonicity**: Error rates must increase with $r$ (Spearman $p < 0.05$)
- **CI Precision**: Clopper-Pearson width $\le 0.01$ (target $\pm 0.5\%$)
- **Performance**: 10,000 replications complete within 6-hour window

## Reproducibility

- All random seeds pinned in `code/config.yaml`
- Configuration audit report logs all active parameters
- Checksums verify data integrity
- Version control tracks all code changes

## Troubleshooting

### Data Fetch Failures
- Pipeline halts with `DataFetchError` if verified URL fails
- No synthetic fallback (per T056b)
- Check network connectivity and URL validity in `data/manifests/datasets.yaml`

### Memory Constraints
- Pre-flight check estimates memory footprint
- Datasets exceeding 6GB threshold are skipped
- Logging to `results/perf_log.json`

### Edge Case Failures
- Specific configurations logged to `results/edge_case_report.json`
- Pipeline continues with remaining valid configurations
- Review logs to identify problematic datasets

## Future Work

- Extend to additional statistical tests (Fisher's exact, Wilcoxon)
- Explore alternative dependency injection methods
- Investigate robust statistical tests for non-independent data
- Expand dataset catalog with more diverse sources
