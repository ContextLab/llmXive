# Feature Specification: llmXive follow-up: extending "Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation"

**Feature Branch**: `001-llmxive-cognitive-load`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation' - comparing cognitive load and correction efficiency between structured typed-edit harness vs natural-language chat interface for human researchers fixing localized errors in scientific figures."

## User Scenarios & Testing

### User Story 1 - Data Curation, Interface Setup, and Within-Subjects Design (Priority: P1)

The system must prepare a static, reproducible dataset of failed figure generations from CrafterBench., deploy two distinct editing interfaces (Structured Harness and Natural Language Chat), and implement a within-subjects design with randomized and counterbalanced interface order for each participant. This forms the foundational layer for the entire study; without a consistent set of errors, functional interfaces, and a valid experimental design, no comparative analysis can occur.

**Why this priority**: This is the prerequisite for all data collection. If the dataset is not curated, the interfaces are not functional, or the experimental design is flawed (e.g., no counterbalancing), the study cannot proceed or yield valid results. It is the most critical dependency.

**Independent Test**: A script can be run to download the CrafterBench figures, inject known localized errors, verify that both the structured harness and the chat interface load successfully (returning a 200 OK status), and confirm that the session initialization logic correctly randomizes the interface order for a test participant.

**Acceptance Scenarios**:

1. **Given** a list of exactly 50 failed figure generation IDs from CrafterBench, **When** the curation script executes, **Then** a local directory containing a set of raster images with injected localized errors and corresponding ground-truth layout vectors is created.
2. **Given** a participant session initialized, **When** the user selects the "Structured Harness" mode, **Then** the system presents a form-based interface accepting typed edits (e.g., `set_color("axis", "red")`) and returns a 200 OK status.
3. **Given** a participant session initialized, **When** the user selects the "Chat Interface" mode, **Then** the system presents a text-input chat window capable of receiving natural language instructions (e.g., "Make the axis red") and returns a 200 OK status.
4. **Given** a participant session initialized, **When** the system assigns the interface order, **Then** the order is randomized and counterbalanced (e.g., [deferred] start with Structured, [deferred] with Chat) to mitigate order effects.

---

### User Story 2 - Interaction Logging, Metric Capture, and Semantic Validation (Priority: P1)

The system must automatically record all user interactions, timestamps, and iteration counts for each task without relying on self-reporting. Additionally, the system must validate "success" using both a ground-truth vector match AND a semantic equivalence check (e.g., visual similarity or expert rating) to avoid syntactic bias.

**Why this priority**: The core research question relies on quantitative metrics (latency, iterations). Manual logging introduces human error and bias, invalidating the statistical analysis. Furthermore, relying solely on vector match creates a tautological trap; a semantic check ensures the metric reflects true "correction efficiency" and not just syntactic compliance.

**Independent Test**: A participant completes a single task in both modes; the system output logs are parsed to verify that start time, end time, and every intermediate edit attempt are recorded with millisecond precision. Additionally, a test case with a semantically correct but syntactically different output must be flagged as a "success" by the semantic check.

**Acceptance Scenarios**:

1. **Given** a user is actively editing a figure, **When** the user submits an edit (typed or chat), **Then** the system logs the timestamp, the edit payload, and the iteration count to a local JSON log file.
2. **Given** a user successfully fixes a figure (matches ground truth AND passes semantic check), **When** the validation check passes, **Then** the system records the "time-to-success" metric and terminates the current task timer.
3. **Given** a user exceeds 15 minutes on a single task, **When** the timeout is reached, **Then** the system logs the task as "aborted" and records the total time elapsed up to that point.
4. **Given** a user produces a figure that is visually correct but syntactically different, **When** the semantic equivalence check runs, **Then** the system flags the task as "success" based on the semantic score (≥ 0.95) even if the vector match fails.

---

### User Story 3 - Statistical Analysis and Result Reporting (Priority: P2)

The system must perform a robust paired statistical test (Wilcoxon signed-rank test by default, as recommended for small sample sizes) on the collected metrics to determine if the difference in performance between the two interfaces is statistically significant, and generate a summary report.

**Why this priority**: This delivers the final research output. It transforms raw logs into the answer for the research question, allowing the team to conclude whether structured interfaces reduce cognitive load. Using a robust test (Wilcoxon) avoids the methodological flaws of two-stage testing (normality check + t-test) which inflates Type I errors.

**Independent Test**: A synthetic dataset with known differences between two groups is fed into the analysis script; the script must correctly identify the significance level (p-value) using the Wilcoxon signed-rank test and output the correct test statistic.

**Acceptance Scenarios**:

1. **Given** a completed dataset with paired metrics (Structured vs. Chat), **When** the analysis script runs, **Then** it outputs a p-value for the difference in "time-to-success" and "iteration count" using the Wilcoxon signed-rank test.
2. **Given** the statistical test is complete, **When** the report is generated, **Then** it includes a summary table comparing mean/median times and iteration counts for both interfaces with confidence intervals.
3. **Given** the analysis is complete, **When** the report is generated, **Then** it includes a breakdown of success rates based on both vector match and semantic equivalence.

---

### Edge Cases

- What happens when a participant fails to fix a figure within the 15-minute timeout? (System logs as aborted, excludes from "time-to-success" mean but includes in "iteration count" analysis as max iterations).
- How does the system handle a corrupted ground-truth vector for a specific figure? (System skips that specific figure for that participant and logs a warning, ensuring N is adjusted in the final report).
- What happens if the natural language chat interface returns a figure that looks correct but is technically wrong (pixel-perfect mismatch)? (The system relies on the semantic equivalence check (≥ 0.95) and vector match; if both fail, it is a failure).
- What happens if the semantic equivalence check is ambiguous (e.g., score = 0.94)? (The system flags the case for manual review and excludes it from the primary statistical analysis).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and curate a static subset of exactly 50 failed figure generations from the CrafterBench dataset with known localized errors. (See US-1)
- **FR-002**: System MUST provide two distinct, functional interfaces for editing: a structured typed-edit harness and a natural-language chat interface, and MUST implement a within-subjects design with randomized and counterbalanced interface order for each participant. (See US-1)
- **FR-003**: System MUST automatically log the start time, end time, and every intermediate edit attempt for each participant task with millisecond precision. (See US-2)
- **FR-004**: System MUST validate "success" by comparing the user's final output against a pre-defined ground-truth vector. (See US-2)
- **FR-005**: System MUST perform a semantic equivalence check (e.g., visual similarity score ≥ 0.95 or expert rating) as a secondary success metric to validate that the correction is semantically correct, not just syntactically identical. (See US-2)
- **FR-006**: System MUST perform a Wilcoxon signed-rank test on the collected metrics (time-to-success, iteration count) to determine statistical significance, without a preliminary normality check. (See US-3)
- **FR-007**: System MUST generate a final report containing the mean/median time-to-success and iteration counts for both interfaces, along with the calculated p-value, confidence intervals, and a breakdown of success rates by vector match and semantic equivalence. (See US-3)

### Key Entities

- **FigureTask**: Represents a single figure editing instance, containing the source image, the injected error, the ground-truth vector, and the assigned interface mode.
- **ParticipantSession**: Represents a single user's run, containing the anonymized ID, the sequence of tasks performed, the assigned interface order, and the aggregated metrics.
- **InteractionLog**: A record of a single edit action, containing the timestamp, the edit payload (typed or text), and the iteration number.
- **SemanticValidation**: A record of the semantic equivalence check, containing the similarity score and the pass/fail status.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in mean "time-to-success" between the structured harness and chat interface is measured against a null hypothesis of zero difference using the Wilcoxon signed-rank test. (See FR-006)
- **SC-002**: The difference in median "iteration count" between the two interfaces is measured against the null hypothesis to determine if one interface requires significantly fewer attempts. (See FR-006)
- **SC-003**: The validity of the "success" metric is measured against the ground-truth vector comparison (ensuring [deferred] of success flags correspond to an exact vector match) AND an external semantic equivalence check (e.g., expert human rating or visual similarity score ≥ 0.95). (See FR-004, FR-005)
- **SC-004**: The data collection completeness is measured against the target N=30 participants, requiring at least 25 valid completed sessions (retention rate ≥ 83%) to proceed to analysis. (See FR-003)
- **SC-005**: The computational feasibility is measured against the standard free-tier time limit, ensuring the entire curation, simulation (if any), and analysis pipeline completes within ≤ 6 hours on CPU-only resources. (See FR-001, FR-006)

## Assumptions

- **Assumption about data availability**: The CrafterBench dataset (or a representative static subset of failed figures) is accessible via the provided arXiv repository links and can be downloaded without authentication barriers during the CI run.
- **Assumption about participant simulation and study design**: The spec deliverable is the **analysis pipeline and instrumentation** (the software system), which will be validated on simulated data in the CI environment to ensure it functions correctly before human recruitment. The **study design** targets N=30 human researchers from non-ML fields for the actual cognitive load study. The simulated data is used solely to validate the pipeline logic (logging, statistical tests, randomization) and does not replace the human study. The pipeline MUST be capable of supporting the recruitment workflow (session initialization, randomization, counterbalancing) for the future human study.
- **Assumption about statistical power**: The sample size of N=30 is assumed to be sufficient to detect a medium effect size (Cohen's d ≈ 0.5) with 80% power at α=0.05 for a within-subjects design, as per standard HCI power analysis conventions.
- **Assumption about compute environment**: The analysis relies solely on lightweight Python libraries (pandas, scipy, numpy) that fit within the RAM and CPU core limits of the GitHub Actions free runner.
- **Assumption about ground truth**: The ground-truth layout vectors for the figures are available in a machine-readable format (e.g., JSON or SVG path data) that allows for exact comparison with user outputs.
- **Assumption about semantic validation**: A reliable method for semantic equivalence check (e.g., a pre-trained visual similarity model or a protocol for expert human rating) is available to supplement the vector match.