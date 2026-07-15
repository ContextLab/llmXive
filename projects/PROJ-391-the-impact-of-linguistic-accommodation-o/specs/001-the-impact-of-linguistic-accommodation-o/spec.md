# Feature Specification: The Impact of Linguistic Accommodation on Perceived Empathy in AI Assistants

**Feature Branch**: `001-linguistic-accommodation-empathy`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does linguistic accommodation in AI assistant responses influence users' perceptions of the AI's empathy and rapport?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing (Priority: P1)

The system MUST load public human-AI dialogue datasets (specifically DailyDialog), extract AI assistant responses and corresponding user turns, and compute raw linguistic metrics (lexical overlap, syntactic similarity, sentence length variance) for each pair.

**Why this priority**: This is the foundational data layer. Without computed accommodation metrics, no correlation analysis or empathy assessment can occur. It represents the minimum viable data pipeline.

**Independent Test**: Can be fully tested by running the ingestion script on a sample of 100 dialogue pairs and verifying that a JSON/CSV output file is generated containing columns for `lexical_overlap`, `syntactic_similarity`, `sentence_length_variance`, and `conversation_id` with no null values in the metric columns.

**Acceptance Scenarios**:

1. **Given** a raw DailyDialog dataset file, **When** the ingestion script is executed, **Then** a processed dataset is generated with computed accommodation metrics for every AI response in the sample.
2. **Given** a dialogue pair where the AI response is empty or missing, **When** the script processes the pair, **Then** the record is either skipped or flagged with a `null` metric value, and the process continues without crashing.

---

### User Story 2 - Empathy Rating Extraction and Mapping (Priority: P2)

The system MUST extract or infer user empathy/helpfulness ratings from the dataset annotations or survey metadata and map them to the corresponding dialogue turns, ensuring each accommodation metric has a paired empathy score. The system MUST apply a defined inference rule (emotion-to-Likert mapping: Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) when explicit empathy ratings are missing.

**Why this priority**: This enables the core research question (correlation between accommodation and empathy). It is the second critical step, transforming raw text metrics into a paired dataset ready for statistical testing.

**Independent Test**: Can be fully tested by verifying that the output dataset contains a `empathy_rating` column paired with every `accommodation_score` row, and that the distribution of ratings matches the source dataset's documented range (e.g., 1-5 Likert scale) and the defined mapping rule.

**Acceptance Scenarios**:

1. **Given** a dataset with explicit empathy ratings, **When** the mapping script runs, **Then** every dialogue turn is assigned the correct corresponding empathy score.
2. **Given** a dataset with missing or implicit empathy data, **When** the mapping script runs, **Then** the system applies the defined emotion-to-Likert mapping rule (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) or excludes the record if no emotion label exists, and documents the exclusion rate in a summary report.

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

The system MUST perform correlation analysis (Pearson/Spearman) between accommodation scores and empathy ratings, run regression models controlling for conversation length and topic, and generate visualizations (scatter plots, effect size distributions) with bootstrap resampling (minimum 1000 iterations, continuing until 95% CI width < 0.01) for robustness.

**Why this priority**: This delivers the final research output (the answer to the research question). It relies on the data prepared in US-1 and US-2.

**Independent Test**: Can be fully tested by running the analysis script on the prepared dataset and verifying that a report is generated containing a correlation coefficient, p-value, and a scatter plot image, and that the bootstrap confidence intervals are calculated.

**Acceptance Scenarios**:

1. **Given** the prepared dataset with accommodation and empathy metrics, **When** the analysis script is executed, **Then** a statistical report is generated showing the correlation coefficient and significance level.
2. **Given** the analysis script, **When** executed, **Then** a scatter plot visualization is saved showing the relationship between accommodation scores and empathy ratings, with a regression line and confidence interval shading.

---

### Edge Cases

- **FR-008**: The system MUST normalize all non-ASCII characters and emojis to Unicode NFKC form before computing syntactic similarity.
- **FR-008**: The system MUST skip records where the AI response or user turn is empty or contains only non-text characters after normalization.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute lexical overlap (Jaccard similarity) between user turns and AI responses with a precision of at least 4 decimal places (See US-1).
- **FR-002**: The system MUST compute syntactic similarity based on Jaccard similarity of POS tag sets for every valid dialogue pair (See US-1).
- **FR-003**: The system MUST extract empathy ratings from dataset metadata OR apply the defined emotion-to-Likert mapping rule (Joy=5, Sadness=2, Anger=1, Fear=2, Surprise=4, Disgust=1, Neutral=3) and exclude records with no emotion label, aligning them with the corresponding AI response turn (See US-2).
- **FR-004**: The system MUST perform a Pearson correlation test and a Spearman rank correlation test between accommodation metrics and empathy ratings (See US-3).
- **FR-005**: The system MUST generate a scatter plot visualization with a regression line and 95% confidence interval for the primary correlation analysis (See US-3).
- **FR-006**: The system MUST execute a bootstrap resampling procedure with a minimum of 1000 iterations, continuing until the confidence interval width for the correlation coefficient is sufficiently narrow to ensure precise estimation (See US-3).
- **FR-007**: The system MUST control for conversation length (word count) and topic (dominant LDA cluster ID, k=10) as covariates in the regression model to isolate the effect of accommodation (See US-3).
- **FR-008**: The system MUST normalize all non-ASCII characters and emojis to Unicode NFKC form before computing metrics, and MUST skip records where the AI response or user turn is empty or contains only non-text characters after normalization (See US-1).
- **FR-009**: The system MUST perform a sensitivity analysis comparing the primary POS-based metrics against dependency-parse-based metrics to validate the construct validity of the accommodation proxy (See US-3).
- **FR-010**: The system MUST generate a manually annotated validation subset (n≥30) by sampling 30 random dialogue pairs and applying a human rating protocol (or using a pre-existing small set if available) to validate the inferred empathy scores against human judgments (See US-2).

### Key Entities

- **DialoguePair**: Represents a single interaction unit containing a `user_turn`, `ai_response`, `conversation_id`, and `topic`.
- **AccommodationMetric**: Represents the computed values (lexical_overlap, syntactic_similarity, sentence_length_variance) for a specific `DialoguePair`.
- **EmpathyRating**: Represents the user's subjective rating (numeric) associated with a specific `DialoguePair` or `ai_response`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient between lexical overlap and empathy ratings is measured against the null hypothesis of zero correlation (See US-3).
- **SC-002**: The stability of the correlation coefficient is measured against the 95% confidence interval derived from bootstrap iterations (See US-3).
- **SC-003**: The effect size of linguistic accommodation on empathy is measured against the baseline effect size observed in human-human accommodation literature (r=0.15, Giles et al., 2003) (See US-3).
- **SC-004**: The proportion of variance in empathy ratings explained by accommodation metrics (R-squared) is measured against the total variance in the empathy rating distribution (See US-3).
- **SC-005**: The false discovery rate for multiple hypothesis tests (Pearson and Spearman on lexical and syntactic metrics) is measured against a Bonferroni-corrected alpha threshold derived from the standard significance level divided by the number of comparisons. (See US-3).

## Assumptions

- **Assumption about data availability**: The DailyDialog dataset (or equivalent public dataset) contains sufficient emotion labels to infer empathy ratings for at least 80% of the dialogue pairs using the defined mapping rule.
- **Assumption about compute constraints**: The entire analysis pipeline (data loading, metric computation, statistical testing, and visualization) will complete within 6 hours on a CPU-only GitHub Actions runner with 2 cores and 7 GB RAM.
- **Assumption about methodological framing**: The study is observational; therefore, all findings will be framed as associational (correlational) rather than causal, as no random assignment of linguistic styles was performed in the source data.
- **Assumption about metric validity**: Lexical overlap (Jaccard similarity) and POS tag overlap are valid proxies for "linguistic accommodation" in the context of AI-human dialogue, consistent with prior psycholinguistic literature, subject to validation via FR-009.
- **Assumption about threshold justification**: The decision to use a Bonferroni correction for the four primary hypothesis tests (Pearson/Spearman on lexical/syntactic metrics) is based on standard community practices for controlling family-wise error rate in exploratory correlation studies.
- **Assumption about sensitivity analysis**: A sensitivity analysis will be conducted by comparing POS-based metrics against dependency-parse-based metrics to ensure the correlation results are robust to the specific granularity of text comparison.