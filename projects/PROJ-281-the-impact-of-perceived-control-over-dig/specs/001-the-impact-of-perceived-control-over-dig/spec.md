# Feature Specification: The Impact of Perceived Control Over Digital Environments on Anxiety

**Feature Branch**: `001-perceived-control-anxiety`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does perceived control over digital interface elements correlate with reduced anxiety markers in public social media traces?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Anxiety Scoring (Priority: P1)

The system must download a public social media dataset, preprocess the text, and apply a validated machine learning model to assign an anxiety score to each post.

**Why this priority**: This is the foundational data layer. Without reliable anxiety scores derived from the text, no correlation analysis can be performed. It delivers the primary dependent variable for the study.

**Independent Test**: The system can be fully tested by running the ingestion pipeline on a small, fixed sample of 100 known posts and verifying that anxiety scores are generated for [deferred] of them, with no null values, and that the distribution of scores matches the expected range (0.0 to 1.0) defined by the model.

**Acceptance Scenarios**:

1. **Given** a valid HuggingFace dataset ID for social media text, **When** the ingestion script runs, **Then** the system downloads the text data and stores it in a local CSV file with at least 10,000 rows.
2. **Given** a pre-trained anxiety detection model, **When** the pipeline processes the downloaded text, **Then** every row in the output dataset receives a numeric anxiety score between 0.0 and 1.0.
3. **Given** a dataset containing non-English or gibberish text, **When** the preprocessing step runs, **Then** the system filters out non-English entries or flags them for exclusion before scoring.

---

### User Story 2 - Control Proxy Extraction (Priority: P2)

The system must extract metadata-based proxies representing "perceived control" from the same dataset, ensuring these proxies are derived strictly from metadata (timestamps, API interaction flags) and are independent of the text content used for anxiety scoring.

**Why this priority**: This provides the primary independent variable. It must be implemented after data ingestion to ensure the proxies align with the specific posts scored in Story 1. Crucially, it must avoid semantic content to satisfy Constitution Principle VI.

**Independent Test**: The system can be tested by processing a subset of posts where the presence of control-related metadata flags (e.g., `filter_applied=true`) and timestamp patterns are manually verified against the extracted proxy values, ensuring a ≥95% match on a test set of 50 items.

**Acceptance Scenarios**:

1. **Given** a post with metadata indicating `filter_applied=true`, **When** the extraction script runs, **Then** the `control_proxy` field for that post is incremented by 1.0.
2. **Given** a sequence of posts from a single user with timestamps varying by less than 5 minutes, **When** the extraction script runs, **Then** the `timestamp_regularity` metric for that user is calculated and stored.
3. **Given** a post with no control-related metadata flags and irregular timestamps, **When** the extraction script runs, **Then** the resulting `control_proxy` score is 0.0.

---

### User Story 3 - Statistical Correlation and Visualization (Priority: P3)

The system must perform a statistical analysis to test the correlation between the control proxy and anxiety scores, including a robustness check for normality assumptions, and generate a scatter plot with the regression line.

**Why this priority**: This delivers the final research output. It depends on the data prepared in Stories 1 and 2 and validates the core hypothesis while ensuring statistical validity.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with a known negative correlation (e.g., r = -0.5) and verifying that the output regression coefficient is negative and the p-value is < 0.05, or that the fallback Spearman correlation is used if normality assumptions are violated.

**Acceptance Scenarios**:

1. **Given** a dataset with `anxiety_score` and `control_proxy` columns, **When** the analysis script runs, **Then** the system first performs a Shapiro-Wilk test on the residuals of a preliminary linear fit.
2. **Given** a dataset where residuals violate normality (p < 0.05), **When** the analysis script runs, **Then** the system automatically switches to Spearman's rank correlation and outputs the resulting coefficient and p-value.
3. **Given** a dataset where residuals meet normality assumptions, **When** the analysis script runs, **Then** the system outputs a Pearson correlation coefficient and a p-value.
4. **Given** a successful analysis, **When** the visualization step runs, **Then** a PNG file is generated containing a scatter plot with the appropriate regression line (OLS or rank-based) and axis labels.

---

### Edge Cases

- What happens when the downloaded dataset is empty or contains fewer than 100 posts? (System should fail gracefully with a specific error code, not crash).
- How does the system handle posts where the anxiety model returns a confidence score below a threshold? (These posts should be excluded from the final analysis).
- What happens if the control proxy extraction logic encounters a post with missing metadata fields? (The system should default the proxy score to 0.0 and log a warning).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download a public social media dataset from HuggingFace or OpenML and store it locally without requiring internet access during the analysis phase. (See US-1)
- **FR-002**: System MUST apply a pre-trained anxiety detection model to assign a continuous anxiety score (0.0–1.0) to every text entry in the dataset. (See US-1)
- **FR-003**: System MUST extract a `control_proxy` score based strictly on metadata fields (e.g., `filter_applied` flags, `timestamp_regularity` metrics) and MUST NOT rely on semantic content or keyword presence in the post text. (See US-2)
- **FR-004**: System MUST perform a statistical analysis (Pearson or Spearman, based on normality check) to calculate the correlation coefficient and p-value between the `control_proxy` and `anxiety_score` variables. (See US-3)
- **FR-005**: System MUST generate a scatter plot visualization showing the relationship between control proxies and anxiety scores, including the regression line appropriate for the selected correlation method. (See US-3)
- **FR-006**: System MUST exclude data points where the anxiety model confidence is below 0.6 to ensure measurement validity. Confidence is defined as the maximum probability of the predicted class from the model's output distribution; if the model does not output probabilities, the raw confidence score must be used. (See US-1)

### Key Entities

- **SocialPost**: A record containing the raw text, metadata (timestamp, user ID, interaction flags), and derived scores (anxiety_score, control_proxy).
- **AnalysisResult**: A summary object containing the correlation coefficient, p-value, regression slope, the method used (Pearson/Spearman), and a flag indicating statistical significance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: ≥95% of non-null dataset rows must be successfully assigned an anxiety score. (See US-1)
- **SC-002**: The system successfully computes and outputs the correlation coefficient (r) and p-value for the provided dataset. (See US-3)
- **SC-003**: The p-value of the regression analysis is measured against the significance threshold of 0.05 to determine if the association is statistically significant. (See US-3)
- **SC-004**: The runtime of the entire analysis pipeline (ingestion to visualization) is measured against the standard free-tier limit. (See US-1)
- **SC-005**: The memory usage peak during model inference is measured against the RAM limit of the free-tier runner. (See US-1)

## Assumptions

- The public social media dataset selected from HuggingFace/OpenML contains sufficient text volume (≥ 10,000 posts) and metadata fields (timestamp, user ID, interaction flags) to perform the analysis.
- The anxiety detection model referenced in the related work can be loaded and executed on a CPU-only environment without requiring CUDA or GPU acceleration.
- The "perceived control" proxies (metadata flags and timestamp regularity) are valid and independent operationalizations of the psychological construct, distinct from the NLP features used for anxiety scoring.
- The dataset does not contain significant missing values in the text or timestamp fields that would prevent the extraction of proxies or scoring.
- The statistical analysis pipeline (including normality checks and fallback methods) is appropriate for testing the association between these variables.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to process the dataset and run the inference model within 6 hours.