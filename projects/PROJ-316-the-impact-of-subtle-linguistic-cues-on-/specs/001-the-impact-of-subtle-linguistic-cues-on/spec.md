# Feature Specification: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

**Feature Branch**: `001-impact-of-subtle-linguistic-cues`  
**Created**: 2026-06-14  
**Status**: Draft  
**Input**: User description: "Do subtle variations in linguistic style—such as first-person pronoun frequency, hedging language, and emotional valence—predict human ratings of perceived authenticity in AI chatbot conversations?"

## User Scenarios & Testing

### User Story 1 - Automated Linguistic Feature Extraction (Priority: P1)

The system must ingest raw conversation text and automatically extract quantitative metrics for first-person pronoun frequency, hedge density, and emotional valence scores using standard NLP libraries.

**Why this priority**: This is the foundational data engineering step. Without accurate, reproducible extraction of the independent variables (linguistic features), no statistical analysis or correlation with human ratings can occur. It is the prerequisite for all downstream research.

**Independent Test**: A researcher can run the extraction script on a provided JSONL file of dummy conversations and receive a CSV output with exactly 3 new columns (pronoun_rate, hedge_density, valence_score) populated with numeric values, verified by spot-checking against manual counts.

**Acceptance Scenarios**:

1. **Given** a JSONL file containing 10 chatbot responses, **When** the extraction script is executed, **Then** the output CSV contains rows where `pronoun_rate` is calculated as (count of first-person pronouns / total word count) and matches manual verification within a 1% tolerance.
2. **Given** a conversation containing specific hedge words ("maybe", "perhaps", "possibly"), **When** the script processes the text, **Then** the `hedge_density` metric correctly identifies and counts these tokens using the predefined lexicon.
3. **Given** a conversation with mixed emotional content, **When** the script applies the VADER sentiment analyzer, **Then** the `valence_score` reflects the aggregate polarity (-1.0 to 1.0) as documented in the VADER methodology.

---

### User Story 2 - Associational Correlation Analysis (Priority: P2)

The system must compute Pearson and Spearman correlation coefficients between the extracted linguistic features and human authenticity ratings, framing results strictly as associational.

**Why this priority**: This addresses the core research question. It transforms raw data into statistical evidence regarding the relationship between style and perception. It is distinct from the extraction phase and can be tested independently once data exists.

**Independent Test**: A researcher can run the analysis module on the extracted CSV and a corresponding ratings file (CSV with columns `conversation_id` and `authenticity_score`), generating a correlation matrix and a scatter plot for any selected feature, with p-values and effect sizes clearly labeled.

**Acceptance Scenarios**:

1. **Given** a dataset of 200 conversations with both linguistic features and human authenticity ratings (provided as a CSV with `conversation_id` and `authenticity_score`), **When** the correlation analysis is run, **Then** the output includes a Pearson correlation coefficient and a p-value for the relationship between `hedge_density` and `authenticity_score`.
2. **Given** non-normally distributed rating data, **When** the analysis is configured to use Spearman’s rank correlation, **Then** the system outputs the rank-based coefficient instead of Pearson’s.
3. **Given** the results of the analysis, **When** the report is generated, **Then** all claims of "relationship" are explicitly labeled as "associated with", avoiding causal language (e.g., "predicts" or "causes" are strictly forbidden in the output).

---

### User Story 3 - Multivariate Regression with Controls (Priority: P3)

The system must fit a multiple linear regression model predicting authenticity ratings from linguistic features while controlling for conversation length and turn count, reporting adjusted R² and AIC.

**Why this priority**: This refines the initial correlation by isolating the unique contribution of linguistic style, controlling for confounding variables like message length. It provides a more robust test of the hypothesis but relies on the data prepared in US-1 and the initial correlations from US-2.

**Independent Test**: A researcher can execute the regression script and receive a summary table showing coefficients, standard errors, and p-values for each linguistic predictor, alongside the model's adjusted R².

**Acceptance Scenarios**:

1. **Given** the feature matrix and outcome vector, **When** the regression model is fitted, **Then** the output includes the coefficient for `pronoun_rate` with a standard error, allowing the researcher to assess significance.
2. **Given** a model with 3 linguistic predictors and 2 control variables, **When** the model is evaluated, **Then** the `adjusted_R_squared` is calculated and reported to account for the number of predictors.
3. **Given** the fitted model, **When** the diagnostic check is run, **Then** a Variance Inflation Factor (VIF) report is generated for all predictors to detect multicollinearity, flagging any VIF > 5.

---

### Edge Cases

- **What happens when the dataset contains empty or extremely short responses?** The system must handle zero-word counts by skipping the calculation for that specific row or assigning a NaN value, rather than crashing with a division-by-zero error.
- **How does the system handle missing human ratings?** If a conversation lacks a corresponding authenticity rating, the system must exclude that row from the correlation and regression analyses, logging the count of excluded samples.
- **What if the linguistic feature distribution is heavily skewed?** The system must detect extreme skewness (e.g., via a Shapiro-Wilk test or visual histogram) and flag the data in the report, suggesting log-transformation or non-parametric alternatives in the output notes.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract first-person pronoun frequency, hedge density, and emotional valence from input text using `spaCy` (model: `en_core_web_sm` v3.5), `NLTK` (v3.8), and `VADER` (v3.3.2), ensuring all variables are normalized per word count. (See US-1)
- **FR-002**: System MUST compute both Pearson and Spearman correlation coefficients between each linguistic feature and the authenticity rating variable. (See US-2)
- **FR-003**: System MUST fit a multiple linear regression model with authenticity as the dependent variable, linguistic features (normalized as density) as independent variables, and conversation length/turn count as covariates, explicitly handling collinearity between text length and feature density. (See US-3)
- **FR-004**: System MUST explicitly frame all statistical findings as associational. The generated report MUST include the exact disclaimer string: "These results indicate association, not causation." (See US-2)
- **FR-005**: System MUST calculate and report Variance Inflation Factors (VIF) for all predictors in the regression model to detect and report multicollinearity. (See US-3)
- **FR-006**: System MUST handle empty or extremely short responses (< 5 words) by skipping metric calculation for that row and logging the exclusion, preventing division-by-zero errors. (See US-1)
- **FR-007**: System MUST exclude rows with missing human ratings from correlation and regression analyses and log the count of excluded samples. (See US-2)
- **FR-008**: System MUST detect extreme skewness in linguistic feature distributions (e.g., via Shapiro-Wilk p < 0.05) and flag the data in the report with suggested transformations. (See US-1)
- **FR-009**: System MUST operationalize "authenticity" via a defined Likert scale (e.g., 1-5) if human annotation is used, requiring inter-rater reliability (Krippendorff's alpha ≥ 0.7) before analysis; synthetic ratings from the same model are strictly forbidden. (See US-2)
- **FR-010**: System MUST test for non-linearity (e.g., via quadratic terms or splines) in the relationship between linguistic features and authenticity before committing to a linear regression model. (See US-3)

### Key Entities

- **ConversationRecord**: Represents a single chatbot interaction, containing raw text, conversation ID, and metadata (length, turn count).
- **LinguisticMetrics**: A derived entity containing the quantitative scores (pronoun_rate, hedge_density, valence_score) linked to a ConversationRecord.
- **HumanRating**: The subjective authenticity score (e.g., 1-5 Likert scale) assigned to a ConversationRecord by a human annotator.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between linguistic features and authenticity ratings is measured against the null hypothesis of zero correlation (p < 0.05) using the extracted dataset. (See US-2)
- **SC-002**: The explanatory power of the multivariate model is measured against the adjusted R² threshold, with the model deemed successful if it explains a statistically significant proportion of variance (p < 0.05) AND adjusted R² ≥ 0.10. (See US-3)
- **SC-003**: The validity of the predictor set is measured against the Variance Inflation Factor (VIF) diagnostic, requiring all VIF values to be < 5 to confirm no severe multicollinearity. (See US-3)
- **SC-004**: The methodological robustness is measured against the requirement for multiple-comparison correction using the Benjamini-Hochberg procedure with alpha = 0.05 applied to the family of correlation tests. (See US-2)
- **SC-005**: The computational feasibility is measured against the constraint of completing the full analysis pipeline (extraction + correlation + regression) within 6 hours on a CPU-only GitHub Actions runner with ≤7 GB RAM, specifically applied to the sampled dataset (≤10,000 conversations) defined in Assumptions. (See US-1)
- **SC-006**: The validity of the outcome variable is measured against the requirement for inter-rater reliability (Krippendorff's alpha ≥ 0.7) if human annotation is performed. (See US-2)

## Assumptions

- The public chatbot conversation datasets (e.g., `facebook/convai2`, `Salesforce/cornell-movie-dialogs`) contain sufficient textual content to allow for meaningful extraction of the specified linguistic features (pronouns, hedges, emotion).
- Human-rated authenticity scores are available from a companion dataset or can be generated via a separate annotation process; the analysis assumes these ratings are independent of the linguistic feature extraction process.
- The "hedging" lexicon used is based on a standard, community-accepted list (e.g., words like "maybe", "perhaps", "possibly") and does not require custom training or fine-tuning.
- The analysis assumes that the relationship between linguistic style and authenticity is linear or monotonic, justifying the use of Pearson/Spearman correlations and linear regression, subject to the non-linearity test in FR-010.
- The dataset size will be constrained to fit within the 7 GB RAM limit of the free-tier GitHub Actions runner; if the source dataset is larger, a random sample of ≤10,000 conversations will be used.
- The study design is observational; therefore, all results will be interpreted as associational, and no causal claims regarding the effect of linguistic style on authenticity will be made.
- The "authenticity" construct is operationalized as a single scalar score provided by the dataset; no multi-dimensional subscale analysis is assumed.
- The 6-hour runtime constraint (SC-005) is justified by the project's requirement for reproducible research within standard CI/CD free-tier limits, ensuring the pipeline can be validated without expensive cloud resources.