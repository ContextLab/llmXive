# Feature Specification: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

**Feature Branch**: `001-llmxive-density-horizon`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "How does the semantic density of retrieved context modulate the optimal masking horizon for long-horizon search agents, and does high-density information retain 'critical evidence' status for significantly longer temporal windows than low-density information?"

## User Scenarios & Testing

### User Story 1 - Synthetic Trajectory Generation with Controlled Density (Priority: P1)

As a researcher, I need a Python-based simulator that generates 500 synthetic search trajectories where "critical evidence" is injected at specific turns, and the semantic density of that evidence is explicitly parameterized (via information entropy per token), so that I can isolate the variable of interest without relying on external, noisy datasets.

**Why this priority**: This is the foundational data source. Without a mechanism to independently control semantic density and evidence age, the core hypothesis cannot be tested. It must be the first implemented component.

**Independent Test**: The system can be tested by running the generator with fixed seeds and verifying that the output JSON file contains a sufficient number of trajectories., where the calculated entropy per token for injected evidence blocks matches the requested density levels (low, medium, high) within a tolerance of ±0.01 bits/token.

**Acceptance Scenarios**:

1. **Given** a request to generate a trajectory with "high-density" evidence injected at turn 5, **When** the simulator runs, **Then** the output JSON file contains a trajectory where the text block at turn 5 has an entropy per token ≥ 4.5 bits, and the ground truth metadata marks turn 5 as "critical."
2. **Given** a request to generate a trajectory with "low-density" evidence injected at turn 10, **When** the simulator runs, **Then** the output JSON file contains a trajectory where the text block at turn 10 has an entropy per token ≤ 2.0 bits, and the ground truth metadata marks turn 10 as "critical."
3. **Given** a request for 500 trajectories, **When** the generation completes, **Then** the total file size is ≤ 100 MB, ensuring it fits within the disk limit of the CI runner.

---

### User Story 2 - Agent Simulation with Variable Retention Horizons (Priority: P2)

As a researcher, I need to run a simulation loop where a rule-based or small-context agent processes the generated trajectories while systematically applying retention horizons (from 1 to $T$ turns) to observe how success rates fluctuate based on the age and density of the retained evidence.

**Why this priority**: This implements the core experimental intervention. It connects the data generation (US-1) to the statistical analysis (US-3) by producing the raw performance metrics (success/failure) needed for the regression model.

**Independent Test**: The system can be tested by running the simulation on a small subset of trajectories with a known "ground truth" retention horizon (e.g., evidence at turn 5 must be visible). The system must correctly report "failure" when the retention horizon is set to < 5 turns for high-density evidence, and "success" when ≥ 5 turns (subject to the probabilistic solver).

**Acceptance Scenarios**:

1. **Given** a trajectory with critical evidence at turn 5, **When** the agent runs with a retention horizon of 4 turns, **Then** the agent's output is recorded as "failure" (binary 0) because the evidence was masked (not retained).
2. **Given** a trajectory with critical evidence at turn 5, **When** the agent runs with a retention horizon of 5 turns, **Then** the agent's output is recorded as "success" (binary 1) because the evidence was retained and the heuristic solver succeeded.
3. **Given** a trajectory with low-density evidence at turn 5, **When** the agent runs with a retention horizon of 4 turns, **Then** the system records the result, allowing for comparison against the high-density condition to detect the "modulation" effect.

---

### User Story 3 - Statistical Analysis and Regime Mapping (Priority: P3)

As a researcher, I need a statistical analysis script that performs a logistic regression (GLM) to quantify the interaction effect between semantic density and masking horizon on success probability, and generates a 3D surface plot visualizing the "regime map" of optimal retention windows.

**Why this priority**: This delivers the scientific answer to the research question. It transforms the raw simulation logs into the final empirical findings (the "regime map") required to validate or falsify the hypothesis.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where the interaction effect is hard-coded (e.g., high density *always* requires longer horizons). The regression output must show a statistically significant interaction term (p < 0.05) and the plot must visually display the surface shift.

**Acceptance Scenarios**:

1. **Given** the simulation logs containing success rates, masking horizons, and density levels, **When** the analysis script runs, **Then** it outputs a logistic regression table showing the coefficient and p-value for the `density * horizon` interaction term.
2. **Given** the same logs, **When** the visualization script runs, **Then** it generates a PNG file (≤ 5 MB) showing a 3D surface plot with Masking Horizon on the X-axis, Semantic Density on the Y-axis, and Success Rate on the Z-axis.
3. **Given** the analysis results, **When** the script completes, **Then** it outputs a summary text file stating whether the hypothesis (positive correlation between density and optimal horizon) was supported by the data.

### Edge Cases

- **What happens when** the semantic density calculation results in a value of 0 (e.g., repetitive text)? The system must handle this by clamping the density value to a minimum threshold to prevent division-by-zero errors in entropy calculations, while logging the event.
- **How does the system handle** trajectories where the "critical evidence" is injected at the very last turn ($T$)? The simulation must ensure that a retention horizon of $T$ does not inadvertently mask the final turn (i.e., horizon $T$ implies retaining the last $T$ turns, so success is possible if the evidence is within that window).
- **What happens when** the simulation runs out of memory on the CI runner? The system must implement a streaming approach to write simulation results to disk immediately after each batch of trajectories, rather than holding all results in RAM.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate a synthetic dataset of search trajectories where semantic density is explicitly parameterized using information entropy per token, ensuring independent control over evidence age and density (See US-1).
- **FR-002**: The system MUST implement a simulation loop that applies a configurable retention horizon (from 1 to $T$ turns) to each trajectory and records a binary success/failure outcome based on ground-truth evidence necessity AND the probabilistic Heuristic Solver (See US-2). Success is defined as: 1 if (critical_evidence_turn_index >= current_turn - retention_horizon + 1) AND (agent_heuristic_success = true), else 0.
- **FR-003**: The system MUST perform a logistic regression (GLM) using the Python `statsmodels` library to quantify the interaction effect between semantic density and masking horizon on the binary success rate. The model MUST include natural splines with a flexible number of degrees of freedom for the 'horizon' variable and require a minimum sample size sufficient to ensure statistical power per (density, horizon) bin. The interaction term MUST be significant at p < 0.05 (See US-3).
- **FR-004**: The system MUST generate a 3D surface plot (PNG format) visualizing the success rate as a function of masking horizon and semantic density (See US-3).
- **FR-005**: The system MUST ensure that the entire simulation and analysis pipeline runs on a CPU-only environment with a peak memory usage of ≤ 7 GB RAM and ≤ 14 GB disk, avoiding any GPU-dependent libraries or large model training (See US-2, US-3).
- **FR-006**: The system MUST output a summary report containing the regression coefficients and p-values for the interaction term to determine statistical significance (See US-3).
- **FR-007**: The system MUST validate that the generated trajectories contain no circular logic by ensuring the density metric is computed solely from input text statistics, independent of the agent's output (See US-1).
- **FR-008**: The system MUST calculate "Semantic Density" as a composite metric defined by the formula: `Density = (Shannon_Entropy weight) + (Technical_Token_Ratio weight)`, where Shannon Entropy is calculated on UTF-8 byte-level tokens and Technical_Token_Ratio is the proportion of tokens matching a predefined list of technical terms (See US-1, Key Entities).
- **FR-009**: The system MUST implement a "Heuristic Solver" that determines retrieval success probabilistically based on the calculated density. The probability of success MUST be calculated using the logistic function: `P(retrieval) = sigmoid(α * (density - threshold)), where α is a scaling parameter and threshold represents a critical density value.`, where density is the value from FR-008 (See FR-002, US-2).

### Key Entities

- **Trajectory**: A sequence of turns representing a search session, containing text blocks, metadata (density, age), and a ground-truth success label.
- **Retention Horizon**: An integer parameter $N$ representing the number of most recent turns to RETAIN (the visible window) applied during simulation.
- **Semantic Density**: A float value representing the composite information density of a specific text block, calculated as `0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio`, used as a predictor variable.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The interaction term coefficient in the logistic regression model is measured against the null hypothesis of zero effect (See FR-003, US-3).
- **SC-002**: The success rate surface plot is measured against the requirement that the output file exists, is a valid PNG ≤ 5 MB, and contains a 3D surface with axes labeled "Masking Horizon", "Semantic Density", and "Success Rate" (See FR-004, US-3).
- **SC-003**: The total runtime of the simulation and analysis pipeline is measured against the time limit of the GitHub Actions free-tier runner. (See FR-005, US-2).
- **SC-004**: The peak memory usage of the simulation process is measured against the 7 GB RAM limit of the CI runner (See FR-005, US-2).
- **SC-005**: The number of generated trajectories is measured against the target of 500 to ensure statistical power for the regression (See FR-001, US-1).

## Assumptions

- The synthetic simulator can approximate "semantic density" using the composite formula defined in FR-008 (Shannon Entropy + Technical Token Ratio) without requiring a pre-trained language model, ensuring CPU feasibility.
- The "critical evidence" ground truth is defined by the simulator's injection logic (i.e., if the evidence is masked, the task is impossible unless the heuristic solver succeeds), removing the need for external human evaluation of success.
- The relationship between density and optimal horizon is non-monotonic and can be adequately captured by a GLM with natural splines as defined in FR-003.
- The 500 trajectories are sufficient to detect a moderate interaction effect (Cohen's $f^2 \approx 0.15$) with 80% power at $\alpha = 0.05$, assuming a balanced design across density levels.
- The "retention" logic in the simulation is implemented as a simple sliding window (retain last $N$ turns) rather than a complex attention mechanism, to maintain computational tractability on free-tier CPU.
- The specific entropy calculation method is defined in FR-008 and Key Entities, ensuring the definition is explicit and not deferred to implementation.