# Feature Specification: Sample Size Impact on Meta-Analysis

## User Stories

### US1: Data Acquisition and Subsampling
As a researcher, I want to acquire a corpus of meta-analyses and generate bootstrap subsamples so that I can analyze the effect of study count (k) on reliability.
- **Acceptance Criteria**:
 - System downloads real data from Cochrane/Campbell or generates valid simulation data if download fails.
 - System generates up to 100 bootstrap subsamples for each k from 3 to N.
 - Subsample data is logged and stored in `data/processed/`.

### US2: Stability and Coverage Metric Computation
As an analyst, I want to compute pooled effects and stability metrics for every subsample so that I can quantify reliability.
- **Acceptance Criteria**:
 - System calculates pooled effect sizes using DL (k>=10) and REML (k<10).
 - System computes the standard deviation of pooled effects across subsamples.
 - System calculates CI coverage rates relative to the full-sample estimate.
 - Results are aggregated in `data/processed/stability_metrics.csv`.

### US3: Threshold Detection and Visualization
As a decision-maker, I want to identify the minimum sample size (k) where estimates stabilize so that I can determine when a meta-analysis is reliable.
- **Acceptance Criteria**:
 - System fits a GAM to stability metrics to detect inflection points.
 - System identifies the k where coverage rate stabilizes within ±2% of nominal.
 - Diagnostic plots (stability curves, coverage plots) are generated in `data/output/`.
 - Threshold estimate is saved to `data/output/threshold_estimate.json`.

## Constraints
- **Data Integrity**: No fake data. Must use real sources or documented simulation parameters.
- **Performance**: Analysis must complete within 6 hours on 2 CPU cores.
- **Reproducibility**: All random operations must use deterministic seeds logged per iteration.
