# Feature Specification: llmXive follow-up: extending "$π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows"

**Feature Branch**: `001-intent-graph-proactive-eval`  
**Created**: 2026-08-01  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending "$π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Hori""

## User Scenarios & Testing

### User Story 1 - Construct and Serialize the Intent Graph (Priority: P1)

**Journey**: The researcher uploads the raw $\pi$-Bench interaction traces and the system automatically parses the dialogue history to infer latent user intents, constructing a directed "Intent Graph" where nodes represent intents and edges represent causal or temporal dependencies, finally serializing this structure into a JSON artifact for downstream consumption.

**Why this priority**: This is the foundational data transformation step. Without a valid, structured representation of the history, the lightweight agent cannot receive input, and the core hypothesis (that structure replaces raw nuance) cannot be tested. It is the prerequisite for all subsequent analysis.

**Independent Test**: The system can be tested by running the graph construction script on a single $\pi$-Bench task file and verifying that the output JSON contains a valid directed graph structure (nodes with intent labels, edges with dependency types) that maps 1:1 to the ground-truth hidden intents in the source data, regardless of whether the agent runs.

**Acceptance Scenarios**:

1. **Given** a raw $\pi$-Bench task file containing 20 turns of dialogue, **When** the graph construction module processes it, **Then** the output JSON must contain a node for every inferred latent intent and edges connecting them in temporal order, with no orphaned nodes.
2. **Given** a raw dialogue where the user explicitly states a goal, **When** the parser processes the text, **Then** the resulting graph node must correctly label the intent as "Explicit Goal" rather than "Implicit" or "Null".
3. **Given** a complex dialogue with multiple conflicting intents, **When** the graph is constructed, **Then** the edge topology must reflect the causal resolution (e.g., an edge from "Conflict Detected" to "Resolution Strategy") as defined by the methodology.

---

### User Story 2 - Execute Lightweight Agent via Intent Graph (Priority: P2)

**Journey**: The researcher runs the lightweight, CPU-tractable agent (e.g., a 1B parameter model or rule-based engine) on the full dataset, providing *only* the constructed Intent Graph and the current prompt as context, and the system records the agent's proactive action selections for every turn.

**Why this priority**: This tests the core hypothesis. If the agent cannot operate using *only* the graph, the experiment fails immediately. This step isolates the "structured memory" variable from the "raw history" variable.

**Independent Test**: The system can be tested by running the agent on a single task with the Intent Graph input and verifying that the agent outputs a proactive action selection (or a "no action" signal) within a defined time limit, without crashing due to context window overflows or missing data.

**Acceptance Scenarios**:

1. **Given** a valid Intent Graph JSON and the current user prompt for Turn 15, **When** the lightweight agent processes them, **Then** the agent must output a specific proactive action (e.g., "suggest_calendar_event") or a null response within 60 seconds.
2. **Given** an Intent Graph with no active latent intents, **When** the agent processes the input, **Then** the agent must output "no_action" rather than hallucinating a proactive intervention.
3. **Given** a task where the graph indicates a high-confidence latent intent, **When** the agent processes the input, **Then** the agent must select an action that aligns with the inferred intent in ≥ 50% of the test runs (baseline sanity check).

---

### User Story 3 - Quantitative Comparison and Statistical Validation (Priority: P3)

**Journey**: The researcher triggers the analysis pipeline to compare the F1-scores of the lightweight agent (Intent Graph) against the baseline (Raw History) and the null condition (No History), performing a paired t-test to determine statistical significance and calculating the latency reduction.

**Why this priority**: This delivers the scientific result. It transforms raw execution logs into the answer to the research question: "Does the graph enable parity?" It also validates the compute feasibility (latency).

**Independent Test**: The system can be tested by feeding a pre-computed set of results (mock data) into the analysis module and verifying that it correctly calculates the F1-score difference, performs the t-test, and outputs a report with p-values and latency statistics.

**Acceptance Scenarios**:

1. **Given** the action logs from the Lightweight Agent and the Baseline Agent, **When** the analysis module runs, **Then** it must calculate the F1-score for proactive action selection for both conditions and output the difference.
2. **Given** a set of 100 paired results (Graph vs. Raw), **When** the statistical test runs, **Then** it must perform a paired t-test and report a p-value indicating significance (or lack thereof) at the α=0.05 level.
3. **Given** the execution timestamps for both agents, **When** the latency analysis runs, **Then** it must report the average inference time per turn for the Graph agent and the percentage reduction compared to the Raw History baseline.

---

### Edge Cases

- **What happens when the graph construction fails to identify any intents?** The system must log a "Null Graph" error for that specific task, exclude it from the statistical pairing, and flag it for manual review in the "Ambiguous Cases" report.
- **How does the system handle a task where the raw history is too large for the baseline model's context window?** The system must truncate the history to the maximum supported window (e.g., 8k tokens) *before* baseline execution, and explicitly record this truncation in the metadata to ensure the comparison remains fair (i.e., comparing "Graph" vs. "Truncated Raw", not "Graph" vs. "Full Raw").
- **What if the lightweight agent produces non-deterministic results across runs?** The system must run each task multiple times with different random seeds and report the mean F1-score and standard deviation, ensuring the statistical test accounts for variance.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse raw $\pi$-Bench interaction traces to extract dialogue turns and ground-truth hidden intents, storing them in a normalized internal format (See US-1).
- **FR-002**: The system MUST construct a directed "Intent Graph" where nodes represent inferred intents and edges represent temporal/causal dependencies, outputting a valid JSON artifact (See US-1).
- **FR-003**: The system MUST execute a lightweight, CPU-tractable agent using *only* the Intent Graph and current prompt as input, recording the proactive action selection for every turn (See US-2).
- **FR-004**: The system MUST execute the baseline $\pi$-Bench evaluation script using the full (or truncated-to-limit) raw conversation history as context for the reference model (See US-2).
- **FR-005**: The system MUST calculate the F1-score for proactive intent resolution for both the lightweight agent and the baseline, and perform a paired t-test to determine statistical significance (p < 0.05) (See US-3).
- **FR-006**: The system MUST record inference time per turn for both the graph-based agent and the baseline to quantify latency reduction (See US-3).
- **FR-007**: The system MUST handle cases where the dataset lacks specific variables required for graph construction by flagging `[NEEDS CLARIFICATION: does $\pi$-Bench dataset contain explicit 'latent intent' annotations for all 100 tasks?]` (See US-1).

### Key Entities

- **InteractionTrace**: A sequence of dialogue turns from a $\pi$-Bench task, including user prompts, agent responses, and ground-truth hidden intent labels.
- **IntentGraph**: A directed graph structure (JSON) where nodes are intents (with type and confidence) and edges are dependencies (temporal or causal).
- **ProactiveAction**: The output of an agent indicating a proactive intervention (e.g., "suggest", "remind") or a null decision.
- **EvaluationResult**: A record containing the F1-score, latency, and statistical test results for a specific agent configuration on a specific task.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The F1-score of the lightweight agent (Intent Graph) is measured against the F1-score of the baseline (Raw History) to determine if the difference is ≤ 10% (See FR-005, US-3).
- **SC-002**: The inference latency per turn for the lightweight agent is measured against the baseline latency to quantify the reduction in computational overhead (See FR-006, US-3).
- **SC-003**: The statistical significance of the performance difference is measured via a paired t-test with a p-value threshold of < 0.05 (See FR-005, US-3).
- **SC-004**: The graph construction success rate is measured against the total number of tasks (target ≥ 95% valid graphs generated) (See FR-002, US-1).
- **SC-005**: The reproducibility of the lightweight agent's output is measured by running each task 3 times and reporting the standard deviation of the F1-score (See FR-003, US-2).

## Assumptions

- The $\pi$-Bench dataset (100 tasks) contains explicit ground-truth annotations for "hidden intents" for every task, which are required to construct the validation graph; if not, the study scope is limited to tasks where these annotations exist.
- The lightweight agent model can be loaded and run on a standard GitHub Actions free-tier runner (2 CPU, 7 GB RAM) without GPU acceleration or quantization requiring CUDA.
- The "Raw History" baseline will be truncated to the maximum context window supported by the reference model if the original dialogue exceeds this limit, ensuring the comparison is between "Graph" and "Max-Context Raw".
- The statistical power of the paired t-test is sufficient with N=100 tasks to detect a [deferred] difference in F1-score; if the effect size is smaller, the study may be underpowered, which will be reported as a limitation.
- The graph construction algorithm (intent inference) is deterministic or can be made deterministic via fixed random seeds to ensure reproducible graph structures for the same input dialogue.
