# Feature Specification: The Influence of Emoji Use on Perceived Emotional Intensity in Text

**Feature Branch**: `001-influence-of-emoji-on-intensity`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Does the frequency and type of emoji in digital text messages influence how emotionally intense recipients perceive those messages to be?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Emoji Feature Extraction (Priority: P1)

The system MUST load a public text message corpus (e.g., CMU Text Message Corpus or OpenML equivalent) and programmatically extract objective emoji metrics (presence, frequency count, and specific type) for every message record.

**Why this priority**: This is the foundational step; without quantified predictor variables (emoji metrics) linked to the dataset, no analysis of their relationship with emotional intensity can occur. It establishes the independent variables for the entire study.

**Independent Test**: Can be fully tested by running the extraction script on a sample of 100 messages and verifying that the output CSV contains columns for `message_id`, `emoji_present` (boolean), `emoji_count` (integer), and `emoji_types` (list of strings), with no missing values for non-null messages.

**Acceptance Scenarios**:

1. **Given** a raw text message containing "I love this!!! 😍🔥", **When** the extraction script processes it, **Then** the output record must show `emoji_present=True`, `emoji_count=2`, and `emoji_types=["U+1F60D", "U+1F525"]`.
2. **Given** a raw text message containing "I love this!!!", **When** the extraction script processes it, **Then** the output record must show `emoji_present=False`, `emoji_count=0`, and `emoji_types=[]`.
3. **Given** a dataset where [deferred] of messages have encoding errors, **When** the script runs, **Then** it must log the errors and proceed with the remaining [deferred] without crashing, ensuring the final dataset is complete for valid records.

---

### User Story 2 - Emotional Intensity Rating Generation (Priority: P2)

If the source dataset lacks human-rated emotional intensity scores, the system MUST implement a local simulation or batch-processing task to generate these ratings for a sample of N=200 messages using a 1-7 Likert scale, simulating the output of a crowdsourced rater panel.

**Why this priority**: The research question requires a dependent variable (perceived intensity). If the chosen public dataset does not include this, the study cannot proceed without generating it. This step ensures the outcome variable is available for correlation analysis.

**Independent Test**: Can be tested by executing the rating generation module on a subset of 50 messages and verifying that the output file contains a `intensity_score` column where every value is an integer between 1 and 7, inclusive.

**Acceptance Scenarios**:

1. **Given** a list of 50 unique text messages, **When** the rating module executes, **Then** it must produce a CSV with 50 rows, each containing a `message_id` and an `intensity_score` (1-7).
2. **Given** the requirement for methodological consistency, **When** the rating module simulates rater variability, **Then** the distribution of scores must show variance (standard deviation > 0.5) to reflect human perception differences, rather than assigning a constant score to all inputs.
3. **Given** a message with extreme emoji usage (e.g., 10+ emojis), **When** rated, **Then** the generated score must be within the 1-7 range, ensuring no out-of-bounds values are produced.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST compute the statistical relationship between emoji metrics and intensity ratings using Pearson/Spearman correlation and linear regression, applying Bonferroni correction for multiple comparisons, and outputting effect sizes (Cohen's d) and visualizations.

**Why this priority**: This is the core scientific output. It answers the research question by quantifying the effect size and significance, adhering to the methodological constraints of the project (CPU-only, free tier).

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated dataset and verifying that the final report includes a correlation matrix, a regression coefficient table with p-values, and a plot image file, all computed within 60 seconds on a CPU.

**Acceptance Scenarios**:

1. **Given** a dataset with 200 messages and extracted emoji features, **When** the analysis script runs, **Then** it must output a correlation coefficient (r) and p-value for the relationship between `emoji_count` and `intensity_score`.
2. **Given** multiple hypothesis tests (e.g., testing correlation for 10 different emoji types), **When** the script runs, **Then** it must apply Bonferroni correction and report adjusted p-values in the final table.
3. **Given** a significant correlation found (p < 0.05), **When** the script calculates effect size, **Then** it must output Cohen's d value and include a coefficient plot visualizing the regression results.

---

### Edge Cases

- What happens when the dataset contains messages with zero text length but emoji characters? (System must handle empty text strings gracefully without division-by-zero errors in feature extraction).
- How does the system handle messages with non-standard emoji sequences (e.g., skin tone modifiers) during type extraction? (System must normalize these to base Unicode points for consistent counting).
- What if the calculated sample size for the rating task (N=200) is insufficient for the observed variance? (System must flag a power limitation warning in the final report rather than silently proceeding with an underpowered test).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract emoji presence (binary), frequency count (integer), and specific type (Unicode category) from every text message in the input dataset. (See US-1)
- **FR-002**: System MUST generate or retrieve human-rated emotional intensity scores on a 1-7 Likert scale for every message in the analysis set. (See US-2)
- **FR-003**: System MUST compute Pearson or Spearman correlation coefficients between emoji frequency/type and intensity ratings. (See US-3)
- **FR-004**: System MUST perform linear regression analysis controlling for text length and punctuation to isolate the emoji effect. (See US-3)
- **FR-005**: System MUST apply Bonferroni correction to p-values when testing multiple emoji types to control family-wise error rate. (See US-3)

### Key Entities

- **Message**: Represents a single text record; attributes include `text_content`, `emoji_presence`, `emoji_count`, `emoji_types`, and `intensity_score`.
- **AnalysisResult**: Represents the output of the statistical test; attributes include `correlation_coefficient`, `p_value`, `adjusted_p_value`, `effect_size`, and `regression_coefficients`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between emoji frequency and intensity is measured against the null hypothesis of no association (r=0) to determine statistical significance. (See FR-003)
- **SC-002**: The adjusted p-values for multiple emoji-type comparisons are measured against the Bonferroni-corrected alpha threshold (0.05/k) to ensure type I error control. (See FR-005)
- **SC-003**: The effect size (Cohen's d) for significant associations is measured against standard benchmarks (small=0.2, medium=0.5, large=0.8) to quantify practical significance. (See FR-004)
- **SC-004**: The total compute time for the full analysis pipeline is measured against the 6-hour limit of the free-tier GitHub Actions runner to ensure feasibility. (See US-3)
- **SC-005**: The memory usage of the analysis script is measured against the 7 GB RAM limit of the runner to ensure no out-of-memory crashes occur. (See US-3)

## Assumptions

- **Dataset Availability**: The project assumes a public dataset (e.g., CMU Text Message Corpus) exists that contains at least 200 text messages with sufficient variation in emoji usage, or that a synthetic rating task can be reliably simulated for N=200 messages.
- **Methodological Framing**: The study assumes an observational design; therefore, all findings will be framed as associational (correlation) rather than causal, as the dataset does not involve random assignment of emoji usage.
- **Compute Constraints**: The analysis assumes that standard statistical libraries (scipy, statsmodels, scikit-learn) running on a 2-core CPU with ~7 GB RAM are sufficient to process the dataset (N=200 to N=1000) without requiring GPU acceleration or large-model inference.
- **Threshold Justification**: The decision cutoff for statistical significance is fixed at p < 0.05 (adjusted for multiplicity), consistent with community standards in psychological research; no additional sensitivity analysis for this threshold is required as it is a standard convention.
- **Measurement Validity**: The project assumes that a 1-7 Likert scale for "emotional intensity" is a valid and standard proxy for the psychological construct of perceived intensity in this context, as supported by prior literature on emotion expression.
