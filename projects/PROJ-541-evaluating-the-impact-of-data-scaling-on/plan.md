# Project Plan: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

## Overview
This project evaluates how data scaling methods (Standardization, Min-Max, Robust) affect the robustness of statistical tests (t-test, ANOVA, Chi-squared) under varying data conditions and sample sizes.

## Objectives
1. Generate synthetic datasets with controlled distributional properties (null and alternative hypotheses).
2. Apply scaling methods and run statistical tests.
3. Aggregate results and calculate empirical error rates and power.
4. Validate findings on real-world datasets.
5. Analyze the impact of scaling on test robustness using mixed-effects models.

## User Stories

### US1: Simulation Engine for Null and Alternative Hypotheses
- Generate synthetic datasets with known ground truth.
- Validate generated data against theoretical expectations.
- Persist data with metadata for reproducibility.

### US2: Scaling Application and Statistical Testing Pipeline
- Implement scaling methods (Standardization, Min-Max, Robust).
- Run parametric tests (t-test, ANOVA, Chi-squared) on scaled data.
- Verify p-value invariance under linear transformations.

### US3: Aggregation, Mixed-Effects, and Visualization
- Aggregate simulation results across iterations.
- Calculate empirical error rates and power with confidence intervals.
- Fit mixed-effects models to analyze scaling impact.
- Generate visualizations and reports.

### US4: Real-World Dataset Validation
- Ingest public datasets (UCI/OpenML).
- Apply the same pipeline to real data.
- Compare synthetic vs real-world results.

## Complexity Tracking
- **Simulation Complexity**: Controlled via distribution parameters (mean, variance, skewness, kurtosis).
- **Scaling Complexity**: Three methods with different edge-case handling (e.g., zero variance).
- **Statistical Complexity**: Multiple tests with varying assumptions (normality, homogeneity).
- **Mixed-Effects Complexity**:
 - Mixed-effects models are used for synthetic data with `config_id` as a fixed effect to satisfy FR-010, and `dataset_id` for real-world data.
 - This approach allows for analyzing the impact of scaling methods while accounting for variability across configurations/datasets.
- **Real-World Complexity**: Handling missing values, diverse data types, and varying dataset sizes.

## Execution Strategy
1. **Phase 1**: Setup project structure and dependencies.
2. **Phase 2**: Implement foundational components (logging, config, streaming).
3. **Phase 3**: Build US1 (simulation engine).
4. **Phase 4**: Build US2 (scaling and testing).
5. **Phase 5**: Build US3 (aggregation and mixed-effects).
6. **Phase 6**: Build US4 (real-world validation).
7. **Phase 7**: Polish and cross-cutting concerns.
8. **Phase 8**: Review resolution and data integrity.

## Deliverables
- Synthetic datasets in `data/synthetic/`.
- Scaled datasets in `data/scaled/`.
- Simulation results in `results/simulation_results.csv`.
- Aggregate metrics in `results/aggregate_metrics.csv`.
- Real-world results in `results/real_world_results.csv`.
- Comparison report in `results/comparison_report.md`.
- Visualizations in `results/figures/`.
- Mixed-effects model analysis in `results/mixed_effects_significance_report.md`.

## Dependencies
- Python 3.8+
- NumPy, Pandas, SciPy, Scikit-learn, Statsmodels, Matplotlib, Seaborn
- HuggingFace Datasets (for streaming)
- PyYAML, JSONSchema

## Risk Mitigation
- **Data Integrity**: Fail loudly if real data fetch fails; no synthetic fallback.
- **Performance**: Use streaming for large datasets; sample if necessary with explicit logging.
- **Reproducibility**: Log all seeds, config hashes, and batch IDs.
- **Edge Cases**: Explicitly handle zero variance, missing values, and bin merging in Chi-squared.

## Success Criteria
- All unit and integration tests pass.
- Simulation results match theoretical expectations (error rate ~ alpha).
- Real-world pipeline runs without crashes and produces valid results.
- Mixed-effects model analysis identifies significant scaling effects.
- Comparison report shows meaningful insights between synthetic and real data.