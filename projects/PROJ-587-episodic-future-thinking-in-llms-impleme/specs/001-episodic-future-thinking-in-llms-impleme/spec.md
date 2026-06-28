# Feature Specification: Episodic Future Thinking in LLMs: Implementing Mental Time Travel

**Feature Branch**: `001-episodic-future-thinking`  
**Created**: 2026-06-01  
**Status**: Draft  
**Input**: User description: "Do LLM architectures with explicit episodic memory modules enable more accurate future scenario simulation compared to standard transformers, and does this improvement generalize across planning tasks requiring episodic retrieval?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Episodic Memory Module Integration (Priority: P1)

The system MUST support storage and retrieval of episodic memories as (state, action, outcome) tuples with semantic embeddings during planning inference.

**Why this priority**: This is the foundational capability without which no future simulation is possible. It represents the core architectural difference from standard transformers and must be validated before any downstream planning claims.

**Independent Test**: Can be fully tested by recording 100 planning trajectories from ALFWorld/TextWorld environments, storing them in the episodic memory module, and verifying retrieval accuracy for [deferred] of stored episodes using semantic similarity search with cosine similarity ≥ 0.75.

**Acceptance Scenarios**:

1. **Given** a completed planning trajectory with 5 state-action-outcome steps, **When** the trajectory is stored in the episodic memory module, **Then** all 5 steps are retrievable with semantic similarity ≥ 0.75 within 2 seconds of query
2. **Given** 100 stored episodic trajectories, **When** a query matches 10 stored episodes semantically, **Then** the top-5 most relevant episodes are retrieved with precision ≥ 0.80 (See US-1)
3. **Given** an episodic memory store with ≥ 1000 entries, **When** a retrieval query is executed, **Then** response time ≤ 500ms on CPU-only execution (See US-1)

---

### User Story 2 - Future Scenario Simulation with Episodic Retrieval (Priority: P2)

The system MUST generate future planning scenarios by combining retrieved episodic memories with current state information to produce coherent multi-step plans.

**Why this priority**: This represents the actual "mental time travel" capability—using past episodes to construct novel future scenarios. It depends on US-1 working correctly but adds the generative simulation layer.

**Independent Test**: Can be fully tested by presenting the model with 50 held-out planning tasks requiring episodic retrieval, measuring plan accuracy against ground-truth solutions, and verifying ≥ 15% improvement over baseline transformer without episodic memory (effect size d ≥ 0.8 with α=0.05).

**Acceptance Scenarios**:

1. **Given** a novel planning scenario requiring retrieval of past episodic experience, **When** the episodic-memory-augmented model generates a plan, **Then** the plan achieves ≥ 15% higher accuracy than baseline transformer on the same task (See US-2)
2. **Given** 50 held-out planning tasks from ALFWorld/TextWorld benchmarks, **When** both baseline and episodic-memory models generate solutions, **Then** paired t-test shows statistically significant improvement (p < 0.05) with effect size d ≥ 0.8 (See US-2)
3. **Given** a planning task requiring combination of 2+ episodic memories, **When** the model constructs a future scenario, **Then** ≥ 80% of generated plans contain valid episodic references (See US-2)

---

### User Story 3 - Episodic vs Semantic Retrieval Validation Protocol (Priority: P3)

The system MUST include an evaluation protocol that distinguishes true episodic recollection from semantic pattern completion using counterfactual detail confidence measurement.

**Why this priority**: This addresses the critical methodological concern raised by reviewers (Kandel, Kahneman) about whether the system truly encodes specific events or merely retrieves statistical patterns. Without this validation, claims about episodic memory lack empirical support.

**Independent Test**: Can be fully tested by generating 100 future scenarios with embedded counterfactual details that could not be known from training data, measuring model confidence scores, and verifying the system flags ≥ 70% of unknown details with confidence ≤ 0.40.

**Acceptance Scenarios**:

1. **Given** 100 generated future scenarios with 5 counterfactual details each that are not in training data, **When** the evaluation protocol measures model confidence, **Then** ≥ 70% of unknown details receive confidence scores ≤ 0.40 (See US-3)
2. **Given** a set of 50 scenarios where episodic details are verifiable against stored memories, **When** the validation protocol runs, **Then** ≥ 85% of verifiable episodic details receive confidence scores ≥ 0.60 (See US-3)
3. **Given** 100 future scenario generations, **When** coherence is rated on 1-5 Likert scale by human evaluators, **Then** mean coherence score ≥ 3.5 with inter-rater reliability ≥ 0.75 (See US-3)

---

### Edge Cases

- What happens when the episodic memory store contains conflicting episodes for the same state-action pair? The system MUST flag conflicts and default to most recent episode unless confidence difference ≥ 0.15 between candidates.
- How does the system handle novel planning tasks with no matching episodic memories in the store? The system MUST fall back to baseline transformer planning and log the fallback event for analysis.
- What occurs when semantic similarity search returns ≤ 2 relevant episodes for a query requiring ≥ 3 for valid planning? The system MUST request additional context or report insufficient episodic retrieval with confidence ≤ 0.30.
- How does the system prevent WYSIATI bias when generating counterfactual details? The system MUST include explicit uncertainty markers for any detail not supported by retrieved episodic memories.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a neural episodic control module with key-value memory store compatible with transformer attention mechanisms, supporting ≥ 10,000 stored episodes with retrieval latency ≤ 500ms on CPU (See US-1)
- **FR-002**: System MUST store episodic trajectories as (state, action, outcome) tuples with semantic embeddings using cosine similarity ≥ 0.75 threshold for retrieval matching (See US-1)
- **FR-003**: System MUST generate future planning scenarios by combining retrieved episodic memories with current state information, requiring ≥ 1 episodic reference per multi-step plan (See US-2)
- **FR-004**: System MUST evaluate planning accuracy using paired comparison against baseline transformer across ≥ 50 held-out planning tasks with statistical significance testing at α=0.05 (See US-2)
- **FR-005**: System MUST implement validation protocol measuring confidence scores for counterfactual details, flagging unknown details with confidence ≤ 0.40 for ≥ 70% of test cases (See US-3)
- **FR-006**: System MUST perform sensitivity analysis on retrieval similarity threshold sweeping values ∈ {0.70, 0.75, 0.80} and report how retrieval precision varies across thresholds (See US-3)
- **FR-007**: System MUST execute all training and inference on CPU-only hardware without CUDA, 8-bit quantization, or GPU acceleration, fitting within 7GB RAM and 14GB disk (See US-1, US-2)
- **FR-008**: System MUST apply multiple-comparison correction when testing ≥ 10 planning task variants using family-wise error rate control at α=0.05 (See US-2)

### Key Entities *(include if feature involves data)*

- **EpisodicMemory**: Stores (state, action, outcome) tuples with semantic embeddings; key attributes include episode_id, state_embedding, action_embedding, outcome, timestamp, confidence_score
- **PlanningTask**: Benchmark task from ALFWorld/TextWorld with ground-truth solution; key attributes include task_id, initial_state, goal_state, required_steps, episodic_dependencies
- **FutureScenario**: Generated planning output combining episodic memories with current state; key attributes include scenario_id, generated_plan, episodic_references, counterfactual_details, confidence_scores

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Planning accuracy improvement is measured against baseline transformer performance on 50 held-out ALFWorld/TextWorld tasks (See US-2)
- **SC-002**: Episodic retrieval precision is measured against ground-truth episode relevance labels for 1000 retrieval queries (See US-1)
- **SC-003**: Counterfactual detail confidence calibration is measured against verifiable episodic truth across 500 generated scenario details (See US-3)
- **SC-004**: Scene construction coherence is measured against human evaluation ratings on 1-5 Likert scale for 100 generated scenarios (See US-3)
- **SC-005**: Retrieval threshold sensitivity is measured by sweeping similarity threshold ∈ {0.70, 0.75, 0.80} and reporting precision variation (See US-3)

## Assumptions

- ALFWorld and TextWorld benchmark environments are available under an Apache license and can be downloaded and executed within the 6-hour CI job time limit
- The 70M parameter baseline transformer model fits within 7GB RAM during both training and inference on CPU-only execution
- Human evaluation for scene construction quality can be conducted with ≥ 3 raters achieving inter-rater reliability ≥ 0.75 using standardized 1-5 Likert scale
- Power analysis with n=10 planning task variants provides [deferred] power to detect effect size d=0.8 at α=0.05; if actual effect size is smaller, results will be reported as underpowered
- The neural episodic control architecture from Pritzel et al. (2017) can be implemented without GPU acceleration while maintaining retrieval performance within 500ms latency requirement
- Dataset-variable fit: ALFWorld/TextWorld benchmarks contain all required variables (state, action, outcome) for episodic memory construction; [NEEDS CLARIFICATION: does benchmark contain temporal markers needed for scene construction?]
- Inference framing: Findings will be framed as associational relationships between architecture and performance, not causal claims about memory mechanisms
- Threshold justification: The cosine similarity threshold of 0.75 is based on community-standard semantic retrieval benchmarks; sensitivity analysis will sweep ∈ {0.70, 0.75, 0.80} and report precision variation
- Predictor collinearity: If state and outcome embeddings show high correlation (r ≥ 0.85), joint relationships will be framed descriptively rather than claiming independent predictive effects
- Multiplicity & power: When testing ≥ 10 planning task variants, Bonferroni correction will be applied to maintain family-wise error rate at α=0.05; power considerations are [deferred] pending actual effect size measurement
