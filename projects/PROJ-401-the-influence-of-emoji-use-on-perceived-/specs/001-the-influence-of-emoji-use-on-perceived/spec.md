# Feature Specification: The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Feature Branch**: `001-influence-of-emoji-on-intensity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does the frequency and type of emoji in digital text messages influence how emotionally intense recipients perceive those messages to be?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Verification (Priority: P1)

The system MUST load a public text message corpus and programmatically verify that the dataset contains three specific modalities: `text_content`, `emoji_presence` (or raw text to extract), and `human_intensity_score`. If any of these modalities are missing, the system MUST halt and generate a "Data Unavailable" report detailing the missing fields.

**Why this priority**: This is the foundational step; without a verified dataset containing human-rated intensity scores, the research question cannot be answered. This step ensures the data resource exists and meets the constitutional requirement for human-perception grounding before any analysis proceeds.

**Independent Test**: Can be fully tested by running the ingestion script on a candidate dataset (e.g., CMU Text Message Corpus) and verifying that the script either outputs a valid processed CSV with `intensity_score` column or a "Data Unavailable" report if the column is missing.

**Acceptance Scenarios**:

1. **Given** a raw text message containing "I love this!!! 😍🔥", **When** the extraction script processes it, **Then** the output record must show `emoji_present=True`, `emoji_count=2`, and `emoji_types=["U+1F60D", "U+1F525"]`.
2. **Given** a raw text message containing "I love this!!!", **When** the extraction script processes it, **Then** the output record must show `emoji_present=False`, `emoji_count=0`, and `emoji_types=[]`.
3. **Given** a dataset where [deferred] percentage of messages have encoding errors, **When** the script runs, **Then** it must log the errors and proceed with the remaining valid records, ensuring the final dataset is complete for valid records, provided the `human_intensity_score` column exists.
4. **Given** a dataset missing the `human_intensity_score` column, **When** the script runs, **Then** it must halt execution and output a "Data Unavailable" report listing the missing modality.

---

### User Story 2 - Human-Rated Data Loading (Priority: P2)

The system MUST prioritize loading datasets that already contain human-rated emotional intensity scores. If the dataset lacks this column, the system MUST NOT generate synthetic scores. Instead, it MUST halt and report that the study cannot proceed without human-rated data, in compliance with Constitution Principle VI.

**Why this priority**: The research question requires a dependent variable (perceived intensity) derived from human perception. Generating synthetic scores violates the project constitution. This step ensures the outcome variable is available and valid before analysis.

**Independent Test**: Can be tested by executing the loading module on a dataset with a `human_intensity_score` column and verifying that the output file contains this column with values between 1 and 7.

**Acceptance Scenarios**:

1. **Given** a dataset with a `human_intensity_score` column, **When** the loading module executes, **Then** it must produce a CSV with the `intensity_score` column preserved.
2. **Given** a dataset without a `human_intensity_score` column, **When** the loading module executes, **Then** it must halt and generate a "Data Unavailable" report.
3. **Given** a message with extreme emoji usage (e.g., 10+ emojis), **When** loaded, **Then** the `intensity_score` must be within the 1-7 range, ensuring no out-of-bounds values are produced.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST compute the statistical relationship between emoji metrics and intensity ratings using Pearson/Spearman correlation and linear regression. For models including 'EmojiType', the system MUST use Lasso Regression (L1 regularization) with alpha=0.1 to handle high dimensionality. The system MUST output effect sizes (Standardized Regression Coefficient / Beta) and visualizations.

**Why this priority**: This is the core scientific output. It answers the research question by quantifying the effect size and significance, while ensuring model stability through regularization.

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated dataset (N≥128) and verifying that the final report includes a correlation matrix, a regression coefficient table with p-values and standardized betas, and a plot image file, all computed within ≤ 300 seconds on a CPU.

**Acceptance Scenarios**:

1. **Given** a dataset with ≥ 128 messages and extracted emoji features, **When** the analysis script runs, **Then** it must output a correlation coefficient (r) and p-value for the relationship between `emoji_count` and `intensity_score`.
2. **Given** multiple hypothesis tests (e.g., testing correlation for all unique emoji types present in the dataset), **When** the script runs, **Then** it must apply Bonferroni correction and report adjusted p-values in the final table.
3. **Given** any tested association (significant or not), **When** the script calculates effect size, **Then** it must output the Standardized Regression Coefficient (Beta) and include a coefficient plot visualizing the regression results.

---

### Edge Cases

- What happens when the dataset contains messages with zero text length but emoji characters? (System must handle empty text strings gracefully without division-by-zero errors in feature extraction).
- How does the system handle messages with non-standard emoji sequences (e.g., skin tone modifiers) during type extraction? (System must normalize these to base Unicode points for consistent counting).
- What if the calculated sample size for the rating task (N determined by power analysis) is insufficient for the observed variance? (System must flag a power limitation warning in the final report rather than silently proceeding with an underpowered test).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract emoji presence (binary), frequency count (integer), and specific type (Unicode category) from every text message in the input dataset. (See US-1)
- **FR-001b**: System MUST verify the presence of `text_content`, `emoji_presence`, and `human_intensity_score` columns in the input dataset before ingestion. If any are missing, the system MUST halt and report "Data Unavailable". (See US-1)
- **FR-002**: System MUST load `human_intensity_score` from the input dataset for every message in the analysis set. The system MUST NOT generate synthetic scores. (See US-2)
- **FR-002c**: System MUST halt execution and generate a "Data Unavailable" report if the input dataset does not contain a `human_intensity_score` column. (See US-2)
- **FR-003**: System MUST compute Pearson or Spearman correlation coefficients between emoji frequency/type and intensity ratings. (See US-3)
- **FR-004**: System MUST perform linear regression analysis controlling for text length and punctuation to isolate the emoji effect, reporting the Standardized Regression Coefficient (Beta) as the effect size. (See US-3)
- **FR-004b**: System MUST use Lasso Regression (L1 regularization) with alpha=0.1 when 'EmojiType' is included as a predictor to prevent overfitting. (See US-3)
- **FR-005**: System MUST apply Bonferroni correction to p-values when testing multiple emoji types to control family-wise error rate. (See US-3)
- **FR-006**: System MUST perform a power analysis to determine the minimum sample size (N) required to detect a small-to-medium effect size (Cohen's f² ≥ 0.02) with 80% power at α=0.05 before finalizing the dataset, provided human-rated data is available. (See US-2)

### Key Entities

- **Message**: Represents a single text record; attributes include `text_content`, `emoji_presence`, `emoji_count`, `emoji_types`, and `intensity_score`.
- **AnalysisResult**: Represents the output of the statistical test; attributes include `correlation_coefficient`, `p_value`, `adjusted_p_value`, `standardized_beta`, and `regression_coefficients`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between emoji frequency and intensity is measured against the null hypothesis of no association (r=0) to determine statistical significance. (See FR-003)
- **SC-002**: The adjusted p-values for multiple emoji-type comparisons are measured against the Bonferroni-corrected alpha threshold (0.05/k) to ensure type I error control. (See FR-005)
- **SC-003**: The effect size (Standardized Beta) for significant associations is measured against standard benchmarks (small=0.1, medium=0.3, large=0.5) to quantify practical significance. (See FR-004)
- **SC-004**: The reproducibility of the analysis is measured by re-running the pipeline on the same input data and verifying that the output statistics match exactly (bit-for-bit reproducibility). (See US-3)
- **SC-005**: The computational efficiency of the analysis is measured against a baseline of ≤ 300 seconds for a dataset of N=1000 messages to ensure feasibility. For N < 1000, the time limit scales linearly (≤ 0.3 seconds per message). (See US-3)

## Assumptions

- **Dataset Availability**: The project assumes a public dataset (e.g., CMU Text Message Corpus) exists that contains at least 128 text messages with `text_content`, `emoji`, and `human_intensity_score` columns. If no such dataset is found, the study halts.
- **Methodological Framing**: The study assumes an observational design; therefore, all findings will be framed as associational (correlation) rather than causal, as the dataset does not involve random assignment of emoji usage.
- **Compute Constraints**: The analysis assumes that standard statistical libraries (scipy, statsmodels, scikit-learn) running on a Multi-core CPU with ≥ 7 GB RAM are sufficient to process the dataset (N=128 to N=1000) without requiring GPU acceleration or large-model inference.
- **Threshold Justification**: The decision cutoff for statistical significance is fixed at p < 0.05 (adjusted for multiplicity), consistent with community standards in psychological research; no additional sensitivity analysis for this threshold is required as it is a standard convention.
- **Measurement Validity**: The project assumes that a 1-7 Likert scale for "emotional intensity" is a valid and standard proxy for the psychological construct of perceived intensity in this context, as supported by prior literature on emotion expression.