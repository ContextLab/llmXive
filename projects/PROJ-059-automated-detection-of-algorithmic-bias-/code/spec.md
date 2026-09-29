# Project Specification: Automated Detection of Algorithmic Bias in Public Code Repositories

## 1. Executive Summary

This project implements a pipeline to detect and quantify algorithmic bias in public code repositories by analyzing textual artifacts (comments, variable names) and correlating them with simulated fairness degradation. The system uses Natural Language Processing (NLP) to score textual bias and statistical simulation to model fairness metrics under varying skew conditions.

## 2. User Stories

### US1: Static Code Artifact Extraction
**As a** researcher, **I want to** extract and quantify "Textual Bias Scores" from Python repositories without executing code, **so that** I can identify potential bias indicators in code structure and comments.

### US2: Simulated Bias Injection & Fairness Proxy
**As a** researcher, **I want to** generate domain-neutral synthetic datasets and simulate bias injection, **so that** I can compute fairness metrics (Demographic Parity, Equalized Odds) as ground truth proxies for correlation analysis.

### US3: Correlation & Statistical Validation
**As a** researcher, **I want to** correlate "Textual Bias Scores" with "Fairness Degradation Slopes" and apply statistical corrections, **so that** I can validate whether textual bias is predictive of actual fairness degradation in models.

### US4: Manual Validation of VADER Thresholds
**As a** researcher, **I want to** validate VADER sentiment thresholds against a manually labeled subset, **so that** I can ensure the reliability of the sentiment analysis component.

## 3. Functional Requirements

### FR-001: AST Parsing
The system MUST parse Abstract Syntax Trees (AST) of Python files to extract variable names, function names, and string literals.

### FR-002: Lexicon Matching
The system MUST match extracted tokens against a curated demographic lexicon to compute a "Textual Bias Score".

### FR-003: Sentiment Analysis
The system MUST use VADER sentiment analysis to score code comments for bias-related sentiment.

### FR-004: Synthetic Data Generation
The system MUST generate domain-neutral synthetic datasets using `numpy` with realistic class imbalance.

### FR-005: Fairness Metric Calculation
The system MUST calculate fairness metrics (Demographic Parity, Equalized Odds) using `fairlearn`.

### FR-006 (Amended): Fairness Degradation Slope Correlation
The system MUST compute **Spearman's rank correlation coefficients** between the aggregated **Textual Bias Scores** and the **Fairness Degradation Slopes** (d(Fairness Metric)/d(Skew)) across the repository dataset.
- **Input**: Aggregated Textual Bias Scores (from US1), Fairness Degradation Slopes (from US2).
- **Method**: Spearman rank correlation.
- **Output**: Correlation coefficient and p-value.

### FR-007: Bonferroni Correction
The system MUST apply Bonferroni correction for multiple comparisons when reporting statistical significance.

### FR-008: Sensitivity Analysis
The system MUST perform sensitivity analysis by sweeping significance levels (alpha) and reporting "High Risk" counts.

### FR-009: Repository Aggregation
The system MUST aggregate file-level scores into a single repository-level score (mean of file scores, excluding 0-token files).

### FR-010: Threshold Validation
The system MUST halt if the Cohen's Kappa score for VADER validation is below 0.6.

### FR-012: Bias Injection Control
The system MUST support an `injected_skew_magnitude` parameter to control the severity of bias injection in simulations.

### FR-013: VADER Validation
The system MUST compute Cohen's Kappa between VADER predictions and manual labels.

### FR-014: Error Injection
The system MUST generate an 'Error Injection Dataset' of repositories with syntax errors for robustness testing.

### FR-015: Synthetic Data Independence
The system MUST verify zero token overlap between synthetic data and code tokens via set-difference.

### FR-016: Noise Threshold Derivation
The statistical noise threshold MUST be derived from a pilot run OR a cited statistical model.

## 4. Success Criteria

### SC-001 (Amended): Correlation Analysis
The correlation analysis must successfully compute a **Spearman correlation coefficient** and a **Bonferroni-corrected p-value** for the relationship between **Textual Bias Scores** and **Fairness Degradation Slopes**.
- **Metric**: Spearman's rho.
- **Correction**: Bonferroni.
- **Target**: Fairness Degradation Slopes (d(Fairness)/d(Skew)).

### SC-002: High Risk Flagging
The system must flag repositories as "High Risk" if the p-value (after correction) is < 0.05.

### SC-003: Performance
The system must process 500 repositories in ≤ 6 hours on a 2-core CPU.

### SC-004: Independence Verification
The system must perform a **diff check** (set-difference on normalized token streams) to verify zero token overlap between synthetic data and code tokens.

### SC-005: Error Handling
The system must handle syntax errors gracefully (log and skip) without crashing, achieving ≥95% success rate on error-injected datasets.

### SC-006: Robustness
The system must complete the full pipeline on the error injection set and write results to `data/processed/error_handling_report.json`.

## 5. Methodology Note

The correlation target is the **slope** of the fairness degradation curve (d(Fairness Metric)/d(Skew)), not a static fairness metric. This aligns with the Methodology Correction (Methodology-a39d8d77) to ensure that the textual bias score predicts how *sensitive* a model is to skew, rather than just its static fairness at one point.

## 6. Data Model

### Textual Bias Score
- **Type**: Float
- **Source**: Lexicon matching + VADER sentiment
- **Aggregation**: Mean of file scores per repository

### Fairness Degradation Slope
- **Type**: Float
- **Source**: Linear regression of Fairness Metric vs. Skew Magnitude
- **Computation**: `compute_degradation_slope` in `simulation.py`

### Correlation Result
- **Type**: Dict
- **Fields**: `spearman_rho`, `p_value`, `bonferroni_p_value`, `high_risk`

## 7. API Surface

### `src/bias_pipeline/extractor.py`
- `parse_ast_tree`: Parse Python AST.
- `normalize_tokens`: Normalize camelCase/snake_case.
- `analyze_sentiment`: VADER analysis.
- `aggregate_repo_score`: Compute repo-level score.
- `process_single_repo`: End-to-end file processing.
- `run_extraction_pipeline`: Batch processing.

### `src/bias_pipeline/simulation.py`
- `generate_synthetic_data`: Create synthetic dataset.
- `inject_bias_model`: Apply skew.
- `calculate_fairness_metrics`: Compute Demographic Parity/Equalized Odds.
- `compute_degradation_slope`: Calculate d(Fairness)/d(Skew).
- `run_simulation_and_independence_check`: Full simulation + validation.
- `aggregate_slopes`: Combine slopes for correlation.

### `src/bias_pipeline/analyzer.py`
- `compute_spearman_correlation`: Correlate scores and slopes.
- `apply_bonferroni_correction`: Adjust p-values.
- `run_sensitivity_analysis`: Sweep alpha levels.
- `flag_high_risk`: Identify high-risk repos.
- `run_correlation_analysis`: End-to-end correlation.

### `src/bias_pipeline/validator.py`
- `load_validation_dataset`: Load manual labels.
- `run_vader_validation`: Compute Cohen's Kappa.
- `validate_threshold`: Check Kappa >= 0.6.
- `run_validation_pipeline`: Full validation.

### `src/bias_pipeline/independence_checker.py`
- `perform_diff_check`: Verify zero token overlap.
- `generate_independence_report`: Output JSON report.

## 8. Configuration

- **Lexicon**: `data/raw/lexicon.csv` or HuggingFace source.
- **Validation Dataset**: `data/validation/labels.csv` (manual labels).
- **Noise Threshold**: `data/processed/noise_threshold.yaml` (derived from pilot).
- **Slopes Dataset**: `data/processed/slopes_dataset.csv`.
- **Correlation Results**: `data/processed/correlation_results.json`.

## 9. Error Handling

- **Syntax Errors**: Log and skip (do not crash).
- **Missing Data**: Fail loudly with clear error message.
- **Independence Fail**: Exit with non-zero code if token overlap > 0.
- **Validation Fail**: Halt if Cohen's Kappa < 0.6.

## 10. Dependencies

- `numpy`
- `pandas`
- `scipy`
- `vaderSentiment`
- `fairlearn`
- `datasets`
- `pyyaml`
- `pytest`
- `scikit-learn`

## 11. Revision History

- **v1.0**: Initial spec.
- **v1.1 (Amended)**: Updated FR-006 and SC-001 to reflect "Fairness Degradation Slopes" methodology (Methodology-a39d8d77). Removed contradiction with `tasks.md`.
- **v1.2**: Added SC-004 for diff check verification.