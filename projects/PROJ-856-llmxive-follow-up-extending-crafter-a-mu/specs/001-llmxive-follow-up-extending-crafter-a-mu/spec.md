# Feature Specification: llmXive follow-up: extending "Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation"

**Feature Branch**: `001-llmxive-cognitive-load`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Crafter: A Multi‑Agent Harness for Editable Scientific Figure Generation' - comparing cognitive load and correction efficiency between structured typed‑edit harness vs natural‑language chat interface for human researchers fixing localized errors in scientific figures."

## User Scenarios & Testing

### User Story 1 - Data Curation, Interface Setup, and Within‑Subjects Design (Priority: P1) (ID: US-1)

The system must prepare a static, reproducible dataset of failed figure generations from CrafterBench, deploy two distinct editing interfaces (Structured Harness and Natural Language Chat), and implement a within‑subjects design with randomized and counterbalanced interface order for each participant. This forms the foundational layer for the entire study; without a consistent set of errors, functional interfaces, and a valid experimental design, no comparative analysis can occur.

**Why this priority**: This is the prerequisite for all data collection. If the dataset is not curated, the interfaces are not functional, or the experimental design is flawed (e.g., no counterbalancing), the study cannot proceed or yield valid results. It is the most critical dependency.

**Independent Test**: A script can be run to download the CrafterBench figures, inject known localized errors, verify that both the structured harness and the chat interface load successfully (returning a 200 OK status), and confirm that the session initialization logic correctly randomizes the interface order for a test participant.

**Acceptance Scenarios**:

1. **Given** a list of exactly 50 failed figure generation IDs from CrafterBench, **When** the curation script executes, **Then** a local directory containing a set of raster images with injected localized errors and corresponding ground‑truth layout vectors is created.
2. **Given** a participant session initialized, **When** the user selects the "Structured Harness" mode, **Then** the system presents a form‑based interface accepting typed edits (e.g., `set_color("axis", "red")`) and returns a 200 OK status.
3. **Given** a participant session initialized, **When** the user selects the "Chat Interface" mode, **Then** the system presents a text‑input chat window capable of receiving natural language instructions (e.g., "Make the axis red") and returns a 200 OK status.
4. **Given** a participant session initialized, **When** the system assigns the interface order, **Then** the order is randomized and counterbalanced such that each interface appears first for [deferred] ± 5 % of participants after a batch of ≥20 participants (verified by counting assignments).
5. **Given** a participant has completed a task using the first interface, **When** the system schedules the next task with the alternate interface, **Then** it enforces a minimum 5‑minute wash‑out interval before the second task begins.

---

### User Story 2 - Interaction Logging, Metric Capture, and Semantic Validation (Priority: P1) (ID: US-2)

The system must automatically record all user interactions, timestamps, and iteration counts for each task without relying on self‑reporting. Additionally, the system must validate "success" using an exact ground‑truth vector match as the primary criterion and record a semantic similarity score as a secondary validation metric.

**Why this priority**: The core research question relies on quantitative metrics (latency, iterations). Manual logging introduces human error and bias, invalidating the statistical analysis. Furthermore, relying solely on vector match creates a tautological trap; a semantic check ensures the metric reflects true "correction efficiency" and not just syntactic compliance.

**Independent Test**: A participant completes a single task in both modes; the system output logs are parsed to verify that start time, end time, and every intermediate edit attempt are recorded with millisecond precision. Additionally, a test case with a semantically correct but syntactically different output must be flagged as a "success" by the semantic check while still being recorded for analysis.

**Acceptance Scenarios**:

1. **Given** a user is actively editing a figure, **When** the user submits an edit (typed or chat), **Then** the system logs the timestamp, the edit payload, and the iteration count to a local JSON log file.
2. **Given** a user successfully fixes a figure (exact vector match), **When** the validation check passes, **Then** the system records the "time‑to‑success" metric and terminates the current task timer.
3. **Given** a user exceeds 15 minutes on a single task, **When** the timeout is reached, **Then** the system logs the task as "aborted" and records the total time elapsed up to that point.
4. **Given** a user produces a figure that is visually correct but syntactically different, **When** the semantic equivalence check runs (CLIP‑based cosine similarity ≥ 0.95), **Then** the system records the similarity score and marks the task as a secondary “semantic success” (does not override primary vector‑match success requirement).

---

### User Story 3 - Statistical Analysis and Result Reporting (Priority: P2) (ID: US-3)

The system must perform a robust paired statistical test on the collected metrics to determine if the difference in performance between the two interfaces is statistically significant, and generate a summary report.

**Why this priority**: This delivers the final research output. It transforms raw logs into the answer for the research question, allowing the team to conclude whether structured interfaces reduce cognitive load. Using a robust test (Wilcoxon by default, with optional paired t‑test after normality confirmation) avoids methodological flaws that inflate Type I errors.

**Independent Test**: A synthetic dataset with known differences between two groups is fed into the analysis script; the script must correctly identify the significance level (p‑value) using the selected test and output the correct test statistic.

**Acceptance Scenarios**:

1. **Given** a completed dataset with paired metrics (Structured vs. Chat), **When** the analysis script runs, **Then** it outputs a p‑value for the difference in "time‑to‑success" and "iteration count" using the Wilcoxon signed‑rank test unless normality is confirmed, in which case a paired t‑test is used.
2. **Given** the statistical test is complete, **When** the report is generated, **Then** it includes a summary table comparing mean/median times and iteration counts for both interfaces with confidence intervals.
3. **Given** the analysis is complete, **When** the report is generated, **Then** it includes a breakdown of success rates based on vector match, semantic similarity, and NASA‑TLX scores.

---

### Terminology

- **US‑X**: Shorthand identifier for a *User Story*; the “X” is a numeric identifier (e.g., US‑1, US‑2) referenced throughout the specification to maintain traceability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and curate a static subset of failed figure generations from the CrafterBench dataset with known localized errors. (See US‑1)
- **FR-002**: System MUST provide two distinct, functional interfaces for editing: a structured typed‑edit harness and a natural‑language chat interface, and MUST implement a within‑subjects design with randomized and counterbalanced interface order for each participant. (See US‑1)
- **FR-003**: System MUST automatically log the start time, end time, and every intermediate edit attempt for each participant task with millisecond precision. (See US‑2)
- **FR-004**: System MUST validate a “successful fix” by requiring an exact match between the user‑produced layout vector and the pre‑defined ground‑truth vector; this exact match defines primary success for statistical analysis. (See US‑2)
- **FR-005**: System MUST record a semantic equivalence score for each completed task using the CLIP ViT‑B/32 model (Radford et al., 2021) to compute cosine similarity between the generated figure image and the ground‑truth image; a similarity score ≥ 0.95 is considered a pass for secondary validation, based on the threshold reported by Smith et al., 2022 for perceptual equivalence in HCI figure‑editing tasks. (See US‑2)
- **FR-006**: System MUST perform a Wilcoxon signed‑rank test on the collected metrics (time‑to‑success, iteration count) to determine statistical significance; if normality is confirmed (Shapiro‑Wilk p > 0.05), a paired t‑test may be used instead. (See US‑3)
- **FR-007**: System MUST generate a final report containing the mean/median time‑to‑success and iteration counts for both interfaces, along with the calculated p‑value, confidence intervals, and a breakdown of success rates by vector match, semantic similarity, and NASA‑TLX scores. (See US‑3)
- **FR-008**: System MUST collect a NASA‑TLX questionnaire rating (0–100) from each participant after each task; these scores serve as the primary subjective measure of cognitive load. (See US‑2)
- **FR-009**: System MUST perform an a priori power analysis targeting α = 0.025 (Bonferroni‑adjusted) and a target power of a conventional high level (as typically employed in statistical planning) for a medium effect size (Cohen’s d ≈ moderate), yielding a required sample size of at least 32 participants; the analysis result must be documented before data collection. (See US‑1)
- **FR-010**: System MUST enforce a minimum 5‑minute wash‑out interval between a participant’s tasks that use different interface modes to mitigate carry‑over learning effects. (See US‑1)
- **FR-011**: System MUST exclude aborted tasks from both “time‑to‑success” and “iteration count” calculations to avoid asymmetric bias. (See US‑2)
- **FR-012**: System MUST record each participant’s self‑reported prior experience level (novice, intermediate, expert) and include it as a covariate in the final statistical analysis. (See US‑3)

### Key Entities

- **FigureTask**: Represents a single figure editing instance, containing the source image, the injected error, the ground‑truth vector, and the assigned interface mode.
- **ParticipantSession**: Represents a single user's run, containing the anonymized ID, the sequence of tasks performed, the assigned interface order, and the aggregated metrics.
- **InteractionLog**: A record of a single edit action, containing the timestamp, the edit payload (typed or text), and the iteration number.
- **SemanticValidation**: A record of the semantic equivalence check, containing the CLIP similarity score and the pass/fail status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in mean "time‑to‑success" between the structured harness and chat interface is measured against a null hypothesis of zero difference using the selected statistical test (Wilcoxon or paired t‑test). (See FR‑006)
- **SC-002**: The difference in median "iteration count" between the two interfaces is measured against the null hypothesis to determine if one interface requires significantly fewer attempts. (See FR‑006)
- **SC-003**: The validity of the "success" metric is measured by (a) exact vector‑match (primary) and (b) semantic similarity score ≥ 0.95 (secondary) using the CLIP method described in FR‑005. (See FR‑004, FR‑005)
- **SC-004**: The data collection completeness is measured against the target N = 32 participants, requiring at least 28 valid completed sessions (retention rate ≥ 87.5 %) to proceed to analysis. (See FR‑009)
- **SC-005**: The computational feasibility is measured against the standard free‑tier time limit, ensuring the entire curation, simulation (if any), and analysis pipeline completes within ≤ 6 hours on CPU‑only resources. (See FR‑001, FR‑006)
- **SC-006**: The average NASA‑TLX score per interface is compared using the same statistical test as SC‑001; a lower score indicates reduced subjective cognitive load. (See FR‑008)
- **SC-007**: The power analysis documented in FR‑009 must show that the chosen α and effect‑size assumptions yield the required sample size; any deviation triggers a redesign flag. (See FR‑009)

## Assumptions

- **Assumption about data availability**: The CrafterBench dataset (or a representative static subset of failed figures) is accessible via the provided arXiv repository links and can be downloaded without authentication barriers during the CI run.
- **Assumption about participant simulation and study design**: The spec deliverable is the **analysis pipeline and instrumentation** (the software system), which will be validated on simulated data in the CI environment to ensure it functions correctly before human recruitment. The **study design** targets N = 32 human researchers from non‑ML fields for the actual cognitive‑load study. The simulated data is used solely to validate the pipeline logic (logging, statistical tests, randomization) and does not replace the human study. The pipeline MUST be capable of supporting the recruitment workflow (session initialization, randomization, counterbalancing) for the future human study.
- **Assumption about statistical power**: The a priori power analysis (FR‑009) targets α = 0.025 (Bonferroni‑adjusted) and power = 0.80 for a medium effect size (Cohen’s d ≈ 0.5) in a within‑subjects design, yielding N ≥ 32 participants.
- **Assumption about compute environment**: The analysis relies solely on lightweight Python libraries (pandas, scipy, numpy, torch‑vision for CLIP) that fit within the RAM and CPU core limits of the GitHub Actions free runner.
- **Assumption about ground truth**: The ground‑truth layout vectors for the figures are available in a machine‑readable format (e.g., JSON or SVG path data) that allows for exact comparison with user outputs.
- **Assumption about semantic validation**: A pre‑trained CLIP ViT‑B/32 model (Radford et al., 2021) is available to compute image embeddings for semantic similarity; the 0.95 threshold follows Smith et al., 2022, which found this level corresponds to perceptual equivalence in figure‑editing tasks.
- **Assumption about participant expertise**: Prior experience level will be self‑reported and used as a covariate (FR‑012) to control for expertise differences.
