# Feature Specification: llmXive follow-up: extending "Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation"

**Feature Branch**: `001-llmxive-cognitive-load`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation' - comparing cognitive load and correction efficiency between structured typed-edit harness vs natural-language chat interface for human researchers fixing localized errors in scientific figures."

## User Scenarios & Testing

### User Story 1 - Data Curation and Interface Setup (Priority: P1)

The system must prepare a static, reproducible dataset of failed figure generations and deploy two distinct editing interfaces (Structured Harness and Natural Language Chat) to participants. This forms the foundational layer for the entire study; without a consistent set of errors and functional interfaces, no comparative analysis can occur.

**Why this priority**: This is the prerequisite for all data collection. If the dataset is not curated or the interfaces are not functional, the study cannot proceed. It is the most critical dependency.

**Independent Test**: A script can be run to download the CrafterBench figures, inject known localized errors, and verify that both the structured harness and the chat interface load successfully and accept input for a test case.

**Acceptance Scenarios**:

1. **Given** a list of 50 failed figure generation IDs from CrafterBench, **When** the curation script executes, **Then** a local directory containing 50 raster images with injected localized errors and corresponding ground-truth layout vectors is created.
2. **Given** a participant session initialized, **When** the user selects the "Structured Harness" mode, **Then** the system presents a form-based interface accepting typed edits (e.g., `set_color("axis", "red")`) without crashing.
3. **Given** a participant session initialized, **When** the user selects the "Chat Interface" mode, **Then** the system presents a text-input chat window capable of receiving natural language instructions (e.g., "Make the axis red") and returning an updated figure.

---

### User Story 2 - Interaction Logging and Metric Capture (Priority: P1)

The system must automatically record all user interactions, timestamps, and iteration counts for each task without relying on self-reporting. This ensures the data collected on "time-to-success" and "iteration count" is objective and machine-readable.

**Why this priority**: The core research question relies on quantitative metrics (latency, iterations). Manual logging introduces human error and bias, invalidating the statistical analysis.

**Independent Test**: A participant completes a single task in both modes; the system output logs are parsed to verify that start time, end time, and every intermediate edit attempt are recorded with millisecond precision.

**Acceptance Scenarios**:

1. **Given** a user is actively editing a figure, **When** the user submits an edit (typed or chat), **Then** the system logs the timestamp, the edit payload, and the iteration count to a local JSON log file.
2. **Given** a user successfully fixes a figure (matches ground truth), **When** the validation check passes, **Then** the system records the "time-to-success" metric and terminates the current task timer.
3. **Given** a user exceeds 15 minutes on a single task, **When** the timeout is reached, **Then** the system logs the task as "aborted" and records the total time elapsed up to that point.

---

### User Story 3 - Statistical Analysis and Result Reporting (Priority: P2)

The system must perform paired statistical tests (t-test or Wilcoxon signed-rank) on the collected metrics to determine if the difference in performance between the two interfaces is statistically significant, and generate a summary report.

**Why this priority**: This delivers the final research output. It transforms raw logs into the answer for the research question, allowing the team to conclude whether structured interfaces reduce cognitive load.

**Independent Test**: A synthetic dataset with known differences between two groups is fed into the analysis script; the script must correctly identify the significance level (p-value) and output the correct test statistic.

**Acceptance Scenarios**:

1. **Given** a completed dataset of 30 participants with paired metrics (Structured vs. Chat), **When** the analysis script runs, **Then** it outputs a p-value for the difference in "time-to-success" and "iteration count".
2. **Given** the normality assumption of the data is violated (Shapiro-Wilk p < 0.05), **When** the analysis script runs, **Then** it automatically switches to a Wilcoxon signed-rank test instead of a paired t-test.
3. **Given** the statistical test is complete, **When** the report is generated, **Then** it includes a summary table comparing mean/median times and iteration counts for both interfaces with confidence intervals.

---

### Edge Cases

- What happens when a participant fails to fix a figure within the 15-minute timeout? (System logs as aborted, excludes from "time-to-success" mean but includes in "iteration count" analysis as max iterations).
- How does the system handle a corrupted ground-truth vector for a specific figure? (System skips that specific figure for that participant and logs a warning, ensuring N is adjusted in the final report).
- What happens if the natural language chat interface returns a figure that looks correct but is technically wrong (pixel-perfect mismatch)? (The system relies strictly on the ground-truth vector comparison, not visual similarity, to mark success).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and curate a static subset of failed figure generations from the CrafterBench dataset with known localized errors. (See US-1)
- **FR-002**: System MUST provide two distinct, functional interfaces for editing: a structured typed-edit harness and a natural-language chat interface. (See US-1)
- **FR-003**: System MUST automatically log the start time, end time, and every intermediate edit attempt for each participant task with millisecond precision. (See US-2)
- **FR-004**: System MUST validate "success" by comparing the user's final output against a pre-defined ground-truth vector, not by visual inspection or model confidence. (See US-2)
- **FR-005**: System MUST perform a normality check (Shapiro-Wilk) on the collected metrics and automatically select either a paired t-test or Wilcoxon signed-rank test based on the result. (See US-3)
- **FR-006**: System MUST generate a final report containing the mean/median time-to-success and iteration counts for both interfaces, along with the calculated p-value and confidence intervals. (See US-3)

### Key Entities

- **FigureTask**: Represents a single figure editing instance, containing the source image, the injected error, the ground-truth vector, and the assigned interface mode.
- **ParticipantSession**: Represents a single user's run, containing the anonymized ID, the sequence of tasks performed, and the aggregated metrics.
- **InteractionLog**: A record of a single edit action, containing the timestamp, the edit payload (typed or text), and the iteration number.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The difference in mean "time-to-success" between the structured harness and chat interface is measured against a null hypothesis of zero difference using a paired statistical test. (See FR-005)
- **SC-002**: The difference in median "iteration count" between the two interfaces is measured against the null hypothesis to determine if one interface requires significantly fewer attempts. (See FR-005)
- **SC-003**: The validity of the "success" metric is measured against the ground-truth vector comparison, ensuring [deferred] of success flags correspond to a vector match. (See FR-004)
- **SC-004**: The data collection completeness is measured against the target N=30 participants, requiring at least 25 valid completed sessions ([deferred] retention) to proceed to analysis. (See FR-003)
- **SC-005**: The computational feasibility is measured against the standard free-tier time limit, ensuring the entire curation, simulation (if any), and analysis pipeline completes within the time budget on CPU-only resources. (See FR-001, FR-005)

## Assumptions

- **Assumption about data availability**: The CrafterBench dataset (or a representative static subset of 50 failed figures) is accessible via the provided arXiv repository links and can be downloaded without authentication barriers during the CI run.
- **Assumption about participant simulation**: Since recruiting 30 real human researchers in a CI environment is infeasible, the "participants" will be simulated by a deterministic script or a small set of pre-recorded interaction logs that mimic human behavior patterns (or the study is designed as a "proof of concept" pipeline where the analysis logic is validated on synthetic data, with the assumption that the *methodology* is validated for future real-human deployment). *Correction*: The idea specifies recruiting N=30 researchers. To fit the "research complete" stage in a CI environment, the assumption is that the **analysis pipeline and instrumentation** are the deliverables, and the "participants" data is either (a) generated by a high-fidelity simulator for the purpose of validating the statistical logic, or (b) the spec assumes the CI job runs the *analysis code* on a provided dataset, while the actual data collection happens offline. Given the constraint "No heavy training... on CPU", we assume the **data collection phase is offline** and the CI job validates the **analysis pipeline** on a provided sample dataset of 30 simulated sessions.
- **Assumption about statistical power**: The sample size of N=30 is assumed to be sufficient to detect a medium effect size (Cohen's d ≈ 0.5) with 80% power at α=0.05 for a within-subjects design, as per standard HCI power analysis conventions.
- **Assumption about compute environment**: The analysis relies solely on lightweight Python libraries (pandas, scipy, numpy) that fit within the RAM and CPU core limits of the GitHub Actions free runner.
- **Assumption about ground truth**: The ground-truth layout vectors for the 50 figures are available in a machine-readable format (e.g., JSON or SVG path data) that allows for exact comparison with user outputs.
