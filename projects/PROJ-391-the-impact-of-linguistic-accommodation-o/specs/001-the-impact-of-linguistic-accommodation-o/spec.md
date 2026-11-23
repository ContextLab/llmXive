# Feature Specification: Linguistic Accommodation and Speaker Emotional Intensity in Human-Human Dialogue

**Feature Branch**: `001-linguistic-accommodation-empathy`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does linguistic accommodation in AI assistant responses influence users' perceptions of the AI's empathy and rapport?"  
**Note on Scope Pivot**: The original research question regarding "AI empathy" could not be addressed with the available public dataset (DailyDialog), which contains human-human dialogue. This specification pivots the study to "Linguistic Accommodation and Speaker Emotional Intensity in Human-Human Dialogue" using DailyDialog as a baseline model. The AI-specific study is moved to "Future Work".

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system MUST load public **human-human** dialogue datasets (specifically DailyDialog), extract human turns and corresponding partner turns, and compute raw linguistic metrics (lexical overlap, syntactic similarity, sentence length variance) for each pair.

**Why this priority**: This is the foundational data layer. Without computed accommodation metrics, no correlation analysis or emotional intensity assessment can occur. It represents the minimum viable data pipeline.

**Independent Test**: Can be fully tested by running the ingestion script on a sample of 100 dialogue pairs and verifying that a JSON/CSV output file is generated containing columns for `lexical_overlap`, `syntactic_similarity`, `sentence_length_variance`, and `conversation_id` with no null values in the metric columns.

**Acceptance Scenarios**:

1. **Given** a raw DailyDialog dataset file, **When** the ingestion script is executed, **Then** a processed dataset is generated with computed accommodation metrics for every turn in the sample.
2. **Given** a dialogue pair where a turn is empty or missing, **When** the script processes the pair, **Then** the record is either skipped or flagged with a `null` metric value, and the process continues without crashing.

---

### User Story 2 - Emotional Intensity Extraction and Mapping (Priority: P2)

The system MUST extract emotion labels from the dataset annotations and map them to a numeric **Speaker Emotional Intensity** score (1-5) for each dialogue turn, ensuring every accommodation metric has a paired intensity score. The system MUST apply a defined inference rule (emotion-to-intensity mapping: Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3).

**Why this priority**: This enables the core research question (correlation between accommodation and speaker emotion). It is the second critical step, transforming raw text metrics into a paired dataset ready for statistical testing.

**Independent Test**: Can be fully tested by verifying that the output dataset contains a `emotional_intensity` column paired with every `accommodation_score` row, and that the distribution of ratings matches the source dataset's documented range (e.g., 1-5 Likert scale) and the defined mapping rule. The system MUST also output a distribution report showing the frequency of each mapped score to verify the mapping logic.

**Acceptance Scenarios**:

1. **Given** a dataset with explicit emotion labels, **When** the mapping script runs, **Then** every dialogue turn is assigned the correct corresponding intensity score.
2. **Given** a dataset with missing or implicit emotion data, **When** the mapping script runs, **Then** the system applies the defined emotion-to-intensity mapping rule or excludes the record if no emotion label exists, and documents the exclusion rate in a summary report.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

The system MUST perform correlation analysis (Pearson/Spearman) between accommodation scores and emotional intensity ratings, run regression models controlling for conversation length and topic, and generate visualizations (scatter plots, effect size distributions) with bootstrap resampling (minimum 1000 iterations, continuing until 95% CI width ≤ 0.05 or a maximum of 5000 iterations is reached) for robustness.

**Why this priority**: This delivers the final research output (the answer to the research question). It relies on the data prepared in US-1 and US-2.

**Independent Test**: Can be fully tested by running the analysis script on the prepared dataset and verifying that a report is generated containing a correlation coefficient, p-value, and a scatter plot image, and that the bootstrap confidence intervals are calculated.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with accommodation and emotional intensity metrics, **When** the analysis script is executed, **Then** a statistical report is generated showing the correlation coefficient and significance level.
2. **Given** the analysis script, **When** executed, **Then** a scatter plot visualization is saved showing the relationship between accommodation scores and emotional intensity ratings, with a regression line and confidence interval shading.

---

### Edge Cases

- The system normalizes all non-ASCII characters and emojis to Unicode NFKC form before computing syntactic similarity.
- The system skips records where the turn or partner turn is empty or contains only non-text characters after normalization.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute lexical overlap (Jaccard similarity) between user turns and AI responses with a precision of at least 4 decimal places (See US-1).
- **FR-002**: The system MUST compute syntactic similarity based on Jaccard similarity of POS tag sets for every valid dialogue pair (See US-1).
- **FR-003**: The system MUST extract emotion labels from dataset metadata AND apply the defined emotion-to-intensity mapping rule (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) to generate a numeric `emotional_intensity` score for every record with a label, aligning them with the corresponding turn (See US-2).
- **FR-004**: The system MUST perform a Pearson correlation test and a Spearman rank correlation test between accommodation metrics and emotional intensity ratings (See US-3).
- **FR-005**: The system MUST generate a scatter plot visualization with a regression line and 95% confidence interval for the primary correlation analysis (See US-3).
- **FR-006**: The system MUST execute a bootstrap resampling procedure with a minimum of 1000 iterations, continuing until the confidence interval width for the correlation coefficient is ≤ 0.05 or a maximum of 5000 iterations is reached, whichever comes first (See US-3).
- **FR-007**: The system MUST control for conversation length (word count) and topic (dominant LDA cluster ID, k=10) as covariates in the regression model to isolate the effect of accommodation (See US-3).
- **FR-008**: The system MUST normalize all non-ASCII characters and emojis to Unicode NFKC form before computing metrics, and MUST skip records where the turn or partner turn is empty or contains only non-text characters after normalization (See US-1).
- **FR-009**: The system MUST perform a sensitivity analysis comparing the primary POS-based metrics against dependency-parse-based metrics to validate the construct validity of the accommodation proxy (See US-3).
- **FR-010**: The system MUST perform a validation step that includes: (a) a consistency check verifying the distribution of mapped `emotional_intensity` scores matches the expected distribution of the source emotion labels, and (b) a literature grounding step comparing the observed distribution to known distributions of emotion labels in similar corpora (See US-2).

### Key Entities

- **DialoguePair**: Represents a single interaction unit containing a `user_turn`, `partner_turn`, `conversation_id`, and `topic`.
- **AccommodationMetric**: Represents the computed values (lexical_overlap, syntactic_similarity, sentence_length_variance) for a specific `DialoguePair`.
- **EmotionalIntensity**: Represents the numeric score (1-5) derived from the source emotion label for a specific `DialoguePair`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between lexical overlap and emotional intensity ratings is measured against the null hypothesis of zero correlation (See US-3).
- **SC-002**: The stability of the correlation coefficient is measured against the 95% confidence interval derived from bootstrap iterations (See US-3).
- **SC-003**: The effect size of linguistic accommodation on emotional intensity is measured against the baseline effect size observed in human-human accommodation literature (r=0.15, Giles et al., 2003). The effect is considered significant if the 95% CI excludes 0 AND the lower bound of the 95% CI is greater than 0.10, OR if a one-sample t-test of the correlation coefficient against 0.15 yields p < 0.05 (See US-3).
- **SC-004**: The proportion of variance in emotional intensity ratings explained by accommodation metrics (R-squared) is measured against the total variance in the emotional intensity distribution (See US-3).
- **SC-005**: The false discovery rate for multiple hypothesis tests (Pearson and Spearman on lexical and syntactic metrics) is measured against a Bonferroni-corrected alpha threshold derived from the standard significance level divided by the number of comparisons. (See US-3).

## Assumptions

- **Assumption about data availability**: The DailyDialog dataset contains sufficient emotion labels to infer emotional intensity scores for at least 80% of the dialogue pairs using the defined mapping rule. We assume Speaker Emotion is a valid proxy for Rapport in this context, subject to validation via FR-010.
- **Assumption about compute constraints**: The entire analysis pipeline (data loading, metric computation, statistical testing, and visualization) will complete within 6 hours on a CPU-only GitHub Actions runner with 2 cores and 7 GB RAM.
- **Assumption about methodological framing**: The study is observational; therefore, all findings will be framed as associational (correlational) rather than causal, as no random assignment of linguistic styles was performed in the source data.
- **Assumption about metric validity**: Lexical overlap (Jaccard similarity) and POS tag overlap are valid proxies for "linguistic accommodation" in the context of human-human dialogue, consistent with prior psycholinguistic literature, subject to validation via FR-009.
- **Assumption about threshold justification**: The decision to use a Bonferroni correction for the four primary hypothesis tests (Pearson/Spearman on lexical/syntactic metrics) is based on standard community practices for controlling family-wise error rate in exploratory correlation studies.
- **Assumption about sensitivity analysis**: A sensitivity analysis will be conducted by comparing POS-based metrics against dependency-parse-based metrics to ensure the correlation results are robust to the specific granularity of text comparison.

## Future Work

- **AI-Specific Study**: The original research question regarding "AI empathy" requires a dataset containing AI responses and user-perceived empathy ratings. This study is planned for a future iteration when such a dataset becomes available.
- **Expanded Validation**: Future work will include a manual annotation study where human raters evaluate perceived empathy in AI responses to validate the proxy model used in this study.