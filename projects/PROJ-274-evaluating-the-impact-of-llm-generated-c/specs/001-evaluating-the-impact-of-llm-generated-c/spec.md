# Feature Specification: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Feature Branch**: `001-evaluating-llm-docs-impact`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "How does LLM-generated code documentation compare to human-written documentation (or no documentation) in reducing onboarding time and effort for new developers working on open-source codebases?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1)

The research team MUST be able to manage the assignment of recruited volunteers to one of three randomized conditions (LLM docs, Human docs, No docs) and guide them through standardized onboarding tasks on selected open-source repositories while capturing objective metrics. The system provides static instructions and logs metrics, while a human moderator handles real-time guidance and intervention.

**Why this priority**: This is the core experimental mechanism. Without a controlled, randomized execution flow that captures time and interaction data, no comparative analysis can be performed.

**Independent Test**: The system can be tested by running a mock study with 3 simulated participants across the 3 conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

**Acceptance Scenarios**:

1. **Given** a participant is assigned to the "LLM Docs" condition, **When** they begin the first onboarding task, **Then** the system records a precise start timestamp and loads the LLM-generated documentation for that specific repository.
2. **Given** a participant is actively working on a task, **When** they ask a clarification question to the moderator, **Then** the system logs the timestamp and content of the question for later frequency analysis.
3. **Given** a participant completes the final onboarding task, **When** the session ends, **Then** the system records the total elapsed time and prompts the participant to complete the subjective helpfulness survey.

---

### User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

The system MUST be able to ingest source code from selected open-source repositories (≤ 500 files) and generate consistent, high-quality documentation artifacts using a state-of-the-art LLM for the "LLM Docs" experimental condition. The system MUST handle model selection and fallback logic to ensure reproducibility.

**Why this priority**: This provides the independent variable (the documentation content) required for the study. The quality and consistency of this generation directly impact the validity of the comparison against human documentation.

**Independent Test**: The system can be tested by feeding a known codebase (e.g., a small Python utility) into the pipeline and verifying that the output documentation covers the architecture, API usage, and setup instructions without hallucinating non-existent functions.

**Acceptance Scenarios**:

1. **Given** a GitHub repository URL and a commit hash, **When** the generation pipeline is triggered, **Then** the system retrieves the codebase and produces a documentation file (Markdown) within 15 minutes.
2. **Given** a codebase with complex dependency structures, **When** the LLM generates documentation, **Then** the output explicitly mentions the installation steps and key architectural components identified in the code.
3. **Given** the generation process encounters an API rate limit, **When** the retry logic is engaged, **Then** the system retries the request up to 3 times with exponential backoff before failing the specific repository generation.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The system MUST be able to aggregate the collected study data (time, questions, ratings) and perform statistical analysis (ANOVA or Kruskal-Wallis with appropriate post-hoc tests) to determine if differences between conditions are statistically significant, outputting a final report.

**Why this priority**: This transforms raw data into the research findings required to answer the research question. It must handle the specific statistical requirements (multiple comparison correction, assumption validation) to ensure methodological soundness.

**Independent Test**: The system can be tested by feeding a synthetic dataset with known effect sizes into the analysis script and verifying that the calculated p-values and confidence intervals match the expected theoretical values.

**Acceptance Scenarios**:

1. **Given** a complete dataset from 15+ participants across 3 conditions, **When** the analysis script is executed, **Then** the system performs a normality test (Shapiro-Wilk) and selects the appropriate primary test (ANOVA or Kruskal-Wallis).
2. **Given** the primary test indicates a significant difference (p < 0.05), **When** post-hoc tests are run, **Then** the system applies Tukey HSD (if ANOVA) or Dunn's test with Bonferroni correction (if Kruskal-Wallis) to control for family-wise error rate.
3. **Given** the analysis is complete, **When** the report is generated, **Then** the output includes a summary table of means, standard deviations, p-values, and a conclusion statement regarding the null hypothesis.

---

### Edge Cases

- **What happens when** a participant abandons the study before completing all tasks? The system must flag the record as "incomplete" and exclude it from the primary time-analysis, but retain it for dropout-rate reporting.
- **How does the system handle** a scenario where the LLM generates documentation that is so poor it prevents the participant from even starting the task? The system must have a "stop-loss" mechanism where a moderator can intervene and reset the condition or record the task as failed with a maximum time cap.
- **What happens when** the selected open-source repository changes structure between the documentation generation phase and the participant study phase? The system must pin the repository to a specific commit hash to ensure consistency between the generated docs and the code under test.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST manage the assignment of N ≥ 15 recruited volunteer participants to one of three randomized conditions (LLM Docs, Human Docs, No Docs) to ensure statistical power for ANOVA (See US-1).
- **FR-002**: The system MUST generate documentation for selected open-source repositories (≤ 500 files) using a state-of-the-art LLM, ensuring the output is pinned to a specific code commit (See US-2).
- **FR-003**: The system MUST measure and log the exact time elapsed from task start to completion for each participant, with a precision of at least 1 second (See US-1).
- **FR-004**: The system MUST count and log the number of clarification questions asked by each participant during the onboarding session (See US-1).
- **FR-005**: The system MUST perform a normality test (Shapiro-Wilk) on task completion time; if assumptions are met, perform a one-way ANOVA followed by Tukey HSD post-hoc tests; if assumptions are violated, perform a Kruskal-Wallis test followed by Dunn's test with Bonferroni correction (See US-3).
- **FR-006**: The system MUST apply a family-wise error rate correction (Tukey HSD for ANOVA, Bonferroni for Dunn's test) when conducting multiple pairwise comparisons to maintain the validity of the statistical inference (See US-3).
- **FR-007**: The system MUST execute the entire data analysis pipeline (including statistical tests) on a CPU-only environment within ≤ 6 hours runtime and ≤ 7GB RAM peak memory usage (See US-3).
- **FR-008**: The system MUST implement model selection logic that attempts a primary API model and falls back to a local model if the API fails, ensuring the 'LLM Docs' condition is reproducible (See US-2).
- **FR-009**: The system MUST enforce repository selection criteria: selected repositories must have existing, high-quality human documentation verified by a rubric to ensure the 'Human' condition is valid and not confounded by poor quality (See US-2).

### Key Entities

- **Participant**: A volunteer recruited for the study, characterized by their assigned condition, demographic data (optional), and performance metrics.
- **Repository**: An open-source project selected for the study, characterized by its URL, pinned commit hash, and documentation status (LLM-generated, Human, or None).
- **Task**: A standardized onboarding activity (e.g., "fix bug X", "explain module Y") assigned to participants, characterized by a unique ID and expected completion criteria.
- **Metric**: A quantitative observation collected during the study, including task completion time, question count, and subjective helpfulness rating.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Task completion time is measured against the baseline established by the "No Documentation" condition to determine the absolute time savings of LLM vs. Human docs (See US-1, US-3).
- **SC-002**: The number of clarification questions is measured against the "No Documentation" condition to assess the reduction in cognitive load or ambiguity (See US-1, US-3).
- **SC-003**: Subjective helpfulness ratings (Likert scale) are measured against the "Human Documentation" condition to evaluate user-perceived quality parity (See US-1, US-3).
- **SC-004**: Statistical significance (p-value) is measured against the alpha threshold of 0.05 to determine if observed differences are not due to random chance (See US-3).
- **SC-005**: The analysis pipeline execution time is measured against a 6-hour threshold, and peak memory usage is measured against a 7GB threshold to ensure the study is reproducible without GPU resources (See US-3).

## Assumptions

- **Assumption about data source**: The selected open-source repositories (≤ 500 files) are small enough that the generated documentation and codebase fit entirely within the 7GB RAM limit of the analysis environment.
- **Assumption about methodology**: The 'Human Documentation' condition relies on existing documentation which varies in quality; therefore, findings regarding 'LLM vs. Human' are associational, while the 'LLM vs. None' comparison remains causal due to random assignment. The 'Human' group is treated as a covariate or excluded from the primary causal claim to avoid confounding.
- **Assumption about participant behavior**: Participants will follow the standardized onboarding tasks without external assistance other than the provided documentation and the moderator.
- **Assumption about LLM access**: The LLM API (or local model) used for documentation generation will be available and stable during the data generation phase, with a fallback to a smaller local model if the primary API fails.
- **Assumption about statistical power**: A sample size of 15-20 participants is sufficient to detect a medium effect size (Cohen's f ≈ 0.25) with 80% power at α=0.05 for the planned ANOVA, acknowledging that power may be lower for detecting small effects.
- **Assumption about threshold justification**: The decision to use a p-value threshold of 0.05 is based on the standard community convention in computer science and social science research, and a sensitivity analysis will sweep this threshold (e.g., 0.01, 0.05, 0.10) to report stability of results.