# Feature Specification: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthetic Dataset and Skill Library Generation (Priority: P1)

The researcher needs to generate a reproducible synthetic environment containing 500 multi-step tasks and a configurable library of 100 overlapping Python "skills" with controlled semantic density to serve as the ground truth for the experiment.

**Why this priority**: Without a deterministic, ground-truth dataset and a controllable skill library, no empirical measurement of retrieval fidelity or task success can occur. This is the foundational data layer required for all subsequent analysis.

**Independent Test**: The system can be fully tested by executing the data generation script and verifying that the output files (tasks.json, skills.json) contain the expected number of records, valid JSON structure, and that the ground-truth solution paths are distinct from the retrieval logic.

**Acceptance Scenarios**:

1. **Given** the researcher specifies a target library size of 100 and overlap level of "high", **When** the generation script runs, **Then** the output contains exactly 100 skills with embedding vectors that reflect the specified semantic density.
2. **Given** the generation script completes, **When** the researcher inspects the task file, **Then** every task includes a unique ground-truth solution path consisting of 3-5 deterministic actions.
3. **Given** the synthetic data is generated, **When** the researcher queries the library for a specific task, **Then** the system returns the correct ground-truth skills, confirming the data integrity.

---

### User Story 2 - Agent Execution and Metric Collection (Priority: P2)

The researcher needs to run the minimalistic "Digital Colleague" agent across varying library sizes (10, 30, 50, 100) and record task completion rates, token usage, and latency for each configuration.

**Why this priority**: This is the core experimental loop. It generates the raw data required to test the hypothesis regarding the "tipping point" of retrieval noise.

**Independent Test**: The system can be tested by running the agent against a fixed subset of tasks with a specific library size and verifying that a metrics log is produced containing latency, token counts, and success/failure flags for every run.

**Acceptance Scenarios**:

1. **Given** a library of 50 skills and a task set of 500, **When** the agent executes, **Then** the system logs the completion status (success/fail) and latency for every single task.
2. **Given** the agent encounters a retrieval failure, **When** it attempts to execute the task, **Then** the system records the failure and the specific retrieval noise metrics (e.g., top-k embedding variance).
3. **Given** the experiment completes, **When** the researcher aggregates the logs, **Then** they can calculate the task success rate and average latency for the 50-skill configuration.

---

### User Story 3 - Pruning Heuristic and Threshold Analysis (Priority: P3)

The researcher needs to apply a "Skill Pruning" heuristic to the active library after every 10 tasks and perform statistical analysis to determine if the pruning mitigates performance degradation caused by library growth.

**Why this priority**: This addresses the "intervention" part of the research question, testing whether active curation can restore efficiency, which is critical for the "Digital Colleague" viability argument.

**Independent Test**: The system can be tested by running the agent with the pruning heuristic enabled on a large library (100 skills) and comparing the resulting success rates against the non-pruned baseline to verify the improvement metric.

**Acceptance Scenarios**:

1. **Given** the agent has processed 10 tasks with a 100-skill library, **When** the pruning heuristic triggers, **Then** the active library size decreases based on usage frequency and embedding distance.
2. **Given** the pruning heuristic is active, **When** the agent continues to process tasks, **Then** the recorded latency and token usage are lower than the non-pruned baseline for the same library size.
3. **Given** the full experiment data is collected, **When** the statistical analysis runs, **Then** the system outputs a p-value indicating whether the performance recovery from pruning is statistically significant.

---

### Edge Cases

- What happens when the semantic overlap is set to "maximal" (defined as mean pairwise cosine similarity ≥ 0.95)? The system must handle the resulting tie-breaking in retrieval without crashing and report the Retrieval Precision (Jaccard similarity to ground truth) as zero if no ground-truth skills are retrieved.
- How does the system handle a task that requires a skill not present in the library? The agent must fail gracefully, log the specific missing skill requirement, and not attempt to hallucinate a solution.
- What happens if the CPU memory limit is approached during the embedding calculation for the largest library? The system must detect memory pressure and either sample the dataset or fail with a clear "Memory Limit Exceeded" error rather than a silent crash.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a synthetic dataset of exactly 500 multi-step tasks, where each task has a unique ground-truth solution path independent of the retrieval mechanism (See US-1).
- **FR-002**: System MUST construct a skill library of 100 Python functions with configurable semantic overlap (low, medium, high) to simulate varying degrees of redundancy (See US-1).
  - **Low**: Mean pairwise cosine similarity < 0.30.
  - **Medium**: Mean pairwise cosine similarity > 0.50 AND at least 30% of all pairs exceed 0.50.
  - **High**: Mean pairwise cosine similarity > 0.80 AND at least 30% of all pairs exceed 0.80.
- **FR-003**: System MUST execute the agent against the task set for library sizes of 10, 30, 50, and 100, recording task completion rates, token usage, and latency for each run (See US-2).
- **FR-004**: System MUST implement a "Skill Pruning" heuristic that removes a skill if (usage_count == 0) AND (min_cosine_similarity_to_any_other_skill_in_library < 0.70) after every 10 tasks (See US-3).
- **FR-005**: System MUST perform Piecewise Linear Regression with a single breakpoint to identify the library size (x0) where task success rate significantly declines, and report the breakpoint value as the "tipping point" (See US-3).
- **FR-006**: System MUST calculate and report two metrics:
  1. **Retrieval Precision**: Jaccard similarity between the set of top-k (k=5) retrieved skills and the task's ground-truth skill set.
  2. **Retrieval Diversity**: The inverse of the variance of the cosine similarities of the top-k (k=5) retrieved skills against the task's ground-truth set (to distinguish noise from collapse). (See US-2).
- **FR-007**: System MUST report the Variance Inflation Factor (VIF) for the predictors "library size" and "total redundancy" in the final statistical model to confirm they are not collinear (See US-3).

### Key Entities

- **Task**: A synthetic multi-step problem requiring 3-5 deterministic actions, containing a ground-truth solution path.
- **Skill**: A Python function with an associated embedding vector and usage metadata, representing a capability in the library.
- **Agent**: The execution engine that retrieves skills, executes them, and logs performance metrics.
- **ExperimentRun**: A record of a single configuration (library size, overlap level, pruning enabled/disabled) and its aggregate results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Task success rate is measured against the ground-truth solution path validity (See US-2, FR-003).
- **SC-002**: Retrieval fidelity is measured against the Retrieval Precision (Jaccard similarity to ground truth) of the top-k (k=5) retrieved skills (See US-2, FR-006).
- **SC-003**: Performance recovery from pruning is measured against the non-pruned baseline for the same library size (See US-3, FR-004).
- **SC-004**: The "tipping point" threshold is measured against the breakpoint parameter (x0) of the Piecewise Linear Regression model (See US-3, FR-005).
- **SC-005**: Compute feasibility is measured against the 6-hour CI job limit and 7 GB RAM constraint (See US-1, FR-001).
- **SC-006**: Predictor collinearity is measured against the Variance Inflation Factor (VIF) reported in FR-007, requiring VIF < 5.0 for valid interpretation (See US-3, FR-007).

## Assumptions

- **Dataset-variable fit**: The synthetic data generation process is assumed to fully contain all necessary variables (task complexity, skill overlap, ground-truth paths) required for the analysis, as the data is constructed programmatically rather than sourced from an external repository.
- **Inference framing**: Since the study uses a synthetic, deterministic environment with random assignment of tasks to library configurations, findings regarding the "tipping point" of retrieval noise can be framed as causal within the bounds of the simulation, but generalization to real-world chaotic environments is associative.
- **Compute feasibility**: The entire analysis (data generation, agent execution, statistical analysis) is assumed to run within the GitHub Actions free-tier limits (limited CPU, 7 GB RAM, 6 hours) by using CPU-tractable methods (scikit-learn, standard cosine similarity) and avoiding GPU-dependent libraries or large model training.
- **Threshold justification**: The specific library sizes (10, 30, 50, 100) are selected as a standard geometric progression to detect non-monotonic trends, and the "pruning" threshold (every 10 tasks) is a defensible default for frequent curation; a sensitivity analysis sweeping these values over {5, 10, 20} tasks will be included to verify robustness.
- **Measurement validity**: The use of Python function embeddings via standard sentence-transformers (CPU version) is assumed to provide a valid proxy for "semantic overlap" in the context of deterministic code retrieval.
- **Predictor collinearity**: The analysis assumes that "library size" and "semantic overlap" are treated as distinct experimental factors; "overlap" is defined as a density parameter (mean pairwise cosine similarity) held constant across library sizes, while "total noise" scales with size. If they become definitionally correlated, the VIF diagnostic (FR-007) will flag the confound.