# Project Plan: Assessing Statistical Significance of Observed Correlations in Public Databases

## Overview
This project assesses the statistical significance of observed correlation structures in multivariate datasets from public databases (specifically UCI). The core hypothesis is that observed network statistics (edge density, clustering, etc.) derived from correlation matrices are significantly higher than what would be expected by chance, after controlling for multiple testing.

## Phase 0: Requirements & Design (Completed)
- Review UCI dataset characteristics
- Define network statistics of interest
- Establish null model generation methodology
- Define multiple testing correction approach

## Phase 1: Infrastructure & Data Pipeline (Completed)
- Set up project structure and dependencies
- Implement data loading from UCI repository
- Create data hygiene pipeline (missing values, constant variables)
- Establish configuration management

## Phase 2: Core Statistical Engine (Completed)
- Implement correlation matrix computation (Pearson, Spearman)
- Build graph construction logic with configurable thresholds
- Create permutation engine for null distribution generation
- Implement network statistic calculators

## Phase 3: Validation & Correction (Completed)
- Validate null model using synthetic identity covariance data
- Implement Benjamini-Yekutieli correction for dependent tests
- Generate empirical p-values with proper handling of extreme values

## Phase 4: Threshold Sensitivity Analysis (Completed)
- Implement threshold sweep across {0.1, 0.2, 0.3, 0.4, 0.5}
- Generate sensitivity reports showing variation in significant findings
- Create visualizations for primary threshold (|r| > 0.3)

### Threshold Sweep Specification
The threshold sensitivity analysis explicitly sweeps across the following absolute correlation thresholds:
**{0.1, 0.2, 0.3, 0.4, 0.5}**

This range was selected to:
1. Provide a baseline at 0.1 (weak correlation)
2. Cover moderate correlations (0.2, 0.3)
3. Test strong correlation thresholds (0.4, 0.5)
4. Align with Spec FR-005 requirements for comprehensive sensitivity analysis

Each threshold value triggers a full re-run of:
- Permutation null distribution generation (N=1,000 permutations)
- Graph construction at that specific threshold
- Network statistic calculation
- Empirical p-value computation
- Benjamini-Yekutieli correction
- Significance flagging

The output includes a summary table with significant counts for each threshold, explicitly including the 0.1 baseline data point as required by FR-005.

## Phase 5: Reporting & Visualization (Completed)
- Generate associational language reports
- Create heatmaps and histograms
- Compile final results with proper documentation

## Key Design Decisions

### Multiple Testing Correction
- **Chosen Method**: Benjamini-Yekutieli (BY) procedure
- **Rationale**: Controls FDR under arbitrary dependence structures, appropriate for correlated network statistics
- **Implementation**: Applied across all tests (datasets × 4 statistics)

### Permutation Strategy
- **Sample Size**: N=1,000 permutations (optimized from Spec's N=2,000 per Plan Phase 1)
- **Exception**: Reduced to N=500 for clustering coefficient on datasets with >50 variables
- **Marginal Preservation**: Permutations preserve marginal distributions while breaking dependencies

### Threshold Selection
- **Primary Threshold**: |r| > 0.3 (used for main visualizations)
- **Sweep Range**: {0.1, 0.2, 0.3, 0.4, 0.5} (explicitly defined to resolve ambiguity)
- **Rationale**: Provides comprehensive sensitivity analysis across weak to strong correlations

### Data Sources
- **Primary**: UCI Machine Learning Repository multivariate datasets
- **Requirements**: ≥20 continuous variables, no constant variables after hygiene
- **Discovery**: Dynamic discovery mechanism if primary list yields <3 valid datasets

## Success Criteria

1. **Null Model Validation**: ≥95% of synthetic identity covariance runs show p > 0.05
2. **Data Coverage**: Successfully process ≥3 valid UCI datasets
3. **Sensitivity Analysis**: Complete threshold sweep across all 5 specified values
4. **Correction Application**: BY correction applied to all tests with proper FDR control
5. **Report Quality**: All outputs use associational language and include required visualizations

## Risk Mitigation

- **Data Availability**: Dynamic discovery ensures sufficient datasets even if primary list fails
- **Computational Load**: Reduced permutation counts for large datasets; streaming for large files
- **Multiple Testing**: BY procedure chosen over BH for dependence robustness
- **Threshold Ambiguity**: Explicit {0.1, 0.2, 0.3, 0.4, 0.5} range defined in this plan

## Future Work

- Explore additional network statistics
- Investigate alternative null models
- Extend to time-series correlation structures
- Add interactive visualization capabilities