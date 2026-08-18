# Research: The Influence of Emoji Use on Perceived Emotional Intensity in Text

## Overview

This research document defines the dataset strategy, methodological approach, and statistical rigor for the project. It addresses the feasibility of the study given the available open data and compute constraints. The primary scientific question is: "Does a public dataset exist that allows for the direct testing of the relationship between emoji use and human-rated emotional intensity?"

## Dataset Strategy

### Verified Datasets
The project is constrained to the following verified datasets from the `# Verified datasets` block. **Crucially, the study requires a dataset containing `text_content`, `emoji_presence`, AND `human_intensity_score`.**

1.  **CMU Datasets**:
    *   `cmu-arctic`: Audio synthesis dataset. Likely lacks human-rated intensity scores for text.
    *   `cmu-book-summaries`: Summaries of books. Unlikely to contain human-rated intensity scores for individual messages.
    *   `cmu_hinglish_dog`: Dog-related content. Unlikely to contain the required intensity metric.
2.  **NOT (Not Open Text) Datasets**:
    *   `issues-kaggle-notebooks`: GitHub issues. No intensity scores.
    *   `Answerable-or-Not`: Binary classification. No intensity scores.
    *   `vlmbook-notebooks`: Code/Notebook data. No intensity scores.

**Gap Analysis**:
None of the verified datasets listed in the `# Verified datasets` block explicitly contain the required `human_intensity_score` column alongside text messages. The spec assumes a "public text message corpus (e.g., CMU Text Message Corpus)" exists with these fields. However, the verified list provided for this project does not include the "CMU Text Message Corpus" with intensity ratings.

**Resolution**:
Per **Constitution Principle VI** and **FR-002c**, the system MUST halt if the required `human_intensity_score` is missing. Since no verified source in the provided list contains this specific modality, the plan is to:
1.  Attempt to load the most text-rich dataset from the verified list (e.g., `cmu-book-summaries` or `issues-kaggle-notebooks`) to verify the schema.
2.  If `human_intensity_score` is absent (which is expected), the pipeline will trigger the "Data Unavailable" report as required by **US-1** and **US-2**.
3.  **Critical Note**: If the study cannot proceed without human-rated data, and no open source exists in the verified list, the research question as stated cannot be answered with the current available resources. The plan includes the logic to detect this and report it, rather than fabricating scores or using a substitute dataset that lacks the outcome variable. The "Data Unavailable" report is the valid scientific output for this scenario.

*Self-Correction for Implementation*: The implementation will strictly follow the "Data Unavailable" path if the verified datasets do not contain the column. The plan does not invent a new dataset URL.

### Data Loading & Verification Plan
*   **Source**: Hugging Face `datasets` library.
*   **Streaming**: Use `streaming=True` to avoid loading large files into memory if necessary, though expected sizes are small.
*   **Verification**:
    *   Check for `text_content` (or equivalent column).
    *   Check for `human_intensity_score`.
    *   If `human_intensity_score` is missing -> **HALT** and generate report.
    *   If present -> Proceed to extraction.

## Methodological Rigor

### Statistical Approach (Conditional on Data Availability)
If a valid dataset is found, the following rigorous methodology will be applied:

1.  **Descriptive Statistics**:
    *   Calculate distribution of `emoji_count`, `emoji_types`, and `intensity_score`.
    *   Check for skewness in intensity ratings.
2.  **Correlation Analysis**:
    *   **Metric**: Spearman's rank correlation (robust to non-normality of Likert scales) and Pearson's correlation (for comparison).
    *   **Hypothesis**: H0: No association between emoji frequency and intensity.
    *   **Correction**: Bonferroni correction applied for multiple tests (testing each unique emoji type).
3.  **Regression Analysis**:
    *   **Model**: Linear Regression.
    *   **Predictors**: `emoji_count`, `text_length`, `punctuation_count`, `emoji_type` (one-hot encoded).
    *   **Feature Collapsing**: To handle high dimensionality in small datasets (N ~128), emoji types with frequency < 5 will be collapsed into a single "Rare" category before modeling.
    *   **Regularization**: Lasso (L1) with **alpha selected via 5-fold cross-validation** (not fixed at 0.1) to optimize the bias-variance tradeoff for the specific dataset. This ensures model stability and valid coefficient estimates.
    *   **Effect Size**: Standardized Beta coefficients reported.
    *   **Causal Framing**: All claims framed as **associational** (observational design). No causal claims (randomization absent).
4.  **Power Analysis**:
    *   Pre-study power analysis to determine N required for Cohen's f² ≥ 0.02, power=0.80, α=0.05.
    *   Post-hoc check: If N is insufficient, flag "Power Limitation Warning" (Edge Case).

### Multiple Comparison & Error Control
*   **Family-Wise Error Rate (FWER)**: Controlled via Bonferroni correction. Adjusted p-value = p * k (where k = number of unique emoji types tested).
*   **Threshold**: Significance at adjusted p < 0.05.

### Measurement Validity
*   **Outcome**: `human_intensity_score` (1-7 Likert). Assumed valid proxy for perceived intensity based on literature (Assumption).
*   **Predictors**: Objective extraction of emoji from raw text. No circularity (Constitution Principle VII).
*   **Independence Check**: The independence of predictors (emoji) and outcomes (intensity) is contingent on the dataset's collection method (e.g., blind rating). If the dataset is not verified, this independence cannot be assumed, reinforcing the decision to halt if data is missing.

## Compute Feasibility

*   **Platform**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
*   **Method**:
    *   Data loading: `pandas` (CPU).
    *   Extraction: `regex` + `emoji` library (CPU).
    *   Analysis: `scipy`, `statsmodels`, `sklearn` (CPU).
*   **GPU Requirement**: None. The analysis relies on classical statistics and linear regression, which are computationally lightweight. No transformer fine-tuning or diffusion models are involved.
*   **Memory**: Streaming or chunked processing if dataset > 1GB (unlikely for text message corpora).
*   **Time**: Expected < 60 seconds for verification-only path; < 300 seconds for full analysis path.

## Decision Rationale

*   **CPU vs GPU**: CPU is sufficient. No deep learning models are required for the specified statistical tests.
*   **Dataset Selection**: The plan strictly adheres to the verified list. If the required `human_intensity_score` is absent, the pipeline halts. This prevents the fabrication of data or the use of invalid proxies, adhering to **Constitution Principle VI**. The "Data Unavailable" report is the valid scientific outcome.
*   **Regularization**: Lasso chosen over Ridge for `emoji_type` to perform feature selection. **Alpha is determined via cross-validation** to ensure optimal performance for the specific data distribution, addressing concerns about arbitrary parameter choice.
*   **Feature Collapsing**: Collapsing rare emoji types prevents overfitting in high-dimensional spaces when N is small, ensuring model stability.