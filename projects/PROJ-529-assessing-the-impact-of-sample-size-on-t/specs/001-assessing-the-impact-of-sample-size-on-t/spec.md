# Specification: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## User Stories

### US1: Data Acquisition and Subsampling Pipeline
As a researcher, I want to acquire real-world meta-analyses and generate bootstrap subsamples
so that I can analyze the impact of sample size on meta-analytic reliability.

**Acceptance Criteria:**
- AC-001: Download at least 50 meta-analyses from Cochrane/Campbell
- AC-002: Generate up to 100 bootstrap subsamples for each k (3 to N)
- AC-003: Log all subsample iterations with seeds and estimator types

### US2: Stability and Coverage Metric Computation
As a researcher, I want to compute pooled effect sizes and derive stability/coverage metrics
so that I can quantify the reliability of meta-analytic estimates at different sample sizes.

**Acceptance Criteria:**
- AC-004: Fit FE/RE models with appropriate estimator switching (DL for k≥10, REML for k<10)
- AC-005: Calculate SD of pooled effects across subsamples for each k
- AC-006: Compute CI coverage rates for each k

### US3: Threshold Detection and Visualization
As a researcher, I want to detect diminishing returns thresholds and generate diagnostic plots
so that I can identify the minimum k required for stable meta-analytic estimates.

**Acceptance Criteria:**
- AC-007: Fit GAM model to stability metrics and detect changepoint
- AC-008: Generate stability curve plots with confidence bands
- AC-009: Save threshold estimates to JSON and update research.md