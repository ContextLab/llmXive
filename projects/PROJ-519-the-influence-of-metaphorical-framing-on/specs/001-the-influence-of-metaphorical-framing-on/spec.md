# Feature Specification: The Influence of Metaphorical Framing on Attitudes Towards Mental Health Treatment

**Feature Branch**: `001-metaphor-framing-attitudes`  
**Created**: 2026-07-15  
**Status**: Draft  
**Input**: User description: "How does exposure to metaphorical framing of mental health conditions (e.g., "battle," "journey," "burden") influence public attitudes toward treatment-seeking behaviors and stigma, as measured through controlled vignette experiments and/or analysis of independent discourse sources?"

## User Scenarios & Testing

### User Story 1 - Experimental Vignette Exposure & Outcome Measurement (Priority: P1)

**Description**: A researcher recruits participants, presents them with one of three standardized vignettes (Battle, Journey, or Medical control) describing a person with depression, and immediately collects their stigma and help-seeking intent scores using the CAMI scale and a Likert scale.

**Why this priority**: This is the core causal mechanism of the study. Without the ability to expose participants to controlled stimuli and record standardized psychometric outcomes, the primary research question regarding the causal influence of framing cannot be answered.

**Independent Test**: The system can be tested by running a batch of simulated participants through the three conditions, verifying that the correct vignette text is displayed for the assigned condition and that the resulting CAMI/Likert scores are recorded correctly in the dataset without text leakage.

**Acceptance Scenarios**:

1. **Given** a participant is assigned to the "Battle" condition, **When** they view the vignette, **Then** the text must contain "fighting a war" metaphors but exclude "journey" or "medical" framing, and the system must record their CAMI score.
2. **Given** a participant is assigned to the "Journey" condition, **When** they view the vignette, **Then** the text must contain "long journey" metaphors but exclude "battle" framing, and the system must record their help-seeking intent score.
3. **Given** a participant is assigned to the "Medical/Control" condition, **When** they view the vignette, **Then** the text must describe the condition as an "illness" without metaphorical framing, and the system must record their baseline scores.

---

### User Story 2 - Independent Discourse Analysis & Sentiment Correlation (Priority: P2)

**Description**: A researcher downloads a corpus of public mental health posts (e.g., from r/mentalhealth and r/depression, or a static equivalent) collected within a recent multi-year period., filters them by metaphor keywords, calculates VADER sentiment scores, and models the relationship between metaphor frequency and sentiment while controlling for engagement metrics. This analysis is exploratory and correlational, not a validation of the stigma construct.

**Why this priority**: This provides an external view of how metaphor usage correlates with general sentiment in naturalistic discourse. While it cannot validate the specific psychological construct of stigma (which VADER does not measure), it offers ecological context for the experimental findings.

**Independent Test**: The system can be tested by processing a small, fixed sample of posts., verifying that posts containing "battle" are correctly identified, their VADER sentiment scores are computed, and a robust regression model (with Huber-White standard errors) can be fitted to show the relationship between metaphor count and sentiment.

**Acceptance Scenarios**:

1. **Given** a dataset of public posts from r/mentalhealth, r/depression, or a static corpus from the last 5 years, **When** the system filters for posts containing "battle," "journey," or "burden," **Then** it must extract the text and metadata (upvotes, comments) for regression analysis.
2. **Given** a filtered post, **When** the VADER sentiment analyzer runs, **Then** it must return a compound sentiment score (representing general polarity, not stigma) and the system must store this alongside the metaphor keyword count.
3. **Given** the processed dataset, **When** the robust linear regression model is executed, **Then** it must output the coefficient for metaphor frequency controlling for post length and engagement, using Huber-White standard errors to account for potential heteroscedasticity.

---

### User Story 3 - Statistical Inference & Visualization Generation (Priority: P3)

**Description**: A researcher runs a one-way ANOVA on the experimental data to test for significant differences across conditions, applies multiple-comparison corrections to post-hoc tests, and generates bar charts comparing mean stigma scores, as well as a scatter plot for the discourse analysis.

**Why this priority**: This transforms raw data into interpretable scientific results. It allows the researcher to answer the hypothesis (p<0.05) and visualize the findings for reporting, which is the final step in the research workflow.

**Independent Test**: The system can be tested by feeding it a pre-generated CSV of experimental scores, verifying that the ANOVA F-statistic and p-value are calculated correctly, that post-hoc tests apply Bonferroni correction, and that the resulting bar chart displays the three conditions with error bars.

**Acceptance Scenarios**:

1. **Given** the experimental dataset with condition labels and CAMI scores, **When** the one-way ANOVA is performed, **Then** the system must output the F-statistic and p-value, flagging significance if p < 0.05.
2. **Given** the discourse regression results, **When** the scatter plot is generated, **Then** it must display metaphor density on the X-axis and sentiment on the Y-axis with a fitted regression line.
3. **Given** a null result (p > 0.05), **When** the visualization is generated, **Then** the system must still render the chart correctly, allowing the researcher to report the lack of significant difference.

### Edge Cases

- **What happens when** the dataset size exceeds the available RAM (7GB) during the discourse analysis?
  - The system must implement chunked processing or sampling to ensure the analysis completes within the computational time limit.
- **How does the system handle** participants who fail attention checks or provide identical responses across all items?
  - The system must flag these records for exclusion prior to statistical analysis.
- **What happens when** the Pushshift API returns fewer than 10,000 posts or returns an error?
  - The system must log the error, attempt a retry (up to a defined maximum of 3), and proceed with the available data or a static fallback corpus while recording the reduced sample size in the assumptions.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate three distinct vignette texts (Battle, Journey, Medical) that differ *only* in metaphorical framing while keeping all clinical details constant (See US-1).
- **FR-002**: System MUST administer the Community Attitudes towards the Mentally Ill (CAMI) scale and a help-seeking intent Likert scale immediately after vignette exposure (See US-1).
- **FR-003**: System MUST acquire a public mental health discourse corpus (e.g., from r/mentalhealth and r/depression via API, or a static equivalent corpus) and filter for specific metaphor keywords using regex (See US-2).
- **FR-004**: System MUST compute general sentiment scores for discourse posts using VADER and store them alongside metaphor frequency counts, explicitly noting that this measures general polarity, not the psychological construct of stigma (See US-2).
- **FR-005**: System MUST perform a one-way ANOVA on experimental data to test for differences in mean scores across the three conditions (See US-3).
- **FR-006**: System MUST execute a robust linear regression on discourse data modeling sentiment as a function of metaphor frequency, controlling for post length and engagement, using Huber-White standard errors (See US-2).
- **FR-007**: System MUST generate visualizations (bar charts for ANOVA, scatter plots for regression) suitable for scientific reporting (See US-3).
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Bonferroni) to the three pairwise comparisons (Battle vs. Journey, Battle vs. Control, Journey vs. Control) following the ANOVA to control the family-wise error rate (See US-3).
- **FR-009**: System MUST perform a Variance Inflation Factor (VIF) check on regression predictors; if VIF ≥ 5, the system must flag multicollinearity and report robust standard errors (See US-2).

### Key Entities

- **Participant**: Represents an individual in the experimental study, containing attributes for assigned condition, CAMI scores, and help-seeking intent scores.
- **Vignette**: Represents the stimulus text, containing the specific metaphorical framing (Battle, Journey, Medical) and the underlying clinical narrative.
- **DiscoursePost**: Represents a unit of public text, containing the raw text, metadata (upvotes, comments), extracted metaphor keywords, and computed sentiment score.
- **StatisticalResult**: Represents the output of an analysis, containing the test statistic (F-value, t-value), p-value, effect size, and visualization data.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The experimental ANOVA must output a p-value and a boolean flag indicating significance at alpha=0.05 (See FR-005, US-3).
- **SC-002**: The discourse regression must output a p-value < 0.05 for the metaphor frequency coefficient, using Huber-White standard errors, and report a VIF < 5 for all predictors (See FR-006, FR-009, US-2).
- **SC-003**: The system must output the specific adjusted alpha threshold (e.g., 0.0167) for the post-hoc comparisons and flag results as significant only if p < adjusted_alpha (See FR-008, US-3).
- **SC-004**: The sentiment analysis must complete within a practical CPU time limit on a free-tier runner., processing the target sample size (See FR-004, US-2).
- **SC-005**: The visualizations must accurately reflect the statistical results, with error bars representing confidence intervals for the ANOVA means (See FR-007, US-3).

## Assumptions

- **Assumption about data source**: The primary data source is the Pushshift API for r/mentalhealth and r/depression; if unavailable, a pre-scraped static corpus of equivalent mental health discourse (last 5 years) will be used as a fallback. The specific source may vary, but the content type (public mental health discourse) is fixed.
- **Assumption about instrumentation**: The CAMI scale and help-seeking Likert items are treated as validated instruments with established reliability; no internal validation of the scale is performed within this pipeline.
- **Assumption about computational resources**: The entire analysis (data download, cleaning, sentiment scoring, regression, ANOVA) will fit within 7 GB RAM and 14 GB disk, utilizing CPU-only methods (scikit-learn, statsmodels) without GPU acceleration.
- **Assumption about experimental design**: The "Battle," "Journey," and "Medical" vignettes are constructed to be equivalent in length, reading level, and clinical severity, differing *only* in the metaphorical framing.
- **Assumption about inference framing**: Since the discourse analysis is observational, any correlations found are framed as associational rather than causal; causal claims are restricted to the randomized experimental component.
- **Assumption about sample size**: The experimental recruitment target is a minimum of 159 participants (calculated to achieve [deferred] power to detect a medium effect size, Cohen's f = 0.25, at alpha = 0.05). If the actual sample is smaller, a post-hoc power analysis must be documented, and results interpreted with caution regarding Type II error.
- **Assumption about threshold**: The significance threshold for hypothesis testing is fixed at p < 0.05, consistent with standard psychological research conventions.
- **Assumption about data fit**: The discourse corpus will be processed in batches or sampled if the full dataset exceeds the memory constraints of the free-tier runner.
- **Assumption about VADER**: VADER sentiment scores are treated as a measure of general text polarity (positive/negative) and are explicitly NOT a validated measure of the psychological construct of stigma or help-seeking intent.