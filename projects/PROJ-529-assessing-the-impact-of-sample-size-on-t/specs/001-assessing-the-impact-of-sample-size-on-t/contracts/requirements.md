# Requirements: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Functional Requirements

### FR-001: Data Acquisition
- The system shall acquire at least 50 real-world meta-analyses
- Fallback to simulation if real data acquisition fails

### FR-002: Subsampling
- The system shall generate up to 100 bootstrap subsamples for each k
- Subsamples must be logged with seeds and estimator types

### FR-003: Model Selection
- Use DerSimonian-Laird (DL) estimator for k ≥ 10
- Use Restricted Maximum Likelihood (REML) estimator for k < 10

### FR-004: Stability Metrics
- Calculate SD of pooled effects across subsamples for each k
- Compute CI coverage rates for each k

### FR-005: Threshold Detection
- Fit GAM model to stability metrics
- Detect inflection point where derivative < 0.05

### FR-006: Visualization
- Generate stability curve plots with confidence bands
- Generate coverage plots by study count

### FR-007: Configuration
- All thresholds must be configurable via config.py
- Default nominal coverage target: 0.95
- Default stability threshold: 0.05

### FR-008: Error Handling
- Handle zero-variance studies gracefully
- Handle negative variance estimates
- Implement boundary clamping

### FR-009: Sensitivity Analysis
- Perturb reference value by its SE
- Quantify variation in coverage rates

### FR-010: Memory Safety
- Implement chunked data processing for large corpora
- Ensure memory usage stays within limits