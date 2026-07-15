# Feature Specification: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

**Feature Branch**: `001-llmxive-symbolic-state-retention`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Beyond the Current Observation: Evaluating Multimodal Large Language M'"

## User Scenarios & Testing

### User Story 1 - ASCII State Rendering and Environment Generation (Priority: P1)

The researcher needs to generate deterministic 3D Maze game instances where the raw visual grid frames are converted into ASCII text representations and accompanying JSON event logs, replacing the original image-based input stream.

**Why this priority**: This is the foundational capability. Without a reliable, deterministic text-based state representation, the core hypothesis (that symbolic inputs improve retention) cannot be tested. It isolates the "modality" variable.

**Independent Test**: Can be fully tested by running the renderer script on a fixed seed, capturing the output ASCII grid and JSON log, and verifying that the same seed produces bit-identical output and that the ASCII grid accurately reflects the ground-truth maze state (walls, player, items).

**Acceptance Scenarios**:

1. **Given** a RNG-Bench 3D Maze instance with a specific random seed, **When** the ASCII renderer is executed, **Then** it outputs a text grid where `#` represents walls, `.` represents floor, and `M` represents the player, matching the visual ground truth.
2. **Given** a game step where an item is collected, **When** the event logger processes the state, **Then** it appends a JSON object `{"t": <timestamp>, "event": "saw_key"}` to the log without ambiguity.
3. **Given** a corrupted or out-of-bounds state from the environment, **When** the renderer processes it, **Then** it outputs a standardized error ASCII block (e.g., `ERROR: STATE_CORRUPT`) rather than crashing.

---

### User Story 2 - Text-Only Agent Inference Loop (Priority: P2)

The researcher needs to execute a text-only LLM (e.g., 3B parameter quantized model) in a long-horizon loop where it receives the ASCII state and event log, updates an internal "mental map," and outputs an action, all within the constraints of a CPU-only CI runner.

**Why this priority**: This implements the experimental condition. It tests whether the model can utilize the symbolic input to maintain state over time without the visual overhead.

**Independent Test**: Can be fully tested by running a short, fixed-sequence maze game with the agent, verifying that the agent successfully outputs a valid move sequence and that the "mental map" string evolves logically based on the ASCII inputs.

**Acceptance Scenarios**:

1. **Given** a prompt containing the current ASCII grid and the history of JSON events, **When** the agent processes the input, **Then** it outputs a valid JSON action (e.g., `{"move": "up"}`) and an updated "mental map" string.
2. **Given** a sequence of 50 steps where a key was seen at step 10, **When** the agent is queried at step 50, **Then** its "mental map" explicitly references the key's location (or lack thereof) based on the ASCII history.
3. **Given** a memory constraint of 7GB RAM, **When** the agent loads the quantized model and runs the inference loop, **Then** the process completes without an Out-Of-Memory (OOM) error.

---

### User Story 3 - Memory Gap Metric Calculation and Statistical Comparison (Priority: P3)

The researcher needs to compute the "Memory Gap" score by comparing the agent's internal state description against the ground-truth environment state at critical decision points and perform a statistical comparison against the baseline MLLM results.

**Why this priority**: This provides the quantitative evidence required to answer the research question. It translates raw agent behavior into a measurable scientific metric.

**Independent Test**: Can be fully tested by feeding the agent's output logs and the ground-truth state logs into the scoring script, verifying that a numeric "Memory Gap" score is produced and that the statistical test (Mann-Whitney U) executes without error.

**Acceptance Scenarios**:

1. **Given** the agent's "mental map" at step $t$ and the ground-truth state at step $t$, **When** the scorer evaluates them, **Then** it calculates a deviation score (e.g., token mismatch count or semantic similarity loss) representing the "Memory Gap."
2. **Given** a set of 20 game runs with the text-only agent and a baseline distribution of scores from the original MLLM paper, **When** the statistical module runs, **Then** it outputs a p-value and a conclusion on whether the difference is significant (p < 0.05).
3. **Given** a run where the agent hallucinates a non-existent wall, **When** the scorer processes the discrepancy, **Then** it increments the "false-positive" count in the final report.

### Edge Cases

- What happens when the ASCII representation becomes too large for the model's context window? (The system must truncate the event log or implement a sliding window strategy).
- How does the system handle a game instance where the agent gets stuck in a loop? (The system must enforce a hard step limit, e.g., 500 steps, and record the run as "timeout" rather than hanging).
- How does the system handle a model inference failure (e.g., NaN output)? (The system must log the error, discard the run, and increment a "failure rate" metric).

## Requirements

### Functional Requirements

- **FR-001**: System MUST render the 3D Maze environment into a deterministic ASCII grid and a structured JSON event log for every time step, ensuring a 1:1 mapping between visual ground truth and text representation (See US-1).
- **FR-002**: System MUST load a quantized text-only LLM (≤3B parameters) into memory using a CPU-optimized inference engine (e.g., `llama.cpp` or `bitsandbytes` in CPU mode) without requiring CUDA or GPU acceleration (See US-2).
- **FR-003**: System MUST execute a closed-loop inference cycle where the agent receives the ASCII state and event history, outputs a move action and an updated state description, and receives the next state from the environment (See US-2).
- **FR-004**: System MUST compute the "Memory Gap" metric by quantitatively comparing the agent's generated "mental map" against the ground-truth environment state at predefined critical decision points, using the algorithm defined in FR-006 (See US-3).
- **FR-005**: System MUST perform a one-tailed Mann-Whitney U test to compare the distribution of "Memory Gap" scores from the text-only agent against the baseline MLLM distribution, testing the null hypothesis (H0) that the distributions are equal against the alternative hypothesis (H1) that the text-only distribution is strictly lower (See US-3).
- **FR-006**: System MUST calculate the "Memory Gap" as the sum of: (1) the normalized Levenshtein distance between the agent's recalled state string and the ground-truth state string, and (2) a penalty of 1.0 for every critical item (e.g., key, door) present in the ground truth but missing from the agent's mental map (See US-3).
- **FR-007**: System MUST validate that the "Memory Gap" metric specifically targets state variables (e.g., item locations) that are NOT visible in the current ASCII frame but must be inferred from history, ensuring the test measures retention rather than parsing accuracy (See US-3).
- **FR-008**: System MUST re-run the baseline MLLM on the exact same ASCII inputs and RNG seeds as the text-only agent to generate a comparable baseline distribution, ensuring the statistical test compares like-for-like modalities (See US-3).

### Key Entities

- **GameInstance**: Represents a specific RNG-Bench maze configuration, including the seed, grid dimensions, and item locations.
- **StateSnapshot**: A composite object containing the ASCII grid string, the JSON event log history, and the ground-truth internal state variables.
- **AgentResponse**: The output from the LLM containing the intended action (move) and the updated "mental map" string.
- **MetricResult**: The final output containing the computed Memory Gap score, the p-value, and the confidence interval.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The "Memory Gap" score (deviation between agent map and ground truth) is measured against the mean Memory Gap score derived from the baseline MLLM re-run on the same ASCII inputs to determine if the text-only agent outperforms the visual baseline (See US-3).
- **SC-002**: The statistical significance (p-value) of the performance difference is measured against the standard threshold of p < 0.05 to validate the hypothesis that modality reduction improves retention (See US-3).
- **SC-003**: The peak RAM consumption during the inference loop is measured against the GitHub Actions runner limit of 7 GB to ensure the method is feasible on free-tier CPU hardware (See US-2).
- **SC-004**: The total execution time for a batch of 20 game instances is measured against the 6-hour CI job limit to ensure the research is reproducible within standard continuous integration windows (See US-2).
- **SC-005**: The consistency of the ASCII renderer is measured against the ASCII ground truth derived from the visual frames to ensure zero information loss (Levenshtein distance = 0) in the text representation (See US-1).

## Assumptions

- The RNG-Bench environment codebase is accessible and can be modified to output ASCII grids without requiring changes to the core game logic.
- A 3B parameter model (e.g., Qwen2-3B or Llama-3-8B-Instruct 4-bit) is sufficient to demonstrate the cognitive capability difference; if a larger model is required for reasoning, the project scope is limited to the CPU-tractable 3B class.
- The "Memory Gap" metric defined in the original RNG-Bench paper is applicable to text-based state representations and can be calculated via string comparison or semantic similarity without needing the original visual tokenization.
- The GitHub Actions free-tier runner provides consistent 2 CPU cores and ~7 GB RAM; any variance in hardware performance is assumed to be within acceptable noise for statistical analysis.
- The baseline MLLM can be adapted to process ASCII inputs (e.g., by treating ASCII as a text prompt or using a text-capable variant) to generate a valid baseline distribution for comparison.
- The quantized model inference will not exceed the 14 GB disk space limit of the runner, including model weights and temporary cache files.