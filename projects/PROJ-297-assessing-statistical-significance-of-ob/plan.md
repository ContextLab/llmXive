# Project Plan: Assessing Statistical Significance of Observed Correlations in Public Databases

## Overview
This project implements a pipeline to assess the statistical significance of observed correlations in multivariate datasets from public databases (specifically UCI Machine Learning Repository). The pipeline generates empirical null distributions via permutation testing and applies rigorous multiple testing corrections.

## Objectives
1. Ingest multivariate datasets with sufficient continuous variables
2. Compute observed network statistics from correlation matrices
3. Generate empirical null distributions via permutation
4. Apply Benjamini-Yekutieli correction for multiple testing
5. Perform threshold sensitivity analysis
6. Generate comprehensive visualizations and reports

## Data Sources
- Primary: UCI Machine Learning Repository multivariate datasets
- Requirement: Datasets must have >= 20 continuous variables
- Minimum valid datasets: 3 (dynamic discovery if primary list fails)

## Methodology

### Phase 0: Data Acquisition & Validation
- Dynamic discovery of UCI datasets
- Data hygiene: missing value handling, constant variable detection
- Validation: >= 20 continuous variables per dataset

### Phase 1: Core Statistical Engine
- **Permutation Testing**: N=1,000 permutations per dataset (optimized from Spec's N=2,000)
 - Exception: For clustering coefficient on datasets with >50 variables, reduce N to 500
- **Statistics Computation**:
 - Mean Absolute Correlation
 - Edge Density
 - Max Absolute Correlation
 - Average Clustering Coefficient
- **Correlation Methods**:
 - Pearson: Primary (used for graph construction and significance testing)
 - Spearman: Exploratory only (stored separately, excluded from significance testing)

### Phase 2: Multiple Testing Correction
- **Benjamini-Yekutieli (BY) Procedure**: Applied across all tests (datasets × 4 statistics)
- **Gate**: Constitution Amendment (BH->BY) must be ratified before execution
- **Empirical P-values**: Calculated as (r+1)/(N+1) to avoid 0/1

### Phase 3: Threshold Sensitivity Analysis
- **Threshold Sweep**: Explicitly test thresholds **{0.1, 0.2, 0.3, 0.4, 0.5}**
 - Re-run permutation and significance for each threshold
 - Generate summary table showing significant counts per threshold
 - Include 0.1 baseline data point
- **Visualization**:
 - Primary threshold (|r| > 0.3) heatmaps and histograms
 - Sensitivity sweep plots
 - Observed vs. null distribution comparisons

### Phase 4: Reporting & Visualization
- CSV summary tables with dataset_id, statistic, observed, p-value, q-value, is_significant
- High-resolution PNG plots (heatmaps, histograms)
- Sensitivity reports with explicit associational language
- Integration of all outputs into `output/plots/` and `output/reports/`

## Technical Architecture

### File Structure
```
project_root/
├── code/
│ ├── config.py # Configuration, paths, seeds
│ ├── loaders.py # Data fetching, hygiene, validation
│ ├── stats_engine.py # Core statistical computations
│ ├── correction.py # BY correction implementation
│ ├── viz.py # Visualization functions
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Downloaded UCI datasets
│ └── processed/ # Cleaned, validated datasets
├── output/
│ ├── results/ # CSV summaries, statistics
│ ├── plots/ # Generated visualizations
│ │ └── primary/ # Primary threshold plots
│ ├── reports/ # Final reports
│ └── exploratory/ # Spearman matrices (exploratory)
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Dependencies
├── plan.md # This file
├── spec.md # Feature specifications
└── README.md # Documentation
```

### Key Dependencies
- pandas: Data manipulation
- numpy: Numerical computations
- scipy: Statistical functions
- networkx: Graph construction and analysis
- matplotlib/seaborn: Visualization
- requests: HTTP requests for UCI downloads

## Validation & Testing

### Synthetic Validation (T016b)
- Run synthetic validation (identity covariance, N=500, V=20) 100 times
- Verify observed statistics fall within central region of null distribution (p > 0.05) in >= 95 runs
- Report confidence interval of pass rate

### Integration Tests
- Permutation preservation of marginals
- BY correction accuracy
- Sensitivity sweep completeness (all thresholds present)
- Data loader failure modes (no synthetic fallback)

## Constraints & Requirements

### Data Integrity (Constitution VII)
- **NO synthetic data** for final results
- **NO silent fallbacks**: Failed real fetches must raise explicit errors
- **Real sources only**: UCI repository via verified URLs
- **Checksum validation**: Store SHA256 hashes for reproducibility

### Computational Constraints
- CPU-only execution (no GPU requirements)
- Runtime < 6h for full pipeline
- Memory: <= 7 GB RAM, <= 14 GB disk
- Streaming for large datasets if needed

### Statistical Rigor
- Benjamini-Yekutieli correction (not Bonferroni or BH)
- Empirical p-values with (r+1)/(N+1) formula
- Explicit associational language in all reports
- Constitution Amendment ratification gate for BY procedure

## Execution Order

1. **Setup** (T001-T003): Project structure, dependencies, linting
2. **Foundational** (T004-T009): Configuration, loaders, stats engine skeleton, correction, viz skeleton
3. **User Story 1** (T010-T016b): Permutation engine, synthetic validation, network statistics
4. **User Story 2** (T018-T022): BY correction, empirical p-values, significance reporting
5. **User Story 3** (T023-T028): Threshold sweep, visualizations, sensitivity reports
6. **Polish** (T029-T036): Documentation, code cleanup, performance optimization

## Risk Mitigation

- **Data Availability**: Dynamic discovery if primary list yields < 3 datasets
- **Runtime Limits**: Conditional N reduction for clustering coefficient on large datasets
- **Statistical Power**: 100-run synthetic validation with CI reporting
- **Multiple Testing**: BY procedure (robust under dependence)
- **Reproducibility**: Fixed random seeds, checksum validation, streaming support

## Success Criteria

- [x] Pipeline runs end-to-end on real UCI datasets
- [x] Synthetic validation passes (>= 95% success rate)
- [x] BY correction correctly applied across all tests
- [x] Threshold sweep includes all 5 thresholds {0.1, 0.2, 0.3, 0.4, 0.5}
- [x] All outputs generated in correct directories
- [x] Documentation complete and accurate
- [x] No synthetic data in final results
- [x] Explicit associational language in reports