# Feature Specification: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

**Feature Branch**: `001-simulated-social-comparison`  
**Created**: 2026-09-06  
**Status**: Draft  
**Input**: User description: "Investigate how specific features of idealized self-presentation (authenticity cues, engagement metrics) moderate the relationship between exposure and self-evaluation outcomes in online environments, and how these moderation effects vary across demographic subgroups."

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

The system MUST ingest public Reddit comment datasets, preprocess them to remove PII, and extract specific "idealized self-presentation" features (authenticity cues, engagement proxies, curated aesthetics) and self-evaluation scores (sentiment, self-reference) for every user corpus.

**Why this priority**: Without accurate extraction of the predictor variables (content features) and outcome variables (self-evaluation), no statistical analysis can occur. This is the foundational data layer.

**Independent Test**: A researcher can run the ingestion pipeline on a sample dataset and verify that the output CSV contains valid columns for `authenticity_score`, `engagement_proxy`, `curated_aesthetic_score`, and `self_eval_score` for at least 1,000 unique users.

**Acceptance Scenarios**:

1. **Given** a raw Reddit JSON dataset from Pushshift, **When** the ingestion script processes it, **Then** the output file contains exactly one row per unique user with aggregated feature scores and no rows containing personally identifiable information (PII).
2. **Given** a user corpus containing text with vulnerability markers (e.g., "I'm struggling," "feeling low"), **When** the feature extractor runs, **Then** the `authenticity_score` for that user is calculated and populated in the dataset.
3. **Given** a user corpus with high self-reference frequency (e.g., "I", "me", "my" counts), **When** the self-evaluation module runs, **Then** the `self_eval_score` reflects the sentiment-adjusted self-reference intensity.

---

### User Story 2 - Moderation Analysis Execution (Priority: P2)

The system MUST perform hierarchical multiple regression analysis to test for moderation effects, specifically modeling the interaction between exposure levels and specific idealized features on self-evaluation outcomes.

**Why this priority**: This is the core research engine. It transforms the extracted data into the primary scientific finding (the moderation effect).

**Independent Test**: A researcher can execute the analysis module on the processed dataset and receive a results file containing regression coefficients, p-values, and interaction terms for at least three distinct models (Exposure only, Exposure + Features, Exposure + Interaction).

**Acceptance Scenarios**:

1. **Given** a dataset with `exposure_level`, `authenticity_score`, and `self_eval_score`, **When** the regression module runs Model 3 (Interaction), **Then** the output includes a statistically significant interaction term coefficient (if present) with a p-value < 0.05.
2. **Given** multiple hypotheses being tested simultaneously, **When** the analysis completes, **Then** the results file includes a corrected p-value (e.g., Bonferroni or FDR) to account for multiple comparisons.
3. **Given** a dataset where the predictor variables are highly correlated, **When** the collinearity check runs, **Then** the output reports the Variance Inflation Factor (VIF) for each predictor to flag potential multicollinearity issues.

---

### User Story 3 - Demographic Stratification and Visualization (Priority: P3)

The system MUST stratify the analysis results by available demographic proxies (e.g., age-related keywords, gender markers) and generate visualizations (interaction plots, correlation matrices) to illustrate how moderation effects vary across subgroups.

**Why this priority**: This adds the necessary granularity to answer the "how do these vary" part of the research question, providing actionable insights for specific user groups.

**Independent Test**: A researcher can run the stratification script and generate a PDF report containing at least three distinct interaction plots showing the relationship between exposure and self-evaluation for different demographic subgroups.

**Acceptance Scenarios**:

1. **Given** a dataset with demographic proxy markers, **When** the stratification script runs, **Then** separate regression models are computed for each identified subgroup (e.g., "younger cohort" vs. "older cohort").
2. **Given** the results of the subgroup analysis, **When** the visualization module runs, **Then** the output includes a matplotlib/seaborn plot showing distinct slopes for the interaction term across at least two demographic groups.
3. **Given** a null result in a specific subgroup, **When** the report is generated, **Then** the visualization clearly indicates the lack of significant moderation effect for that specific group.

---

### Edge Cases

- **What happens when** the dataset lacks sufficient demographic markers? The system MUST default to a global analysis and flag the inability to perform stratification in the final report.
- **How does the system handle** a dataset where the "idealized feature" scores are near-zero (no variation)? The regression module MUST detect low variance and skip the interaction test for that specific feature to prevent division-by-zero or singular matrix errors.
- **What happens when** the RAM usage approaches the 7 GB limit during preprocessing? The system MUST stream data or sample the dataset to a size that fits within 6 GB RAM to prevent OOM crashes on the free-tier runner.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract "authenticity cues" from text using a rule-based classifier or pre-trained BERT embeddings (without fine-tuning) to identify vulnerability markers. (See US-1)
- **FR-002**: System MUST calculate a continuous "self-evaluation score" for each user based on sentiment analysis and self-reference frequency (e.g., ratio of first-person pronouns). (See US-1)
- **FR-003**: System MUST perform hierarchical multiple regression analysis including an interaction term between exposure levels and specific idealized features. (See US-2)
- **FR-004**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to all hypothesis test p-values generated in the analysis. (See US-2)
- **FR-005**: System MUST compute and report Variance Inflation Factors (VIF) for all predictors to diagnose collinearity before finalizing regression results. (See US-2)
- **FR-006**: System MUST stratify the dataset by demographic proxies (e.g., age/gender keywords) and run separate regression models for each identified subgroup. (See US-3)
- **FR-007**: System MUST generate interaction plots visualizing the moderation effect for at least two distinct demographic subgroups. (See US-3)
- **FR-008**: System MUST operate entirely on CPU-only resources, utilizing pre-trained models in default precision and avoiding any GPU-dependent libraries or 8-bit quantization. (See US-1, US-2)

### Key Entities

- **UserCorpus**: Represents a single user's aggregated comment history. Key attributes: `user_id`, `self_eval_score`, `demographic_proxy`, `post_count`.
- **FeatureExtraction**: Represents the derived metrics for a specific user. Key attributes: `authenticity_score`, `engagement_proxy`, `curated_aesthetic_score`.
- **RegressionResult**: Represents the output of a statistical model. Key attributes: `model_id`, `coefficients`, `p_values`, `interaction_term_significance`, `vif_scores`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The "Dataset-variable fit" is measured against the requirement that every predictor (authenticity, engagement, aesthetics) and outcome (self-evaluation) variable is successfully extracted from the source Reddit data without missing data exceeding 10%. (See FR-001, FR-002)
- **SC-002**: The "Inference framing" is measured against the output log, which MUST explicitly label all reported effects as "associational" unless randomization is detected (which is not expected in this observational design). (See FR-003)
- **SC-003**: The "Multiplicity control" is measured against the results file, which MUST show that p-values for >1 hypothesis test have been adjusted using a standard correction method (e.g., FDR). (See FR-004)
- **SC-004**: The "Predictor collinearity" is measured against the VIF report, ensuring no predictor has a VIF > 5.0; if exceeded, the model must flag the limitation rather than claiming independent effects. (See FR-005)
- **SC-005**: The "Compute feasibility" is measured against the CI runner logs, confirming the entire analysis (ingestion to visualization) completes within 6 hours on a 2-core CPU without OOM errors. (See FR-008)
- **SC-006**: The "Threshold justification" is measured against the documentation, which MUST include a sensitivity analysis sweeping the self-reference or sentiment thresholds (e.g., ±0.05) and reporting the variation in headline rates. (See FR-002, FR-003)

## Assumptions

- **Assumption about data source**: The Pushshift Reddit dataset contains sufficient metadata (e.g., timestamp, subreddit, text) to infer "engagement proxies" (comment depth/threading) and "demographic proxies" (user bio keywords) without requiring external API calls.
- **Assumption about NLP validity**: Pre-trained BERT embeddings (without fine-tuning) and standard sentiment analysis tools (NLTK/spaCy) are sufficient proxies for "authenticity cues" and "self-evaluation" in this specific observational context, despite not being custom-trained on social media data.
- **Assumption about demographic proxies**: Demographic subgroups will be identified via keyword matching in user bios or self-referential text (e., "19M", "female"), acknowledging this is a noisy proxy rather than verified census data.
- **Assumption about computational limits**: The dataset size, after sampling to ensure RAM compliance, will be large enough (n > 500 per subgroup) to support hierarchical regression with interaction terms without statistical under-powering.
- **Assumption about threshold sensitivity**: A default sensitivity sweep of ±0.05 for the self-reference and sentiment thresholds will be sufficient to demonstrate robustness, as the CPU-trivial nature of this sweep allows for easy execution.
- **Assumption about causal framing**: Since the design is purely observational using public data, all findings will be framed as associational; no causal claims regarding "impact" will be made in the final output.
