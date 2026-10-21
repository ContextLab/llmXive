# Feature Specification: llmXive follow-up: extending "$π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows"

**Feature Branch**: `001-intent-graph-proactive-eval`  
**Created**: 2026-08-01  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending "$π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Hori""

## User Scenarios & Testing

### User Story 1 - Construct and Serialize the Intent Graph (Priority: P1)

**Journey**: The researcher uploads the raw $\pi$-Bench interaction traces and the system automatically parses the dialogue history to infer latent user intents, constructing a directed "Intent Graph" where nodes represent intents and edges represent temporal or causal dependencies, finally serializing this structure into a JSON artifact for downstream consumption.

**Why this priority**: This is the foundational data transformation step. Without a valid, structured representation of the history, the lightweight agent cannot receive input, and the core hypothesis (that structure replaces raw nuance) cannot be tested. It is the prerequisite for all subsequent analysis.

**Independent Test**: The system can be tested by running the graph construction script on a single $\pi$-Bench task file and verifying that the output JSON contains a valid directed graph structure (nodes with intent labels, edges with dependency types) that maps 1:1 to the ground‑truth hidden intents **for tasks that have ground‑truth annotations** (see US‑1), regardless of whether the agent runs.

**Acceptance Scenarios**:

1. **Given** a raw $\pi$-Bench task file containing 20 turns of dialogue, **When** the graph construction module processes it, **Then** the output JSON must contain a node for every inferred latent intent and edges connecting them in temporal order, with no orphaned nodes.
2. **Given** a raw dialogue where the user explicitly states a goal, **When** the parser processes the text, **Then** the resulting graph node must correctly label the intent as "Explicit Goal" rather than "Implicit" or "Null".
3. **Given** a complex dialogue with multiple conflicting intents, **When** the graph is constructed, **Then** the edge topology must include an edge from a node labeled "Conflict Detected" to a node labeled "Resolution Strategy" (the defined conflict‑resolution pattern).

---

### User Story 2 - Execute Lightweight Agent via Intent Graph (Priority: P2)

**Journey**: The researcher runs the lightweight, CPU‑tractable agent (e.g., a modest‑size parameter model or rule‑based engine) on the full dataset, providing *only* the constructed Intent Graph and the current prompt as context, and the system records the agent's proactive action selections for every turn.

**Why this priority**: This tests the core hypothesis. If the agent cannot operate using *only* the graph, the experiment fails immediately. This step isolates the "structured memory" variable from the "raw history" variable.

**Independent Test**: The system can be tested by running the agent on a single task with the Intent Graph input and verifying that the agent outputs a proactive action selection (or a "no_action" signal) within a defined time limit, without crashing due to context window overflows or missing data.

**Acceptance Scenarios**:

1. **Given** a valid Intent Graph JSON and the current user prompt for Turn 15, **When** the lightweight agent processes them, **Then** the agent must output a specific proactive action (e.g., "suggest_calendar_event") or a null response within 60 seconds.
2. **Given** an Intent Graph with no active latent intents, **When** the agent processes the input, **Then** the agent must output "no_action" rather than hallucinating a proactive intervention.
3. **Given** a task where the graph indicates a high‑confidence latent intent, **When** the agent processes the input, **Then** the agent must select an action that matches the ground‑truth expected action label for that turn in ≥ 50 % of the three random‑seed runs.

---

### User Story 3 - Quantitative Comparison and Statistical Validation (Priority: P3)

**Journey**: The researcher triggers the analysis pipeline to compare the F1‑scores of the lightweight agent (Intent Graph) against the baseline (Raw History) and the null condition (No History), performing appropriate statistical tests to determine significance and calculating the latency reduction.

**Why this priority**: This delivers the scientific result. It transforms raw execution logs into the answer to the research question: “Does the graph enable parity (or superiority) with respect to raw history, and is any history necessary at all?” It also validates the compute feasibility (latency).

**Independent Test**: The system can be tested by feeding a pre‑computed set of results (mock data) into the analysis module and verifying that it correctly calculates the F1‑score differences, performs the specified statistical tests on per‑task mean scores, and outputs a report with p‑values and latency statistics.

**Acceptance Scenarios**:

1. **Given** the action logs from the Lightweight Agent, the Raw‑History baseline, and the No‑History baseline, **When** the analysis module runs, **Then** it must calculate the F1‑score for proactive action selection for each condition and output the pairwise differences.
2. **Given** a set of 100 paired results (Graph vs. Raw, and Graph vs. Null), **When** the statistical test runs, **Then** it must perform a Wilcoxon signed‑rank test on the per‑task mean F1 scores (averaged over three random seeds) as the primary significance test and report a p‑value < 0.05; a paired *t*‑test shall be run as a secondary check, and 95 % bootstrap confidence intervals for the mean difference shall be reported.
3. **Given** the inference timestamps for all three conditions, **When** the latency analysis runs, **Then** it must report the average inference time per turn for each condition and the percentage reduction of the Graph agent relative to both baselines.

---

### Edge Cases

- **What happens when the graph construction fails to identify any intents?** The system must log a "Null Graph" error for that specific task, exclude it from the statistical pairing, and flag it for manual review in the "Ambiguous Cases" report.
- **How does the system handle a task where the raw history is too large for the baseline model's context window?** The system must truncate the history to the maximum supported window (e.g., 8 k tokens) *before* baseline execution, and explicitly record this truncation in the metadata to ensure the comparison remains fair (i.e., comparing "Graph" vs. "Truncated Raw", not "Graph" vs. "Full Raw").
- **What if the lightweight agent produces non‑deterministic results across runs?** The system must run each task three times with different random seeds and report the mean F1‑score and standard deviation, ensuring the statistical test accounts for variance.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST parse raw $\pi$-Bench interaction traces to extract dialogue turns and ground‑truth hidden intents, storing them in a normalized internal format (See US-1).
- **FR-002**: The system MUST construct a directed "Intent Graph" where nodes represent inferred intents and edges represent temporal/causal dependencies, outputting a valid JSON artifact (See US-1).
- **FR-003**: The system MUST execute a lightweight, CPU‑tractable agent using *only* the Intent Graph and current prompt as input, recording the proactive action selection for every turn (See US-2).
- **FR-004**: The system MUST execute the baseline $\pi$-Bench evaluation script using the full (or truncated‑to‑limit) raw conversation history as context for the reference model (See US-2).
- **FR-005**: The system MUST calculate the F1‑score for proactive action selection for both the lightweight agent and the baseline, compute per‑task mean F1 scores averaged over three random seeds, and perform a Wilcoxon signed‑rank test (primary) and a paired *t*‑test (secondary) to assess significance (p < 0.05); 95 % bootstrap confidence intervals for the mean difference shall also be reported (See US-3).
- **FR-006**: The system MUST record inference time per turn for both the graph‑based agent and the baseline to quantify latency reduction (See US-3).
- **FR-007**: For any task where the dataset lacks an explicit ground‑truth latent‑intent annotation, the system MUST infer intents using a deterministic LLM prompt (fixed seed), label such nodes as "Inferred (unverified)", and record confidence scores. Nodes with confidence ≥ 0.8 are included in the **inferred subset**, which is the primary analysis set where graph construction is independent of scoring labels. Tasks with no confident inference are logged as "Null Graph" errors and excluded from statistical pairing. The analysis MUST also report a secondary validation on the ground‑truth‑annotated subset where available (See US-1).
- **FR-008**: The system MUST execute a null‑history baseline where the agent receives no prior conversation context (empty history) and only the current prompt, recording proactive action selections for each turn. (See US-3).
- **FR-009**: For the experimental condition (Graph agent), graph construction MUST be performed **without** using ground‑truth hidden‑intent labels; ground‑truth may be used only for downstream scoring. (See US-2).

### Key Entities

- **InteractionTrace**: A sequence of dialogue turns from a $\pi$-Bench task, including user prompts, agent responses, and ground‑truth hidden intent labels.
- **IntentGraph**: A directed graph structure (JSON) where nodes are intents (with type and confidence) and edges are dependencies (temporal or causal).
- **ProactiveAction**: The output of an agent indicating a proactive intervention (e.g., "suggest", "remind") or a null decision.
- **EvaluationResult**: A record containing the F1‑score, latency, and statistical test results for a specific agent configuration on a specific task.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The F1‑score of the lightweight agent (Intent Graph) must be ≤ 10 % lower than the Raw‑History baseline **and** must be at least 10 % higher than the No‑History baseline (See FR‑005, US‑3).
- **SC-002**: The inference latency per turn for the lightweight agent must be lower than the baseline latency, and the percentage reduction must be reported (See FR‑006, US‑3).
- **SC-003**: The statistical significance of each pairwise performance difference (Graph vs. Raw, Graph vs. Null) is measured via a Wilcoxon signed‑rank test on per‑task mean F1 scores (averaged over three seeds) with p < 0.05 as the primary test; a paired *t*‑test shall be reported as a secondary check, and 95 % bootstrap confidence intervals shall be included (See FR‑005, US‑3).
- **SC-004**: The graph construction success rate is measured against the total number of tasks (target ≥ 95 % valid graphs generated) (See FR‑002, US‑1).
- **SC-005**: Reproducibility is measured by running each task three times with different random seeds, reporting the standard deviation of per‑task mean F1 scores across tasks, and additionally reporting seed‑level variance to ensure stability of the results (See FR‑003, US‑2).

## Assumptions

- The $\pi$-Bench dataset (≈ 100 tasks) **may** contain explicit ground‑truth annotations for hidden intents for many tasks, but some tasks can lack these annotations; FR‑007 provides a fallback inference mechanism for such cases.
- The lightweight agent model can be loaded and run on a standard GitHub Actions free‑tier runner (multiple CPUs, 7 GB RAM) without GPU acceleration or quantization requiring CUDA.
- The "Raw History" baseline will be truncated to the maximum context window supported by the reference model if the original dialogue exceeds this limit, ensuring the comparison is between "Graph" and "Max‑Context Raw".
- The statistical power of the paired tests is considered sufficient with N ≈ 100 tasks to detect a medium effect size; if the observed effect is smaller, the limitation will be reported.
- The graph construction algorithm (intent inference) is deterministic via fixed random seeds to ensure reproducible graph structures for the same input dialogue.