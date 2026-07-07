# Feature Specification: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

**Feature Branch**: `001-linguistic-cues-authenticity`  
**Created**: 2026-06-14  
**Status**: Draft  
**Input**: User description: "Do subtle variations in linguistic style—such as first-person pronoun frequency, hedging language, and emotional valence—predict human ratings of perceived authenticity in AI chatbot conversations?"

## User Scenarios & Testing

### User Story 1 - Extract Linguistic Features from Conversation Corpus (Priority: P1)

As a researcher, I need to automatically extract specific linguistic metrics (pronoun frequency, hedge count, emotional valence) from a raw text corpus of chatbot conversations so that I can quantify the "subtle cues" hypothesized to influence authenticity.

**Why this priority**: This is the foundational data preparation step. Without quantified predictors, no statistical analysis or correlation testing can occur. It is the prerequisite for all downstream research activities.

**Independent Test**: Can be fully tested by running the extraction script on a small, known sample of text (e.g., a limited set of sentences with manually verified counts) and verifying that the output CSV contains the exact expected counts for pronouns, hedges, and sentiment scores.

**Acceptance Scenarios**:

1. **Given** a raw JSONL file containing 100 chatbot responses, **When** the extraction script is executed with the defined feature list, **Then** the output CSV contains exactly 100 rows with columns for `first_person_count`, `hedge_count`, and `sentiment_score`.
2. **Given** a conversation turn containing the phrase "I believe this might be correct," **When** the script processes this turn using the 15-word hedge lexicon defined in FR-001, **Then** it correctly increments the `hedge_count` by 2 (for "believe" and "might"), `first_person_count` by 1, and assigns a neutral-to-positive `sentiment_score`. This scenario verifies the counting logic; the specific count of 2 is an example for this sentence based on the fixed lexicon.
3. **Given** an empty or malformed conversation entry, **When** the script processes it, **Then** it logs a warning and outputs a row with `NaN` or 0 for the metrics without crashing the pipeline.

---

### User Story 2 - Compute Correlations and Regression Models (Priority: P2)

As a researcher, I need to compute Pearson/Spearman correlations and run a multiple linear regression model (controlling for length and topic) to determine if the extracted linguistic features significantly predict authenticity ratings.

**Why this priority**: This addresses the core research question. It transforms raw data into statistical evidence, allowing us to accept or reject the hypothesis regarding the relationship between linguistic style and perceived authenticity. This step must also ensure statistical validity by controlling the family-wise error rate via multiple-comparison correction (Benjamini-Hochberg procedure) to prevent false positives across multiple tests. It must also account for non-linear relationships and multicollinearity.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic dataset with known correlations (e.g., a generated dataset where `hedge_count` has a known correlation with `authenticity_score`) and verifying the script outputs a correlation coefficient within a 5% tolerance of the known value.

**Acceptance Scenarios**:

1. **Given** a dataset of 200 conversations with pre-computed linguistic features and human authenticity ratings, **When** the analysis script is executed, **Then** it outputs a CSV containing correlation coefficients (r) and p-values for each predictor against the outcome variable.
2. **Given** the same dataset, **When** the multiple regression is run, **Then** the output includes the adjusted R², AIC, and regression coefficients with standard errors, controlling for conversation length and turn count.
3. **Given** a dataset where no significant relationship exists (null hypothesis is true), **When** the script runs, **Then** it correctly reports p-values > 0.05 for the primary predictors, avoiding false positives.
4. **Given** a dataset with multiple predictors, **When** the script runs, **Then** it applies the Benjamini-Hochberg correction to all p-values (from correlations and regression) and reports the adjusted p-values.
5. **Given** a dataset where predictors exhibit non-linear relationships with the outcome, **When** the script runs, **Then** it tests for and reports quadratic terms or interaction effects as defined in FR-009.

---

### User Story 3 - Visualize Results and Generate Report (Priority: P3)

As a researcher, I need to generate publication-quality scatter plots with regression lines and a summary report of the statistical findings so that I can interpret the strength of the relationships and present the results.

**Why this priority**: Visualization is essential for interpreting complex statistical interactions and communicating findings to the broader community. It is the final step in the research workflow before conclusion.

**Independent Test**: Can be fully tested by running the visualization script on a sample dataset and verifying that the generated PNG/SVG files contain the correct axis labels, legends, and regression trendlines corresponding to the input data.

**Acceptance Scenarios**:

1. **Given** the regression results from User Story 2, **When** the visualization script is executed, **Then** it generates a scatter plot for `hedge_count` vs. `authenticity_rating` with a fitted regression line and a 95% confidence interval shaded area.
2. **Given** the full model output, **When** the report generator is run, **Then** it produces a Markdown summary stating the adjusted R², the significance of each predictor (p < 0.05 or not), and the direction of the effect (positive/negative).
3. **Given** a scenario where the regression model fails to converge, **When** the script runs, **Then** it generates a placeholder image indicating "Model Convergence Failed" and logs the specific error code for debugging.

---

### Edge Cases

- What happens when the dataset contains zero variance in a predictor (e.g., every chatbot response uses exactly one first-person pronoun)? The system must detect zero variance and exclude that predictor from regression to avoid singular matrix errors.
- How does the system handle missing authenticity ratings for specific conversation turns? The system must perform listwise deletion or imputation (if specified) and report the final sample size used in the analysis.
- How does the system handle conversations with extremely high length (outliers) that might skew the correlation? The system must apply a robust statistical method (e.g., Spearman rank correlation) or cap the length variable at the 99th percentile to prevent outlier dominance.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract first-person pronoun counts, `hedge_count` (frequency of uncertainty markers), and emotional valence scores (mapped to output column `sentiment_score`) from raw text inputs. The system MUST use VADER Sentiment Analyzer for valence and a fixed lexicon of uncertainty markers for hedges: ["maybe", "perhaps", "possibly", "probably", "likely", "unlikely", "seem", "seems", "appear", "appears", "believe", "think", "guess", "suppose", "assume"]. (See US-1)
- **FR-002**: System MUST compute Pearson and Spearman correlation coefficients between each linguistic feature and the human-rated authenticity scores, reporting both the coefficient and the p-value. (See US-2)
- **FR-003**: System MUST execute a multiple linear regression model with authenticity as the dependent variable and linguistic features as independent variables, explicitly controlling for conversation length and turn count. Before running the regression, the system MUST calculate Variance Inflation Factors (VIF) for all predictors; if any VIF > 5, the system MUST exclude the collinear covariate or log a warning and proceed with caution. (See US-2)
- **FR-004**: System MUST apply the Benjamini-Hochberg procedure to all p-values generated by correlation tests (FR-002) and regression coefficient tests (FR-003) to control the false discovery rate. (See US-2)
- **FR-005**: System MUST generate visualizations including scatter plots with regression lines and confidence intervals for each significant predictor, and a bar chart of feature importance coefficients. (See US-3)
- **FR-006**: System MUST validate that all input datasets contain the required columns (text, authenticity_score) and raise a clear error if columns are missing or mismatched. (See US-1)
- **FR-007**: System MUST check if the dataset size is insufficient for reliable regression (N < 30) and issue a warning regarding statistical power, unless a valid power analysis (FR-011) confirms the sample size is adequate for the effect size of interest. (See US-2)
- **FR-008**: System MUST compute a normalized `hedge_ratio` (hedge_count / total_word_count) if a density metric is explicitly requested, distinct from the raw `hedge_count`. (See US-1)
- **FR-009**: System MUST test for non-linear relationships (e.g., quadratic terms for `hedge_count`) and context-dependent interactions (e.g., `hedge_count` × `sentiment_score`) to ensure the model captures potential non-monotonic effects on authenticity. (See US-2)
- **FR-010**: System MUST perform a pragmatic validation step on a sample of 50 annotated turns to verify the precision of the hedge lexicon (target precision ≥ 0.8) before full extraction; if precision < 0.8, the system MUST flag the dataset for manual review. (See US-1)
- **FR-011**: System MUST perform a power analysis (target power ≥ 0.8, α=0.05) to determine the required sample size for the annotated subset and ensure the study is not underpowered. (See US-2)

### Key Entities

- **Conversation**: Represents a single chatbot interaction turn or exchange. Key attributes include `text_content`, `conversation_id`, `turn_number`, and `topic_category`.
- **LinguisticMetrics**: Represents the quantitative features extracted from a conversation. Key attributes include `first_person_count`, `hedge_count`, `hedge_ratio`, `sentiment_score`, and `conversation_length`.
- **AuthenticityRating**: Represents the subjective human judgment of a conversation. Key attributes include `rating_value` (scale 1-5 or 1-7), `rater_id`, and `conversation_id`.
- **StatisticalResult**: Represents the output of the analysis. Key attributes include `correlation_coefficient`, `p_value`, `adjusted_p_value`, `adjusted_r_squared`, `regression_coefficients`, `vif_values`, and `significance_flag`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation analysis pipeline is measured against the theoretical expectation of statistical validity; specifically, the system must report p-values and effect sizes (Cohen's d or r) for all tested hypotheses. (See US-2)
- **SC-002**: The regression model's explanatory power is measured against the adjusted R² metric, indicating the proportion of variance in authenticity ratings explained by linguistic features after controlling for confounds. (See US-2)
- **SC-003**: The robustness of the findings is measured against the results of a sensitivity analysis where the hedge lexicon is swept by removing one word at a time from the core 15-word list (leave-one-out) and re-running the analysis to ensure stability of the significance results. (See US-2)
- **SC-004**: The computational feasibility is measured against the constraint of running on a CPU-only environment with ≤ 7 GB RAM and completing the full analysis (extraction + regression + visualization) within 6 hours, tested on a dataset of [deferred] conversation turns (approx. 500k tokens). (See US-1, US-2, US-3)
- **SC-005**: The methodological soundness is measured by the explicit documentation of whether the dataset contains all necessary variables (predictors, outcome, covariates) and the framing of results as associational rather than causal due to the observational nature of the data. (See US-2)

## Assumptions

- The public chatbot conversation datasets (e.g., `convai2`, `cornell-movie-dialogs`) contain sufficient text volume to extract meaningful linguistic features, and any missing authenticity ratings will be supplemented by a small-scale human annotation effort (sample size [deferred: determined by power analysis]) if existing benchmarks are unavailable.
- The "hedge" definition will rely on a standard, citable lexicon (the 15-word list defined in FR-001) rather than a learned model, to ensure interpretability and reproducibility on CPU.
- The relationship between linguistic features and authenticity is assumed to be linear or monotonic for the purpose of initial correlation and linear regression; non-linear interactions are tested via FR-009.
- The human authenticity ratings, if sourced from existing benchmarks, are assumed to be reliable and consistent; if new annotations are required, a standard inter-rater reliability check (e.g., Cohen's Kappa > 0.6) will be performed.
- The analysis will treat the dataset as observational; therefore, findings will be framed strictly as associations between linguistic style and perceived authenticity, with no causal claims regarding the effect of changing linguistic style on authenticity.
- The computational resources (2 CPU cores, 7 GB RAM) are sufficient for processing the dataset size (estimated < 100k tokens) and running standard statistical libraries (scikit-learn, statsmodels) without GPU acceleration.
- The sample size for the study is determined by the annotation budget and power analysis (FR-011), not by the volume of available public dataset text.