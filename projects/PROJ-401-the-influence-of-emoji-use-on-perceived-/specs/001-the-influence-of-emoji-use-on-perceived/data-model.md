# Data Model: The Influence of Emoji Use on Perceived Emotional Intensity in Text

## Overview

This document defines the data structures, schemas, and transformation logic used in the project. It ensures that the data flow from raw ingestion to final statistical output is type-safe and reproducible. The model explicitly handles the "Data Unavailable" state as a valid terminal condition.

## Entities

### 1. PipelineState
Represents the current state of the pipeline execution.
*   **status**: String. Enum: `running`, `data_unavailable`, `analysis_complete`.
*   **data_available**: Boolean. True if `human_intensity_score` was found.
*   **missing_fields**: List[String]. List of required fields not found in the dataset (if `data_available` is false).
*   **timestamp**: String. ISO 8601 timestamp of the state change.

### 2. DataUnavailableReport
Represents the output when the required data is missing.
*   **report_type**: String. Fixed: "Data Unavailable".
*   **dataset_source**: String. The name of the dataset checked.
*   **missing_modality**: String. e.g., "human_intensity_score".
*   **recommendation**: String. e.g., "Study cannot proceed without human-rated data."
*   **timestamp**: String. ISO 8601 timestamp.

### 3. Message (Conditional)
Represents a single text record. **Only instantiated if `data_available` is true.**
*   **text_content**: String. The raw message text.
*   **emoji_presence**: Boolean. True if at least one emoji is detected.
*   **emoji_count**: Integer. Total number of emojis in the message.
*   **emoji_types**: List[String]. List of unique Unicode code points (normalized) for emojis present.
*   **intensity_score**: Float/Integer (1-7). Human-rated emotional intensity.
*   **text_length**: Integer. Character count of `text_content`.
*   **punctuation_count**: Integer. Count of punctuation marks (e.g., !, ?, ...).

### 4. AnalysisResult
Represents the output of a statistical test. **Only instantiated if `data_available` is true.**
*   **test_type**: String. e.g., "pearson_correlation", "lasso_regression".
*   **predictor**: String. e.g., "emoji_count", "U+1F60D".
*   **coefficient**: Float. Correlation coefficient (r) or Regression Beta.
*   **p_value**: Float. Raw p-value.
*   **adjusted_p_value**: Float. Bonferroni-corrected p-value.
*   **standardized_beta**: Float. Standardized effect size (for regression).
*   **significance**: Boolean. True if adjusted p < 0.05.

### 5. PowerAnalysisResult
*   **effect_size**: Float. Target Cohen's f².
*   **power**: Float. Target power (0.80).
*   **alpha**: Float. Significance level (0.05).
*   **required_n**: Integer. Minimum sample size.
*   **actual_n**: Integer. Sample size of the loaded dataset.
*   **status**: String. "Sufficient", "Insufficient", "Unknown".

## Transformation Pipeline

1.  **Ingestion**:
    *   Input: Raw Hugging Face dataset (Parquet/CSV).
    *   Validation: Check for `text_content` and `human_intensity_score`.
    *   Output: `PipelineState` (either `data_unavailable` or `running`).
2.  **Extraction** (Conditional):
    *   Input: `text_content` (only if `data_available` is true).
    *   Logic: Regex for emoji detection; Unicode normalization (NFC) to handle skin tone modifiers.
    *   Output: `Message` records (with `intensity_score` mapped).
3.  **Analysis** (Conditional):
    *   Input: List of `Message` records.
    *   Logic: Compute statistics, power analysis, regression.
    *   Output: `AnalysisResult` and `PowerAnalysisResult` records.
4.  **Reporting**:
    *   Input: `PipelineState`, `AnalysisResult`, `PowerAnalysisResult`.
    *   Logic: Generate final JSON/Markdown reports.
    *   Output: `DataUnavailableReport` (if failed) or `AnalysisReport` (if successful).

## Data Hygiene Rules

*   **Checksums**: All raw input files checksummed (SHA-256) upon download.
*   **Immutability**: Raw data never modified. Derived data written to new files (e.g., `data/processed/messages_extracted_v1.parquet`).
*   **PII**: No PII fields are expected in the verified datasets, but if present, they will be excluded or hashed.
*   **State Persistence**: The `PipelineState` is saved to `results/pipeline_state.json` after every phase to ensure reproducibility and clear termination status.