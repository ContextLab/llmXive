# Feature Specification: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Feature Branch**: `001-llmxive-scaffold-analysis`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re'"

## User Scenarios & Testing

### User Story 1 - Scaffolded Protocol Injection (Priority: P1)

The system must load 10 specific tasks from the ResearchClawBench dataset previously flagged for "experimental protocol mismatch" and inject domain-specific procedural templates from a fixed, curated set into the agent's system prompt before execution.

**Why this priority**: This is the core experimental intervention. Without the ability to inject scaffolds, the study cannot distinguish between retrieval and reasoning deficits. It is the primary variable manipulation.

**Independent Test**: Can be fully tested by running a single agent on a single scaffolded task and verifying the system prompt contains the injected template (matching a specific ID from the Curated Template Set v1.0) and the agent executes the task steps.

**Acceptance Scenarios**:

1. **Given** a task from the ResearchClawBench dataset flagged for protocol mismatch, **When** the system prepares the execution context, **Then** the system MUST append the curated domain-specific protocol template (identified by a fixed ID from the Curated Template Set v1.0) to the system prompt without altering the task description.
2. **Given** an autonomous agent configured for the task, **When** the agent receives the scaffolded prompt, **Then** the agent MUST generate a plan that explicitly references the injected procedural steps (e.g., "Step 3: Purification as per template").
3. **Given** a task with a missing or invalid template ID, **When** the system attempts to inject the scaffold, **Then** the system MUST log a specific error and abort the run for that task, preventing silent degradation.

---

### User Story 2 - Dual-Condition Execution & Scoring (Priority: P2)

The system must execute the same agent on the same tasks under two conditions (Zero-Shot and Scaffolded) and apply the original expert-curated multimodal rubrics (loaded from a JSON schema) to extract "Protocol Alignment" and "Scientific Core" sub-scores for both.

**Why this priority**: This enables the comparative analysis required to answer the research question. It ensures data integrity by applying the exact same scoring logic to both conditions.

**Independent Test**: Can be fully tested by running the evaluation script on a saved log of a completed task and verifying that two distinct score objects (Zero-Shot and Scaffolded) are generated with the correct sub-metrics populated using the loaded rubric schema.

**Acceptance Scenarios**:

1. **Given** a completed run of an agent on a Zero-Shot task, **When** the scoring module processes the output, **Then** it MUST extract the "Protocol Alignment" score (0-50) and "Scientific Core" score based on the `rubric_schema.json` definitions.
2. **Given** a completed run of the same agent on the corresponding Scaffolded task, **When** the scoring module processes the output, **Then** it MUST extract the same metrics using the identical rubric schema to ensure comparability.
3. **Given** a pair of runs (Zero-Shot and Scaffolded) for a single task, **When** the results are aggregated, **Then** the system MUST store them as a paired dataset entry linked by the original task ID.

---

### User Story 3 - Statistical Decoupling Analysis (Priority: P3)

The system must perform a Two One-Sided Tests (TOST) equivalence test on the "Scientific Core" scores to establish a safety bound (not a validation) of independence, with an equivalence margin of 5 points. For "Protocol Alignment", the system MUST perform a paired t-test or Wilcoxon signed-rank test and report the effect size and 95% confidence intervals.

**Why this priority**: This is the final analytical step that produces the research conclusion. It validates the hypothesis that scaffolding addresses protocol issues while quantifying the risk to scientific reasoning using a statistically valid framework for non-inferiority claims, acknowledging the statistical power limits of N=10.

**Independent Test**: Can be fully tested by feeding a synthetic CSV of paired scores into the analysis module and verifying the output includes the equivalence test results (TOST p-values), p-value, test statistic, effect size (Cohen's d or r), and 95% confidence intervals for both metrics.

**Acceptance Scenarios**:

1. **Given** a dataset of paired "Protocol Alignment" scores (Zero-Shot vs. Scaffolded), **When** the analysis module runs, **Then** it MUST perform a normality check and select either a paired t-test or Wilcoxon signed-rank test accordingly.
2. **Given** the statistical test results, **When** the system evaluates the "Scientific Core" scores, **Then** it MUST perform a TOST equivalence test with an equivalence margin of 5 points. The result is interpreted as "safe" only if both p-values are < 0.05; otherwise, it is flagged as "inconclusive".
3. **Given** a failure in the statistical assumptions (e.g., insufficient data points), **When** the analysis runs, **Then** it MUST output a warning regarding the low statistical power (<0.4 for N=10) and report the result as "inconclusive" rather than "validated".

---

### Edge Cases

- What happens if the selected ResearchClawBench tasks do not have "experimental protocol mismatch" as the dominant failure mode? (System MUST filter and report the actual dominant mode by writing a CSV report to `results/failure_mode_audit.csv` containing the task ID and the detected mode).
- How does the system handle a scenario where the injected scaffold contradicts the specific constraints of a task? (System MUST log a "Scaffold Conflict" warning, exclude the run from the primary analysis, and record the audit ID for the human expert validation required by FR-007, specifically referencing the Curated Template Set v1.0).
- How does the system handle agent timeouts exceeding the 6-hour limit on the CPU runner? (System MUST record a "Timeout" status and exclude the score from the statistical calculation).

## Requirements

### Functional Requirements

- **FR-001**: System MUST load exactly 10 tasks from the ResearchClawBench dataset that are pre-flagged for "experimental protocol mismatch" and retrieve the corresponding domain-specific protocol template from the fixed "Curated Template Set v1.0" (stored in `assets/templates/`) for each. (See US-1)
- **FR-002**: System MUST append the retrieved protocol template to the system prompt of the agent without modifying the original task description or hidden target paper content. (See US-1)
- **FR-003**: System MUST execute all autonomous agents from the original study on both the original Zero-Shot tasks and the new Scaffolded tasks (totaling execution runs across all agents, conditions, and tasks) with a strict time limit per run, utilizing a concurrency limit of, within a total wall-clock time budget of 24 hours on a GitHub Actions `ubuntu-latest` runner (2-core, 7GB RAM). (See US-2)
- **FR-004**: System MUST load the scoring logic from `rubric_schema.json` and apply it to extract "Protocol Alignment" (0-50) and "Scientific Core" sub-scores for every completed run in both conditions. (See US-2)
- **FR-005**: System MUST perform a paired statistical test (t-test or Wilcoxon signed-rank) on the "Protocol Alignment" scores and perform a Two One-Sided Tests (TOST) equivalence test with an equivalence margin of 5 points on the "Scientific Core" scores to establish a safety bound. (See US-3)
- **FR-006**: System MUST abort the experiment, log a critical error to `stderr`, and exit with code 1 if the ResearchClawBench dataset lacks the specific "protocol mismatch" metadata required to select the 10 tasks. (See US-1)
- **FR-007**: System MUST detect when an injected scaffold contradicts the specific constraints of a task by validating the task metadata against a defined `constraint_keywords` list in the template schema; if a conflict is detected, the system MUST log a "Scaffold Conflict" warning, exclude the run from the primary analysis, and record the run ID for a mandatory human expert audit of a random [deferred] sample of conflict decisions. (See US-1)
- **FR-008**: System MUST include a validation step that scores two distinct sets of dummy outputs: Set A (contains scaffold text but fails protocol steps) and Set B (contains protocol steps but no scaffold text). The system MUST verify that the `rubric_schema.json` scores Set B high and Set A low, confirming the rubric scores steps, not text. (See US-3)

### Key Entities

- **Task Instance**: A specific experimental task from ResearchClawBench, containing the task description, hidden target paper, and metadata regarding failure modes.
- **Protocol Scaffold**: A static, domain-specific procedural template derived from open-access laboratory manuals, stored in `assets/templates/` and identified by a versioned ID (e.g., `TEMPLATE-001-v1.0`).
- **Execution Log**: The complete trace of an agent's interaction with the environment, including prompts, actions, and final output.
- **Score Pair**: A data structure linking the Zero-Shot and Scaffolded scores for a single task instance, containing "Protocol Alignment" and "Scientific Core" values.
- **Rubric Schema**: A JSON file (`rubric_schema.json`) defining the scoring logic, weights, and multimodal input formats for the "Protocol Alignment" and "Scientific Core" metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The increase in "Protocol Alignment" scores between Zero-Shot and Scaffolded conditions is measured against the baseline performance reported in the original ResearchClawBench study. (See FR-005)
- **SC-002**: The statistical significance of the "Protocol Alignment" improvement is measured against a standard alpha threshold of 0.05 using the selected paired test. (See FR-005)
- **SC-003**: The stability of "Scientific Core" scores is measured against the Zero-Shot baseline by reporting the 95% confidence interval of the mean difference; a "safe" result is defined as the TOST test showing equivalence within a margin of 5 points. (See FR-005, FR-008)
- **SC-004**: The computational feasibility is measured against the constraint that ≥ 95% of the 140 execution runs (7 agents × 2 conditions × 10 tasks) complete successfully within the total wall-clock time budget of 24 hours on a GitHub Actions `ubuntu-latest` runner (2-core, 7GB RAM). (See FR-003)
- **SC-005**: The dataset-variable fit is measured by verifying that the ResearchClawBench metadata contains the specific "protocol mismatch" flag required for task selection. (See FR-006)

## Assumptions

- The ResearchClawBench dataset (arXiv:2606.07591) contains a metadata field or error log that explicitly identifies "experimental protocol mismatch" as the dominant failure mode for at least 10 tasks.
- The seven autonomous agents from the original study can be instantiated and executed on a GitHub Actions `ubuntu-latest` runner (multi-core, standard RAM) without requiring GPU acceleration or extreme quantization.
- The domain-specific protocol templates are static, curated artifacts from open-access laboratory manuals, stored in `assets/templates/`, and do not require generation at runtime.
- The "Scientific Core" rubric, as defined in `rubric_schema.json`, is robust enough to score both Zero-Shot and Scaffolded outputs without penalizing the presence of the scaffold text (validated by FR-008).
- The statistical power of the test is low (<0.4) with N=10 paired observations for detecting moderate effect sizes; therefore, non-significant results for "Scientific Core" are interpreted as "inconclusive" or a "safety bound" rather than a definitive validation of independence.
- The "Protocol Alignment" sub-score (0-50) is a valid and reliable metric for measuring procedural execution, independent of the agent's hypothesis generation capabilities.