# Project Specification: The Impact of Perceived Control Over Digital Environments on Anxiety

## Overview
This research project investigates the correlation between perceived control over digital environments (proxied by metadata patterns) and anxiety levels in social media posts.  
The dataset used is the HuggingFace **`tweet_eval`** collection, which includes the required `timestamp` and `user_id` fields for per‑user analyses.

## User Stories

### US1: Data Ingestion and Anxiety Scoring
As a researcher, I want to ingest a public social media dataset and assign anxiety scores using a CPU‑tractable model so that I can analyze anxiety levels across posts.

**Acceptance Criteria:**
- AC-001: System downloads `tweet_eval` from HuggingFace and stores it as `data/raw/social_media.csv`.
- AC-002: Non‑English text is filtered out using language detection with confidence ≥ 0.8; gibberish text is filtered out using entropy < 3.5 bits.
- AC-003: Anxiety scores are generated for ≥ 95 % of rows **that pass the confidence ≥ 0.6 filter**.
- AC-004: Low‑confidence predictions (confidence < 0.6) are excluded from the final scoring set.

### US2: Control Proxy Extraction
As a researcher, I want to extract metadata‑based proxies for "perceived control" without accessing text content, so that I can maintain independence between variables.

**Acceptance Criteria:**
- AC-005: `filter_applied` metadata contributes to the control proxy score with a weight of 0.3.
- AC-006: `timestamp_regularity` is calculated per user as the coefficient of variation of inter‑tweet intervals (requires ≥ 5 tweets per user **and the presence of `timestamp` and `user_id` fields**, which are guaranteed by the chosen `tweet_eval` dataset). Users with fewer tweets are excluded.
- AC-007: No text content column is read during proxy extraction; only metadata fields are used.

### US3: Statistical Correlation and Visualization
As a researcher, I want to perform statistical analysis and generate visualizations to determine if a significant correlation exists between control proxies and anxiety scores.

**Acceptance Criteria:**
- AC-008: Shapiro‑Wilk test is performed on residuals to check normality (α = 0.05).
- AC-009: If normality is violated, Spearman correlation is used; otherwise Pearson correlation.
- AC-010: Results include a significance flag (p < 0.05).
- AC-011: A scatter plot with regression line is generated and saved as PNG.
- AC-012: The analysis controls for confounding variables by including `timestamp_of_day`, `day_of_week`, and a user‑level random intercept in the regression model.

## System Constraints (SC)

### SC-001: CPU Tractability (See US1, US2, US3)
All model inference must run on CPU without CUDA or quantization.

### SC-002: Data Independence (See US2)
Proxy extraction must not access text content (Constitution Principle VI).

### SC-003: Error Handling (See US1, US2, US3)
The pipeline must handle empty datasets and download failures gracefully.

### SC-004: Runtime Threshold (See US1, US2, US3)
The entire pipeline execution must complete within **6 hours** on standard free‑tier cloud runners (e.g., GitHub Actions, Google Colab free tier). If this threshold is exceeded, the pipeline aborts with exit code 3 and logs “runtime exceeded”.

### SC-005: Reproducibility (See US1, US2, US3)
All random seeds must be fixed (seed = 42) and documented in `code/config.py`.

## Data Model

### Raw Data
- Source: HuggingFace `tweet_eval` (includes `timestamp` and `user_id` fields)
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

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the HuggingFace `tweet_eval` dataset and save it to `data/raw/social_media.csv`. (See US1)
- **FR-002**: System MUST filter out non‑English posts using a language‑detection model with confidence ≥ 0.8. (See US1)
- **FR-003**: System MUST filter out gibberish posts using entropy < 3.5 bits as the cutoff. (See US1)
- **FR-004**: System MUST generate anxiety scores with a CPU‑only model and assign a confidence score; predictions with confidence < 0.6 are excluded. (See US1)
- **FR-005**: System MUST ensure that anxiety scores are produced for ≥ 95 % of rows that remain after confidence filtering. (See US1)
- **FR-006**: System MUST extract a control proxy using only metadata fields (`filter_applied` and `timestamp_regularity`) without reading any text column. (See US2)
- **FR-007**: System MUST compute `timestamp_regularity` per user as the coefficient of variation of inter‑tweet intervals, requiring ≥ 5 tweets per user; users with fewer tweets are omitted. (See US2)
- **FR-008**: System MUST combine `filter_applied` (weight 0.3) and `timestamp_regularity` (weight 0.7) into a composite control score in the range [0, 1]. (See US2)
- **FR-009**: System MUST perform a Shapiro‑Wilk test on regression residuals (α = 0.05). (See US3)
- **FR-010**: System MUST compute Pearson correlation if residuals are normal; otherwise compute Spearman correlation (two‑sided). (See US3)
- **FR-011**: System MUST adjust for confounding variables by including `timestamp_of_day`, `day_of_week`, and a user‑level random intercept as covariates in the correlation analysis. (See US3)
- **FR-012**: System MUST generate a scatter plot with regression line, annotate the p‑value, and save it as a PNG file. (See US3)
- **FR-013**: System MUST fit a mixed‑effects regression model with a random intercept for `user_id` to account for user‑level effects, and report variance components. (See US3)

### Key Entities *(include if feature involves data)*

- **SocialMediaPost**: Represents a single post with metadata fields (`user_id`, `timestamp`, `filter_applied`, etc.) but no text content used in proxy extraction.
- **AnxietyScore**: Numeric score derived from the CPU‑only model, together with a confidence value.

## Success Criteria

- **SC-101**: Download completes and the file’s MD5 checksum matches the expected value. (See US1)
- **SC-102**: Language filter removes ≤ 5 % of English posts; confidence threshold 0.8 is applied correctly. (See US1)
- **SC-103**: Gibberish filter removes posts with entropy < 3.5 bits; a random sample audit confirms correctness. (See US1)
- **SC-104**: Anxiety scoring achieves ≥ 95 % coverage of rows that pass the confidence ≥ 0.6 filter; coverage metric recorded in `coverage_report.json`. (See US1)
- **SC-105**: Proxy extraction runs without reading any text column; log entry “text column not accessed” is present. (See US2)
- **SC-106**: `timestamp_regularity` is successfully computed for ≥ 80 % of eligible users; results stored in `proxy_results.csv`. (See US2)
- **SC-107**: Composite control score lies within [0, 1] and basic sanity checks (e.g., monotonicity with `filter_applied`) pass. (See US2)
- **SC-108**: Shapiro‑Wilk p‑value > 0.05 indicates normality; otherwise the pipeline switches to Spearman as recorded in `analysis_results.json`. (See US3)
- **SC-109**: Correlation test yields p‑value < 0.05 and the significance flag is set to true. (See US3)
- **SC-110**: Scatter plot PNG contains a regression line and annotated p‑value; visual inspection checklist passed. (See US3)
- **SC-111**: Pipeline exits with code 0 on success, 1 on download failure (with up to 3 retries), 2 on empty dataset, and logs explicit messages for each scenario. (See SC-003)
- **SC-112**: Runtime is measured; if it exceeds 6 hours, the pipeline aborts with exit code 3 and logs “runtime exceeded”. (See SC-004)
- **SC-113**: Random seeds are fixed to 42 in `code/config.py`; the config file contains a comment confirming the seed. (See SC-005)
- **SC-114**: Mixed‑effects regression converges, reports variance components for `user_id`, and the control‑proxy coefficient remains significant (p < 0.05) after adjustment. (See US3)

## Assumptions

- Users have stable internet connectivity to download the HuggingFace dataset.
- The `tweet_eval` dataset provides sufficient tweet volume to compute `timestamp_regularity`.
- Existing CPU resources are sufficient for model inference within the runtime budget.
- The anxiety model outputs a confidence score in the range [0, 1].