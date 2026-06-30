# Feature Specification: AutoResearchClaw Reproduction & Validation

**Feature Branch**: `001-autoresearchclaw-repro`  
**Created**: 2025-05-23  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI Collaboration"

## User Scenarios & Testing

### User Story 1 - End-to-End Execution on CPU (Priority: P1)

The user (researcher) must be able to execute the vendored `AutoResearchClaw` codebase on a standard GitHub Actions free-tier runner (limited CPU and RAM resources, no GPU) to generate at least one complete research artifact (paper draft, data plot, or analysis report) without manual intervention beyond initial configuration.

**Why this priority**: This is the fundamental "reproduction" requirement. If the system cannot run on the target hardware (CPU-only, constrained RAM) or fails to produce *any* artifact, the project cannot validate the paper's core claims about autonomous research execution.

**Independent Test**: Execute the `evaluate.py` script or the primary CLI entry point with a minimal, pre-configured topic (e.g., a single biology topic `B01` or a synthetic test case) and verify the generation of a non-empty output file (PDF, JSON report, or PNG plot) within the 6-hour job limit.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner with the submodule cloned, **When** the user runs the validation script with a minimal topic manifest, **Then** the system completes the full research loop (hypothesis, execution, analysis) and outputs a valid artifact file.
2. **Given** the system encounters a code execution error during the loop, **When** the self-healing executor activates, **Then** the system attempts a fix (via the `Pivot`/`Refine` loop) and either resolves the error or logs a structured failure report without crashing the entire runner.

---

### User Story 2 - Human-in-the-Loop (HITL) Intervention Mode (Priority: P2)

The user must be able to simulate a human-in-the-loop intervention at a specific high-leverage decision point (e.g., hypothesis refinement or experimental design) and verify that the system incorporates this feedback into the subsequent research cycle.

**Why this priority**: The paper claims that "precise, targeted collaboration at high-leverage decision points consistently outperforms both full autonomy and exhaustive step-by-step oversight." Validating this specific mechanism requires a mode where the user can inject feedback and observe the system's reaction.

**Independent Test**: Configure the system to pause at a defined "intervention point" (e.g., after hypothesis generation), inject a specific JSON feedback payload (simulating human input), and verify that the next iteration of the research loop reflects this change in its output.

**Acceptance Scenarios**:

1. **Given** the system is configured in "HITL Mode" with a specific intervention trigger, **When** the system reaches the trigger point and pauses, **Then** it waits for external input (simulated via a pre-loaded JSON file) and proceeds with the modified plan.
2. **Given** a human feedback payload suggesting a change in the experimental variable, **When** the system resumes, **Then** the generated code and subsequent results explicitly reflect the modified variable, and the final report documents the human intervention.

---

### User Story 3 - Cross-Run Evolution & Error Memory (Priority: P3)

The user must be able to demonstrate that the system retains "memory" of a failure from a previous run and uses it to prevent the same error in a subsequent run on a similar topic.

**Why this priority**: This validates the "Self-Reinforcing" and "Cross-run evolution" mechanisms claimed in the abstract. It ensures the system isn't just a static pipeline but a learning agent that improves over time.

**Independent Test**: Run the system on a topic known to trigger a specific type of error (or simulate one), record the "lesson learned," then run the system on a similar topic and verify that the system avoids the previously failed approach.

**Acceptance Scenarios**:

1. **Given** a previous run that failed due to a specific library import error, **When** the system initiates a new run on a related topic, **Then** the system's initial plan explicitly avoids the previously failed pattern (e.g., by selecting an alternative library or method).
2. **Given** the system's evolution log, **When** the user inspects the log after a successful run, **Then** the log contains a structured entry linking the current success to a specific "lesson learned" from a prior failure.

---

### Edge Cases

- **What happens when** the system hits the 6-hour GitHub Actions timeout limit mid-execution? The system must gracefully halt and save the current state (checkpoint) to disk, allowing a potential restart or at least producing a partial report of progress.
- **How does the system handle** an LLM API call failure (timeout or rate limit) during the critical hypothesis generation phase? The system must implement a retry strategy (with a bounded number of attempts and exponential backoff) and, if all fail, log a structured error and skip to the next available topic or abort cleanly without corrupting the workspace.
- **What happens when** the generated code attempts to allocate more than 7 GB of RAM? The system must detect the OOM condition (or anticipate it via size estimation) and trigger a data sampling strategy (reducing dataset size) or a method fallback to a lighter-weight algorithm.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `AutoResearchClaw` research loop on a CPU-only environment (no GPU/CUDA dependencies) to complete at least one full research cycle (hypothesis → experiment → analysis → report) within 6 hours. (See US-1)
- **FR-002**: System MUST implement a self-healing executor that detects code execution errors, attempts a fix via the `Pivot`/`Refine` loop, and logs the error/fix attempt before proceeding or failing. (See US-1)
- **FR-003**: System MUST support a Human-in-the-Loop (HITL) mode where it pauses execution at configurable decision points and accepts external feedback (JSON) to modify the research plan. (See US-2)
- **FR-004**: System MUST maintain a persistent "evolution log" that records failures, lessons learned, and safeguards applied across separate research runs to prevent recurrence of the same errors. (See US-3)
- **FR-005**: System MUST validate that all generated artifacts (papers, plots, data) are non-empty and structurally valid before marking a research cycle as complete. (See US-1)
- **FR-006**: System MUST enforce a strict memory limit of 7 GB RAM per job, automatically triggering data sampling or method simplification if a task exceeds this threshold. (See US-1)

### Key Entities

- **ResearchCycle**: A single end-to-end execution of the autonomous research pipeline on a specific topic, containing the hypothesis, code, data, and final report.
- **InterventionEvent**: A structured record of a human feedback injection, including the trigger point, the feedback payload, and the resulting system action.
- **EvolutionLog**: A persistent data store (file or DB) containing the history of failures and the derived "lessons learned" used to update the system's strategy.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of research cycles that successfully produce a valid artifact (non-empty PDF/JSON/PNG) on a CPU-only runner is measured against the target of ≥ 80% for a set of 5 diverse topics. (See FR-001)
- **SC-002**: The average time from "hypothesis generation" to "final report" for a single research cycle is measured against the 6-hour job limit, ensuring ≤ 90% of the time budget is utilized. (See FR-001, FR-006)
- **SC-003**: The rate of successful error recovery (self-healing) is measured against the total number of code execution errors encountered, targeting ≥ 50% recovery without manual intervention. (See FR-002)
- **SC-004**: The effectiveness of HITL intervention is measured by comparing the quality score (rubric-based) of runs with intervention vs. runs without intervention, targeting a ≥ 10% improvement in the intervention runs. (See FR-003)
- **SC-005**: The recurrence rate of specific errors across runs is measured against the evolution log, targeting [deferred] recurrence for errors that have been logged as "resolved." (See FR-004)

## Assumptions

- **Assumption about data/environment**: The GitHub Actions free-tier runner (standard CPU allocation, 7 GB RAM, 14 GB disk) is sufficient to run the `AutoResearchClaw` codebase for at least one topic, provided that large model inference is avoided or sampled.
- **Assumption about scope boundaries**: The reproduction effort focuses on validating the *execution* and *mechanism* of the system (does it run? does it heal? does it learn?) rather than re-evaluating the scientific validity of the generated papers across all ARC-Bench topics.
- **Assumption about target users**: The primary "user" for this validation phase is the CI/CD pipeline and the researcher reviewing the logs, not an end-user interacting with a web UI.
- **Assumption about dependencies**: The system relies on the `aiming-lab/AutoResearchClaw` submodule being up-to-date and the `credentials.example.env` being correctly configured with valid (but potentially limited) API keys for LLM access, or a mock provider for testing.
- **Assumption about compute feasibility**: The "heavy" components of the original paper (e.g., training large models) are either not required for the reproduction of the *pipeline* or have been abstracted to use smaller, CPU-tractable models as per the "Compute feasibility" constraints.
