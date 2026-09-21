# Project Specification: Automated Detection of Algorithmic Bias in Public Code Repositories

## 1. Overview

This project implements an automated pipeline to detect and quantify algorithmic bias in public code repositories. The system analyzes code artifacts (variable names, comments) for textual bias indicators and correlates these with simulated fairness degradation metrics to identify high-risk repositories.

## 2. Objectives

- **Primary Goal**: Automatically detect potential algorithmic bias in code repositories using static analysis
- **Secondary Goal**: Correlate textual bias indicators with fairness degradation slopes
- **Validation**: Ensure synthetic data independence and validate sentiment analysis thresholds

## 3. User Stories

### US1: Static Code Artifact Extraction (Priority: P1)
As a researcher, I want to extract and quantify "Textual Bias Scores" from Python repositories without executing code, so that I can identify potentially biased code patterns.

### US2: Simulated Bias Injection & Fairness Proxy (Priority: P2)
As a researcher, I want to generate domain-neutral synthetic datasets and simulate bias injection to compute fairness metrics as ground truth proxies, so that I can establish a baseline for fairness degradation.

### US3: Correlation & Statistical Validation (Priority: P3)
As a researcher, I want to correlate "Textual Bias Scores" with "Simulated Fairness Metrics" (specifically the degradation slope) and apply statistical corrections, so that I can identify statistically significant relationships between textual bias and fairness impact.

### US4: Manual Validation of VADER Thresholds (Priority: P2)
As a researcher, I want to validate VADER sentiment thresholds against a manually labeled subset, so that I can ensure the reliability of the sentiment analysis component.

## 4. Functional Requirements

### FR-001: AST Parsing
The system MUST parse Python Abstract Syntax Trees (AST) to extract variable names, function names, and string literals without executing code.

### FR-002: Lexicon Matching
The system MUST match extracted tokens against a curated demographic lexicon to compute "Textual Bias Scores".

### FR-003: Sentiment Analysis
The system MUST use VADER sentiment analysis to evaluate code comments for biased language patterns.

### FR-004: Synthetic Data Generation
The system MUST generate domain-neutral synthetic datasets using realistic class imbalances without using code tokens.

### FR-005: Bias Injection & Fairness Metrics
The system MUST inject controlled bias into synthetic datasets and calculate fairness metrics (Demographic Parity, Equalized Odds) using `fairlearn`.

### FR-006: Correlation Analysis (AMENDED)
The system MUST compute Spearman's rank correlation coefficients between the aggregated **Textual Bias Scores** and the **Fairness Degradation Slopes** (d(Fairness Metric)/d(Skew)) across the repository dataset.

### FR-007: Multiple Comparison Correction
The system MUST apply Bonferroni correction when computing p-values for multiple correlation tests.

### FR-008: Sensitivity Analysis
The system MUST perform sensitivity analysis by sweeping alpha across a range of significance levels and reporting "High Risk" counts.

### FR-009: Repository Aggregation
The system MUST aggregate file-level scores into repository-level scores using the mean of file scores (excluding 0-token files).

### FR-010: Threshold Validation
The system MUST halt pipeline execution if Cohen's Kappa score for VADER validation is below 0.6.

### FR-012: Controlled Bias Injection
The system MUST support an `injected_skew_magnitude` parameter to control the degree of bias injection in synthetic data.

### FR-013: Validation Dataset Usage
The system MUST use a manually labeled validation dataset (200 comments) to validate sentiment thresholds. [UNRESOLVED-CLAIM: c_16a1c0e7 — status=not_enough_info]

### FR-014: Error Injection Testing
The system MUST generate an 'Error Injection Dataset' of repositories with syntax errors to test robustness.

### FR-015: Synthetic Data Independence
The system MUST verify zero token overlap between synthetic data and code tokens using string-hash comparison.

### FR-016: Statistical Noise Threshold (AMENDED)
The statistical noise threshold (a predefined low magnitude) MUST be derived from a pilot run OR a cited statistical model.

## 5. Success Criteria

### SC-001: Correlation Analysis (AMENDED)
The correlation analysis must successfully compute a Spearman correlation coefficient and a Bonferroni-corrected p-value for the relationship between Textual Bias Scores and **Fairness Degradation Slopes**.

### SC-002: High Risk Flagging
The system must correctly flag repositories as "High Risk" when p < 0.05 after Bonferroni correction.

### SC-003: Performance
The system must process 500 repositories in ≤6h on a 2-core CPU. [UNRESOLVED-CLAIM: c_025d2083 — status=not_enough_info]

### SC-004: Independence Verification (AMENDED)
The system must perform a **diff check** (set-difference on normalized token streams) to verify zero token overlap between synthetic data and code tokens.

### SC-005: Error Handling Success Rate
The system must handle ≥95% of syntax errors gracefully without crashing. [UNRESOLVED-CLAIM: c_01b647bb — status=not_enough_info]

### SC-006: Error Report Generation
The system must generate an `error_handling_report.json` with success rates and error statistics.

## 6. Methodology Notes

### 6.1 Fairness Degradation Slopes
Per the methodology correction (Methodology-a39d8d77), the system computes the **slope** of fairness degradation (d(Fairness)/d(Skew)) by sweeping `injected_skew_magnitude` values, rather than using static fairness metrics. This slope represents the rate at which fairness degrades as bias is introduced.

### 6.2 Statistical Noise Threshold
The noise threshold is derived from a pilot run (T028) or a cited statistical model (T028b). It is NOT hardcoded.

### 6.3 Synthetic Data Independence
Synthetic data must be generated from noise distributions, not code tokens. A diff check (set-difference) must verify zero overlap.

## 7. Data Models

### Repository Bias Profile
```yaml
repo_id: str
textual_bias_score: float
fairness_degradation_slope: float
correlation_p_value: float
is_high_risk: bool
```

### Independence Report
```yaml
overlap_count: int
status: "PASS" | "FAIL"
pass_fail: bool
```

### Correlation Results
```yaml
spearman_coefficient: float
bonferroni_p_value: float
high_risk_count: int
sensitivity_analysis: list
```

## 8. Configuration

The system loads configuration from `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml`.

Key configuration parameters:
- `CITATION_TITLE_OVERLAP_THRESHOLD`: Threshold for title overlap detection
- `SENTIMENT_THRESHOLD`: VADER sentiment threshold for bias detection
- `NOISE_THRESHOLD`: Statistical noise threshold from pilot run
- `MAX_REPOS`: Maximum number of repositories to process

## 9. Dependencies

- Python 3.11+
- `numpy`, `pandas`, `scipy`
- `vaderSentiment`
- `fairlearn`
- `datasets`
- `pyyaml`
- `pytest`

## 10. Output Artifacts

- `data/processed/textual_bias_scores.csv`: Per-repo textual bias scores
- `data/processed/slopes_dataset.csv`: Per-repo fairness degradation slopes
- `data/processed/correlation_results.json`: Final correlation analysis results
- `data/processed/independence_report.json`: Synthetic data independence verification
- `data/processed/error_handling_report.json`: Error handling success rates
- `data/processed/noise_threshold.yaml`: Derived statistical noise threshold