# Feature Specification: The Influence of Chatbot Politeness on User Trust

**Feature Branch**: `001-chatbot-politeness-trust`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Does higher linguistic politeness in text-based chatbot responses lead to higher user-reported trust in the chatbot?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1)

Researcher downloads the Persona-Chat and EmpatheticDialogues datasets, filters dialogues for completeness, and computes a mean politeness score per conversation using an open-source classifier.

**Why this priority**: Without valid input data and politeness features, no statistical analysis is possible. This is the foundational data pipeline.

**Independent Test**: Can be fully tested by running the download and scoring script on a sample of 100 dialogues and verifying that each dialogue has a computed politeness score and that trust ratings are extracted.

**Acceptance Scenarios**:

1. **Given** Persona-Chat and EmpatheticDialogues are accessible, **When** the download script executes, **Then** both datasets are stored locally in a structured format with all dialogue metadata intact.
2. **Given** dialogues are downloaded, **When** the politeness scoring module runs, **Then** each chatbot utterance receives a politeness score and each conversation receives a mean politeness score.
3. **Given** dialogues with missing trust ratings, **When** filtering is applied, **Then** those dialogues are excluded and logged as incomplete.

---

### User Story 2 - Mixed-Effects Regression Analysis (Priority: P2)

Researcher fits a linear mixed-effects model testing the association between politeness scores and trust ratings while controlling for conversation length and accounting for user/dialogue-level random effects.

**Why this priority**: This is the core hypothesis test. It determines whether the research question can be answered.

**Independent Test**: Can be fully tested by running the regression on a pre-processed dataset and verifying that the model converges, produces fixed-effect estimates with p-values, and outputs the results to a CSV file.

**Acceptance Scenarios**:

1. **Given** pre-processed data with politeness and trust scores, **When** the regression model is fitted, **Then** the model converges without error and outputs coefficient estimates for politeness, conversation length, and random effects variance components.
2. **Given** the fitted model, **When** likelihood-ratio tests are executed, **Then** statistical significance (p < 0.05) is reported for fixed effects where applicable.
3. **Given** multiple hypothesis tests (main effect + covariates), **When** correction is applied, **Then** family-wise error rate is controlled via Bonferroni or Benjamini-Hochberg adjustment.

---

### User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

Researcher validates findings by re-running analysis with an alternative lexicon-based politeness classifier and conducts subgroup analyses by user age and gender to test for moderation effects.

**Why this priority**: Robustness checks increase confidence in results; subgroup analyses explore boundary conditions. These are important but secondary to the core analysis.

**Independent Test**: Can be fully tested by running the robustness pipeline on the same dataset and verifying that results are consistent (or divergence is documented) across classifiers and that subgroup splits produce valid statistical outputs.

**Acceptance Scenarios**:

1. **Given** the primary politeness scores, **When** a lexicon-based classifier is applied, **Then** a second set of politeness scores is generated and the regression is re-run, producing comparable or documented-divergent results.
2. **Given** demographic metadata, **When** subgroup analysis is executed by age and gender, **Then** separate model coefficients are computed for each subgroup and interaction terms are tested.
3. **Given** multiple subgroup tests are performed, **When** multiplicity is addressed, **Then** a correction factor is applied to control for inflated Type I error rates across subgroups.

---

### Edge Cases

- What happens when a dialogue lacks trust ratings? → Exclude and log count of excluded dialogues.
- How does system handle dialogues with no chatbot utterances? → Exclude and log count.
- What happens when the politeness classifier fails on an utterance? → Assign NaN and exclude that utterance from the conversation mean.
- How does system handle participants with missing demographic metadata? → Exclude from subgroup analysis but retain for main analysis.
- What happens when the regression model fails to converge? → Report convergence failure, attempt simplified model (remove random effects), and log diagnostic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Persona-Chat and EmpatheticDialogues datasets from their official repositories and store them locally in a structured format (See US-1)
- **FR-002**: System MUST compute a mean politeness score per conversation using an open-source classifier (≤ 100MB) and standardize scores via z-scoring (See US-1)
- **FR-003**: System MUST fit a linear mixed-effects model with the formula `trust ~ politeness + conversation_length + (1|user_id) + (1|dialogue_id)` and report fixed-effect estimates with p-values (See US-2)
- **FR-004**: System MUST apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all hypothesis tests to control family-wise error rate (See US-2)
- **FR-005**: System MUST re-run the analysis with an alternative lexicon-based politeness classifier and compare coefficient estimates to the primary classifier (See US-3)
- **FR-006**: System MUST conduct subgroup analyses by user age and gender, testing for moderation effects via interaction terms (See US-3)
- **FR-007**: System MUST output all results to a CSV file including coefficient estimates, standard errors, p-values, and confidence intervals (See US-2)

### Key Entities *(include if feature involves data)*

- **Dialogue**: A single conversation containing multiple utterances; key attributes include user_id, dialogue_id, trust_rating (1-7 Likert), and mean_politeness_score
- **Utterance**: A single message within a dialogue; key attributes include speaker_role (user/chatbot), text_content, and politeness_score
- **User**: A participant in the dataset; key attributes include user_id, age, gender, and number_of_dialogues

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Total pipeline runtime is measured against the 6-hour GitHub Actions free-tier limit (See US-1, US-2, US-3)
- **SC-002**: Memory footprint is measured against the 7 GB RAM constraint during peak processing (See US-1, US-2)
- **SC-003**: Model convergence rate is measured against the requirement that ≥ 95% of fitted models converge without error (See US-2)
- **SC-004**: Effect size consistency between primary and lexicon-based classifiers is measured against a correlation threshold of r ≥ 0.80 (See US-3)
- **SC-005**: Statistical significance is measured against the p < 0.05 threshold after multiple-comparison correction (See US-2, US-3)

## Assumptions

- Persona-Chat and EmpatheticDialogues datasets contain trust/quality ratings in a parseable format (1-7 Likert scale)
- The open-source Politeness-BERT classifier (≤ 100MB) is available and runs on CPU-only environments without CUDA dependencies
- Conversation length can be computed as word count or utterance count per dialogue
- User demographic metadata (age, gender) is present in ≥ 80% of dialogues to enable subgroup analysis
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM, 14 GB disk) is sufficient for the full pipeline within 6 hours
- Findings will be framed as associational (not causal) given the observational nature of the data (no random assignment)
- Any decision thresholds (e.g., p < 0.05, r ≥ 0.80) are justified by community standards in psychology/statistics literature
- A sensitivity analysis will sweep the significance threshold over {0.01, 0.05, 0.10} and report how headline rates vary across it
- Predictor collinearity between politeness and conversation length will be diagnosed (e.g., VIF < 5) to avoid spurious independent effects
