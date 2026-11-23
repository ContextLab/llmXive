# Architecture Documentation

## Overview

This document describes the architecture of the llm-code-review-impact research pipeline.

## Design Principles

1. **Modularity**: Each user story is implemented independently with clear interfaces
2. **Reproducibility**: Random seeds are managed centrally for all sampling operations
3. **Data Integrity**: All raw data is checksummed; no synthetic data fallbacks
4. **Fail-Loud**: Scripts fail explicitly on errors rather than silently degrading
5. **Auditability**: Manual validation gates ensure classification accuracy

## Component Architecture

### Data Layer (`code/data/`)

- **fetch_github.py**: Handles GitHub API interaction with rate limiting and backoff
- **classify_prs.py**: Primary classification using signatures, secondary using code analysis
- **save_labeled_dataset.py**: Persists classified PRs with metadata
- **extract_metrics.py**: Calculates review metrics from raw PR data
- **save_metrics.py**: Persists metrics to CSV format

### Analysis Layer (`code/analysis/`)

- **complexity.py**: Computes cyclomatic complexity and LOC for PR diffs
- **save_complexity_scores.py**: Persists complexity scores joined with PR data
- **statistical_tests.py**: Implements t-tests (primary) and Mann-Whitney U (sensitivity)
- **sensitivity_analysis.py**: Re-runs tests on detector-filtered cohorts
- **visualizations.py**: Generates boxplots, histograms, and correlation plots
- **generate_results_report.py**: Aggregates statistical findings
- **generate_final_report.py**: Compiles complete research summary
- **generate_final_report_pdf.py**: Creates PDF visualization report

### Audit Layer (`code/audit/`)

- **manual_validation.py**: Implements stratified sampling, human judgment checklist, error rate calculation

### Utilities (`code/utils/`)

- **seeds.py**: Centralized random seed management
- **config.py**: Repository lists, thresholds, and API settings
- **logging.py**: Configurable logging with file rotation
- **checksum.py**: SHA-256 checksum generation and verification

## Data Flow

```
GitHub API
 ↓ (T013)
data/raw/*.json (checksummed)
 ↓ (T014, T015)
Classified PRs (in memory)
 ↓ (T017)
data/processed/prs_labeled.csv
 ↓ (T033)
data/processed/complexity_scores.csv
 ↓ (T022)
data/processed/prs_metrics.csv
 ↓ (T024a, T024b)
data/processed/results.json
 ↓ (T019a, T019b)
data/audit/error_rate.json → data/processed/gate_status.json
 ↓ (T034, T035)
reports/figures/*.pdf
 ↓ (T037)
Final Report PDF
```

## Statistical Methodology

### Primary Analysis
- Independent two-sample t-tests comparing LLM vs human groups
- Metrics: comment density, time-to-merge
- Significance level: α = 0.05 (no multiple-comparison correction)
- Effect size: Cohen's d

### Sensitivity Analysis
- Mann-Whitney U tests for non-parametric verification
- Secondary detector cohort filtering

### Confounding Control
- Cyclomatic complexity scores computed for all PRs
- Correlation analysis between complexity and review metrics
- Complexity included as covariate in regression analysis

## Audit Framework

### Sample Size Calculation
```
n = max(minimum_threshold, ceil(0.10 * N_LLM))
```

### Error Rate Threshold
- Maximum acceptable error rate: 5%
- Gate blocks final report if error rate exceeds threshold

### Ground Truth
- Human expert judgment is the ground truth (SC-004)
- Secondary detector is validation metric only, NOT ground truth

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies (GitHub API, file I/O)
- Verify edge cases and error handling

### Integration Tests
- Test end-to-end pipeline stages
- Verify file outputs exist and contain expected schemas
- Test rate limiting and backoff behavior

### Test Execution Order
1. Run unit tests (fast, no dependencies)
2. Run integration tests (requires data files)
3. Run full pipeline (complete end-to-end)

## Configuration Management

All configurable parameters are centralized in `code/utils/config.py`:
- Repository list for data collection
- API rate limits and retry settings
- Statistical thresholds
- Audit sample size parameters

## Logging Infrastructure

- File-based logging with rotation
- Separate log files for data/ and reports/
- Configurable log levels per module

## Reproducibility

- All random operations use `utils.seeds.SeedManager`
- Global seed set at pipeline start
- Checksums verify data integrity across runs

## Error Handling

- **Fetch failures**: Exponential backoff with max retries, then fail loudly
- **Classification failures**: Flag ambiguous cases (confidence < 0.6)
- **Memory limits**: Fallback to standard metrics if >6GB usage
- **Audit failures**: Block final report if error rate > 5%

## Future Considerations

- Support for additional LLM sources beyond Copilot
- Extended review metrics (sentiment analysis, code quality scores)
- Interactive dashboard for results exploration
- Real-time classification during PR submission