# Feature Specification: llmXive follow-up: extending "ABot-AgentOS" with Symbolic Memory

**Feature Branch**: `001-symbolic-memory-edge-robotics`  
**Created**: 2026-09-04  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending ABot-AgentOS: A General Robotic Agent OS with Lifelong Multi-modal Mem - investigating the trade-off between computational efficiency and task success rates when replacing neural embedding-based memory with a purely symbolic, CPU-tractable knowledge base for long-horizon robotic navigation."

## User Scenarios & Testing

### User Story 1 - Symbolic Graph Construction from Task Traces (Priority: P1)

**Description**: The system must ingest raw task traces (dialogue, spatial coordinates, temporal sequences) from the EmbodiedWorldBench Logs and convert them into a deterministic, directed acyclic graph (DAG) of semantic tokens and logical predicates without requiring GPU inference during the construction phase. The system must support sweeping tokenization granularity (coarse vs. fine taxonomies) and predicate expressiveness (spatial-only vs. spatial+temporal) as independent variables.

**Why this priority**: This is the foundational step. Without a valid symbolic representation of the environment and task history, no retrieval or navigation can occur. It validates the core "offline discretization" and "graph construction" components of the methodology and enables the parametric study required by the research question.

**Independent Test**: The system can be tested by running the construction pipeline on a subset of task traces and verifying the output graph structure (nodes, edges, predicates) against ground-truth annotations from EmbodiedWorldBench via a manual audit of a random sample of traces. Success is defined by a graph reconstruction error rate < 1% against ground truth.

**Acceptance Scenarios**:

1. **Given** a raw task trace containing spatial coordinates and dialogue, **When** the offline discretization module processes it, **Then** the system outputs a DAG where nodes correspond to unique semantic tokens (e.g., "red_cup_kitchen_counter") and edges represent logical predicates (e.g., `on_top_of`, `near`), with a graph reconstruction error rate < 1% against ground truth.
2. **Given** a task trace with ambiguous visual data, **When** the system applies the frozen VLM mapping, **Then** the system assigns the token based on the pre-defined taxonomy and logs the mapping confidence for later error analysis.
3. **Given** 500 task traces, **When** the graph construction completes, **Then** the total memory footprint of the constructed graph structure in RAM is ≤ 2 GB.

---

### User Story 2 - Deterministic Symbolic Query Execution (Priority: P2)

**Description**: The system must execute memory queries using a depth-first traversal algorithm on the symbolic graph to retrieve relevant context for navigation decisions, ensuring zero GPU dependency and deterministic results.

**Why this priority**: This implements the core "query engine" and "task simulation" steps. It demonstrates that the symbolic substrate can actively drive agent behavior and retrieve information efficiently on CPU.

**Independent Test**: The system can be tested by issuing a series of standard navigation queries (e.g., "Where is the red cup?") against the constructed graph and verifying the returned path/context matches the ground truth in the source logs within a defined latency budget.

**Acceptance Scenarios**:

1. **Given** a constructed symbolic graph and a navigation query, **When** the query engine executes a depth-first traversal, **Then** the system returns the relevant semantic tokens and predicates within 100 ms on a standard CPU.
2. **Given** a query that requires chaining multiple predicates (e.g., "Find object X near object Y which is before object Z"), **When** the engine performs logical inference, **Then** the system correctly identifies the target node (matching the path in the source log) or returns a "not found" status (returns null when no path exists in the DAG) without hallucinating a path.
3. **Given** a high-load scenario with a queue of 100 sequential queries, **When** the system processes them sequentially, **Then** the average latency remains ≤ 150 ms and no GPU resources are utilized.

---

### User Story 3 - Comparative Performance & Success Rate Analysis (Priority: P3)

**Description**: The system must run a comparative experiment executing the same set of logic-heavy navigation tasks using both the new symbolic memory system and the baseline neural memory system (ABot-AgentOS v1.0), recording success rates, latency, and memory usage to generate statistical evidence. The experiment must sweep tokenization granularity and predicate expressiveness as independent variables.

**Why this priority**: This addresses the primary research question regarding the trade-off between efficiency and success. It is the final validation step that produces the publishable results (success rate within 5%, memory reduction >80%) and validates the parametric study.

**Independent Test**: The system can be tested by running the simulation on a fixed subset of tasks, collecting the metrics, and generating a report that compares the symbolic baseline against the neural baseline (ABot-AgentOS v1.0). Success is defined by the system outputting the correct statistical metrics (p-value, t-statistic/McNemar statistic) and error categorization.

**Acceptance Scenarios**:

1. **Given** a set of 100 logic-heavy navigation tasks, **When** both the symbolic and neural systems execute the tasks, **Then** the system records the success rate, peak RAM usage, and query latency for each task.
2. **Given** the collected metrics, **When** the statistical comparison module runs, **Then** it outputs the p-value and the test statistic (McNemar's test for binary outcomes) for the paired comparison, allowing verification of the calculation.
3. **Given** the failure cases in the symbolic system, **When** the error analysis module runs, **Then** it categorizes errors into "discretization ambiguity" or "logical inference limitations" with a count for each category.

---

### Edge Cases

- **What happens when** the frozen VLM mapping fails to find a match for a visual observation in the pre-defined taxonomy? The system must default to a generic "unknown_object" token and log the event for the error analysis phase, rather than crashing or hallucinating a new token.
- **How does the system handle** a task trace with contradictory spatial information (e.g., "Object A is near Object B" and "Object A is far from Object B")? The system must detect the logical inconsistency during graph construction and flag the edge for review, rather than creating a cyclic or invalid graph structure.
- **What happens when** the dataset contains a variable required for the analysis (e.g., specific environmental noise levels) that is not present in the standard EmbodiedWorldBench logs? The system MUST record a warning log if a required variable for the analysis is missing from the standard EmbodiedWorldBench logs, and proceed with the analysis using only the available features while documenting the missing variable as a limitation in the final report.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest task traces from the EmbodiedWorldBench Logs and extract dialogue, spatial coordinates, and temporal sequences for processing (See US-1).
- **FR-002**: System MUST map raw visual observations to a fixed taxonomy of semantic tokens using a frozen, pre-trained VLM in offline mode, storing mappings in a lookup table (See US-1).
- **FR-003**: System MUST construct a directed acyclic graph (DAG) where nodes represent discrete semantic tokens and edges represent logical predicates (e.g., `on_top_of`, `near`, `before`) (See US-1).
- **FR-004**: System MUST execute memory queries using a deterministic, depth-first graph traversal algorithm that operates entirely on CPU without GPU acceleration (See US-2).
- **FR-005**: System MUST measure and record task success rates (against ground-truth task outcome in EmbodiedWorldBench), retrieval latency (ms), and peak CPU memory usage (RAM) for both the symbolic and neural baseline systems (ABot-AgentOS v1.0) across the same task set (See US-3).
- **FR-006**: System MUST perform McNemar's test to compare the binary success/failure outcomes between the symbolic and neural baselines to determine statistical significance (See US-3).
- **FR-007**: System MUST categorize and report failure cases in the symbolic system as either "discretization ambiguity" or "logical inference limitations" (See US-3).
- **FR-008**: System MUST support sweeping the granularity of semantic tokenization (e.g., coarse vs. fine taxonomies) and measure the impact on performance metrics (See US-1, US-3).
- **FR-009**: System MUST support sweeping the expressiveness of logical predicates (e.g., spatial-only vs. spatial+temporal) and measure the impact on performance metrics (See US-1, US-3).

### Key Entities

- **Task Trace**: A record containing dialogue, spatial coordinates, and temporal sequences from a specific navigation task in EmbodiedWorldBench.
- **EmbodiedWorldBench Logs**: The raw data artifact containing task traces, including dialogue, spatial coordinates, and temporal sequences, used as input for the system.
- **Semantic Token**: A discrete string identifier (e.g., "red_cup_kitchen_counter") representing a mapped visual or spatial state.
- **Symbolic Graph**: A directed acyclic graph (DAG) where nodes are semantic tokens and edges are logical predicates.
- **Performance Metric**: A data point capturing success rate, latency, or memory usage for a specific task execution.
- **Neural Baseline**: The ABot-AgentOS v1.0 implementation using embedding-based retrieval, executed on GPU for latency measurements and with pre-computed embeddings for memory usage measurements.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Task success rate for the symbolic system is measured against the neural baseline system (ABot-AgentOS v1.0), with a target difference of ≤ 5% (See US-3).
- **SC-002**: Memory footprint (RAM) of the symbolic system is measured against the neural baseline system (ABot-AgentOS v1.0), with a target reduction of ≥ 80% (See US-3).
- **SC-003**: Query latency (ms) for the symbolic system is measured against the neural baseline system (ABot-AgentOS v1.0, GPU-accelerated), with a target of ≤ 100 ms per query on CPU (See US-2).
- **SC-004**: Statistical significance of the success rate difference is measured against the threshold p > 0.05 using McNemar's test (See US-3).
- **SC-005**: Error analysis coverage is measured as the percentage of symbolic system failures categorized into "discretization ambiguity" or "logical inference limitations" (See US-3).

## Assumptions

- **Assumption about data**: The public EmbodiedWorldBench Logs contain sufficient spatial and temporal information to reconstruct the necessary logical predicates for navigation tasks; if specific variables (e.g., fine-grained texture data) are missing, the analysis will proceed with available features and note the limitation.
- **Assumption about compute**: The entire analysis pipeline (discretization, graph construction, query execution, and statistical comparison) will run within the GitHub Actions free-tier limits using sampled data and CPU-tractable methods.
- **Assumption about methodology**: The frozen VLM used for offline discretization is sufficiently accurate to map raw observations to the fixed taxonomy with minimal error, such that discretization ambiguity does not dominate the failure mode; if errors are high, the sensitivity analysis will sweep the confidence threshold.
- **Assumption about baseline**: The neural baseline implementation (ABot-AgentOS v1.0) will be executed on GPU for latency measurements to ensure the comparison measures memory efficiency rather than hardware capability; for memory usage measurements, pre-computed embeddings will be used to isolate the memory component.
- **Assumption about inference framing**: Since the study compares two system architectures on the same observational dataset without random assignment of agents to architectures, all findings regarding performance differences are framed as ASSOCIATIONAL, not causal, unless the experimental design explicitly includes randomization of task ordering or agent initialization.