# Project Specification: The Impact of Perceived Control Over Digital Environments on Anxiety

## Overview
This research project investigates the correlation between perceived control over digital environments (proxied by metadata patterns) and anxiety levels in social media posts.

## User Stories

### US1: Data Ingestion and Anxiety Scoring
As a researcher, I want to ingest a public social media dataset and assign anxiety scores using a CPU-tractable model so that I can analyze anxiety levels across posts.

**Acceptance Criteria:**
- AC-001: System downloads `cardiffnlp/tweet_sentiment_extraction` from HuggingFace.
- AC-002: Non-English and gibberish text is filtered out.
- AC-003: Anxiety scores are generated for ≥95% of valid rows.
- AC-004: Low-confidence predictions (threshold < 0.6) are excluded.

### US2: Control Proxy Extraction
As a researcher, I want to extract metadata-based proxies for "perceived control" without accessing text content, so that I can maintain independence between variables.

**Acceptance Criteria:**
- AC-005: `filter_applied` metadata contributes to the control proxy score.
- AC-006: `timestamp_regularity` is calculated per user.
- AC-007: No text content is accessed during proxy extraction.

### US3: Statistical Correlation and Visualization
As a researcher, I want to perform statistical analysis and generate visualizations to determine if a significant correlation exists between control proxies and anxiety scores.

**Acceptance Criteria:**
- AC-008: Shapiro-Wilk test is performed on residuals to check normality.
- AC-009: If normality is violated, Spearman correlation is used; otherwise Pearson.
- AC-010: Results include a significance flag (p < 0.05).
- AC-011: A scatter plot with regression line is generated.

## System Constraints (SC)

### SC-001: CPU Tractability
All model inference must run on CPU without CUDA or quantization.

### SC-002: Data Independence
Proxy extraction must not access text content (Constitution Principle VI).

### SC-003: Error Handling
The pipeline must handle empty datasets and download failures gracefully.

### SC-004: Runtime Threshold
The entire pipeline execution must complete within **6 hours** on standard free-tier cloud runners (e.g., GitHub Actions, Google Colab free tier) to ensure reproducibility and cost-effectiveness. If this threshold cannot be met with the current dataset size or model complexity, the dataset size must be reduced or the model architecture simplified.

### SC-005: Reproducibility
All random seeds must be fixed and documented in `code/config.py`.

## Data Model

### Raw Data
- Source: HuggingFace `cardiffnlp/tweet_sentiment_extraction`
- Format: CSV
- Location: `data/raw/social_media.csv`

### Processed Data
- Preprocessed Text: `data/processed/preprocessed_text.csv`
- Scoring Results: `data/processed/scoring_results.csv`
- Proxy Results: `data/processed/proxy_results.csv`
- Final Analysis: `data/processed/final_analysis.csv`
- Coverage Report: `data/processed/coverage_report.json`
- Analysis Results: `data/processed/analysis_results.json`
- Normality Check: `data/processed/normality_check.json`

## Configuration

Global configuration, seeds, and paths are managed in `code/config.py`.