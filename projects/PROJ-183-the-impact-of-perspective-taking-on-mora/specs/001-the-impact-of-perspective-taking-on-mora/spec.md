# Feature Specification: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Feature Branch**: `001-perspective-taking-moral-outrage`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Does prompting individuals to adopt the perspective of a disagreeing online poster reduce their self‑reported moral outrage toward the post?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stimulus Curation and Randomization (Priority: P1)

The system MUST ingest the "Against the Others!" moral outrage dataset (or a validated alternative), filter for high-outrage posts on specific controversial topics, and generate a randomized set of unique stimuli (multiple per topic) with paired instruction sets (Perspective-Taking vs. Control Summarization).

**Why this priority**: Without a curated, balanced, and randomized set of stimuli, the experimental intervention cannot be administered, rendering the study impossible. This is the foundational data layer.

**Independent Test**: The system can be tested by executing the data ingestion script and verifying the output JSON contains exactly 40 unique posts, split evenly by topic, with both instruction variants correctly attached to each post ID.

**Acceptance Scenarios**:

1. **Given** the raw annotated Twitter dataset is available, **When** the ingestion script runs with filters for "high-outrage" and specific topics (e.g., climate, immigration), **Then** the output contains exactly 40 posts, with 20 per topic, and no duplicates.
2. **Given** a selected post, **When** the stimulus generator runs, **Then** two distinct instruction strings are generated: one for perspective-taking and one for control summarization, both attached to the post ID.

---

### User Story 2 - Pipeline Simulation & Validation (Priority: P2)

The system MUST simulate the assignment of synthetic participants to two experimental conditions (Perspective-Taking vs. Control), administer the stimuli with the assigned instructions, and record the resulting -item Moral Outrage Scale scores to validate the analysis pipeline logic.

**Why this priority**: This represents the software validation phase. It ensures the randomization, data capture, and statistical analysis code functions correctly BEFORE human data is collected. It does NOT validate the psychological hypothesis.

**Independent Test**: The system can be tested by running a simulation where A set of synthetic participants is assigned to conditions., provided with stimuli, and generating synthetic outrage scores; the output dataset must reflect the correct condition labels and score ranges, and the analysis module must produce deterministic results for known inputs.

**Acceptance Scenarios**:

1. **Given** 200 synthetic participant IDs, **When** the assignment logic runs, **Then** approximately 100 participants are assigned to the "Perspective-Taking" condition and 100 to the "Control" condition, with no overlap and a split within 5% of 50/50.
2. **Given** a synthetic participant assigned to a condition, **When** they process a set of stimuli, **Then** the system records 5 individual 7-item Likert scores and calculates a mean outrage score per participant.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST compute the difference in mean moral outrage scores between the two conditions using an independent-samples t-test, calculate effect sizes (Cohen's d), and perform a robustness check using a Mann-Whitney U test.

**Why this priority**: This delivers the final research output. It validates whether the hypothesis is supported and provides the necessary statistical evidence for the project's conclusions.

**Independent Test**: The system can be tested by feeding it a dataset with known group differences; the output must correctly identify the p-value, confidence interval, and effect size, matching manual calculations within a 1% margin of error.

**Acceptance Scenarios**:

1. **Given** a dataset with mean scores for Condition A and Condition B, **When** the t-test module runs, **Then** it outputs a p-value, 95% confidence interval for the mean difference, and Cohen's d.
2. **Given** the same dataset, **When** the robustness check runs, **Then** it outputs a Mann-Whitney U statistic and a corresponding p-value to verify the non-parametric consistency of the result.

---

### User Story 4 - Human Experiment Execution (Priority: P4)

The system MUST provide the interface and data collection logic for human participants (recruited via Prolific or similar) to view the stimuli, respond to the instructions, and submit their Moral Outrage Scale scores, ensuring strict separation from synthetic data.

**Why this priority**: This is the actual data generation phase required to answer the research question. It replaces the simulation for the final hypothesis test.

**Independent Test**: The system can be tested by deploying a pilot with real humans and verifying that the collected data is stored in a distinct "human" dataset, separate from the "simulation" dataset, with correct condition labels.

**Acceptance Scenarios**:

1. **Given** a human participant ID, **When** they complete the survey, **Then** their data is tagged as 'human' and stored in the primary analysis dataset, distinct from simulation data.
2. **Given** a participant fails an attention check, **Then** their record is flagged for exclusion prior to analysis.

---

### Edge Cases

- What happens if the dataset contains fewer than 40 high-outrage posts meeting the topic criteria? (System must halt with a specific error indicating insufficient data).
- How does the system handle participants who fail attention checks? (System must flag and exclude these records from the final analysis dataset; defined as >2 missed items out of 5 embedded checks).
- What if the t-test assumptions (normality, homogeneity of variance) are violated? (System must rely on the Mann-Whitney U robustness check as the primary fallback for inference).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the "Against the Others!" annotated Twitter dataset (or a validated alternative high-outrage dataset) from the provided arXiv/GitHub source to extract posts tagged as "high-outrage". (See US-1)
- **FR-002**: System MUST filter the dataset to retain only posts related to at least two specific controversial topics (e.g., climate policy, immigration) and randomly select a representative sample of posts per topic. (See US-1)
- **FR-003**: System MUST generate two distinct instruction prompts for every selected post: a "Perspective-Taking" prompt and a "Control Summarization" prompt. (See US-1)
- **FR-004**: System MUST assign a large cohort of simulated participants to two groups using a randomization algorithm that ensures balanced group sizes (within 5% of a 50/50 split). (See US-2)
- **FR-005**: System MUST calculate the mean score across the items of the Moral Outrage Scale for each participant and aggregate these by experimental condition. (See US-2)
- **FR-006**: System MUST perform an independent-samples t-test comparing the mean outrage scores of the two conditions and report the p-value and Cohen's d. (See US-3)
- **FR-007**: System MUST execute a Mann-Whitney U test as a non-parametric robustness check on the same data. (See US-3)
- **FR-008**: System MUST exclude any participant records where attention checks were failed (defined as >2 missed items out of 5 embedded attention check items) prior to statistical analysis. (See US-2, US-4)
- **FR-009**: System MUST maintain separate data streams for simulated participants (US-2) and human participants (US-4) to prevent data contamination. (See US-2, US-4)
- **FR-010**: System MUST perform a formal power analysis to determine the required sample size for the human experiment before recruitment begins. (See US-4)
- **FR-011**: System MUST assign human participants to two groups using a randomization algorithm that ensures balanced group sizes (within 5% of a 50/50 split). (See US-4)

### Key Entities

- **Stimulus**: A single social media post with its associated metadata (topic, outrage label) and the two generated instruction variants.
- **Participant**: A subject record (simulated or human) containing demographics, assigned condition, attention check status, and raw response scores.
- **Response**: A set of 7 Likert-scale scores (1-7) representing the moral outrage rating for a specific stimulus.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The difference in mean moral outrage scores between conditions is measured against the null hypothesis (no difference) using an independent-samples t-test. (See US-3)
- **SC-002**: The effect size of the intervention is measured against the design target of Cohen's d ≥ 0.2 (medium effect) to determine practical significance. (See US-3)
- **SC-003**: The robustness of the findings is measured against the Mann-Whitney U test results to confirm consistency in the absence of normality assumptions. (See US-3)
- **SC-004**: Data integrity is measured against the exclusion criteria, ensuring that the participant pass rate meets a pre-defined minimum viable threshold (to be set during protocol registration). (See US-2, US-4)
- **SC-005**: The analysis pipeline is measured against a computational efficiency target, ensuring the entire pipeline (data loading, randomization, statistical testing) completes within 1 hour on a standard CPU environment. (See Assumptions)

## Assumptions

- The "Against the Others!" dataset is publicly accessible via the link provided in the arXiv paper and contains sufficient "high-outrage" posts on the specified topics (climate, immigration) to meet the n=40 requirement. If unavailable, a validated alternative dataset will be used.
- The Moral Outrage Scale (Smith et al., n.d.) is a validated 7-item instrument suitable for self-reporting in this online context, and the 7-point Likert scale is the standard metric for the study.
- The analysis will be conducted using Python libraries (pandas, scipy, statsmodels) which are compatible with the CPU-only, no-GPU environment of the GitHub Actions free tier.
- Since the study design is observational in the sense of using a pre-existing dataset for stimulus selection (though the intervention is experimental), the analysis will frame results as associational effects of the prompt type on outrage scores, not causal claims about the posts themselves.
- The a target sample size sufficient to ensure adequate statistical power [deferred: to be validated by formal power analysis] is assumed to provide sufficient power (≥ 0.80) to detect a medium effect size (Cohen's d indicates a moderate effect size.) at α = 0.05, assuming a two-tailed test.
- The "attention check" mechanism is implemented as embedded items in the survey flow, and failure is defined strictly as missing >2 items.
- No GPU acceleration, CUDA, or large language model inference is required; all statistical operations are classical and computationally lightweight.
- The analysis pipeline will complete within 1 hour on a standard CPU environment, ensuring reproducibility without excessive resource consumption.