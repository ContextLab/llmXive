# Feature Specification: OPID Critical-First Routing Complexity Analysis

**Feature Branch**: `001-opid-routing-complexity`  
**Created**: 2026-07-24  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning' - investigating non-monotonic relationship between critical-first routing and environment complexity."

## User Scenarios & Testing

### User Story 1 - Synthetic Environment Construction & Tier Generation (Priority: P1)

The researcher needs to generate a suite of synthetic State-Graph Environments with three distinct complexity tiers (Tier 1: Deterministic, Tier 2: Stochastic, Tier 3: High-Entropy) to serve as the controlled testbed for the OPID algorithm.

**Why this priority**: Without valid, reproducible, and complexity-varied environments, no empirical analysis of the routing mechanism can occur. This is the foundational data layer.

**Independent Test**: The system can be tested by instantiating the environment generator, verifying that Tier 1 graphs have a single deterministic path with 5-10 nodes, Tier 2 graphs have branching paths with 20-50 nodes, and Tier 3 graphs have sparse rewards with 100+ nodes, all generated without external dependencies.

**Acceptance Scenarios**:

1. **Given** the environment generator is initialized with Tier 1 parameters, **When** a graph is generated, **Then** the resulting graph must contain a single unique path from start to goal with 5 to 10 nodes and zero stochastic branching.
2. **Given** the environment generator is initialized with Tier 2 parameters, **When** a graph is generated, **Then** the resulting graph must contain at least 20 nodes with multiple branching paths and stochastic transition probabilities.
3. **Given** the environment generator is initialized with Tier 3 parameters, **When** a graph is generated, **Then** the resulting graph must contain 100+ nodes with sparse reward signals and high-entropy state transitions.

---

### User Story 2 - OPID Integration with Tunable Routing Threshold (Priority: P2)

The researcher needs to integrate the OPID algorithm with a tunable "critical-first" routing threshold parameter (ranging from 0 to 1) to control the density of hindsight skill injection during policy execution.

**Why this priority**: This directly manipulates the independent variable (predictor) of the research question. Without a controllable injection rate, the non-monotonic relationship cannot be measured.

**Independent Test**: The system can be tested by running the agent with the threshold set to 0 (always inject) and 1 (never inject) and verifying that the log-probability shifts and action selections differ significantly in accordance with the injection density.

**Acceptance Scenarios**:

1. **Given** the OPID agent is running with a routing threshold of 0.0, **When** the agent encounters a state, **Then** the system must inject a hindsight skill distillation signal for every eligible action.
2. **Given** the OPID agent is running with a routing threshold of 1.0, **When** the agent encounters a state, **Then** the system must suppress all hindsight skill injection signals.
3. **Given** the OPID agent is running with a routing threshold of 0.5, **When** the agent encounters a state, **Then** the system must inject skill signals for eligible actions where a Bernoulli trial with p = 1 - threshold (0.5) succeeds, based on the critical-first routing threshold logic.

---

### User Story 3 - Performance & Rigidity Measurement Across Thresholds (Priority: P3)

The researcher needs to execute 1,000 simulated episodes per threshold setting for each complexity tier and record "policy rigidity" (variance in action entropy) and "success rate" to identify the inflection point where skill injection becomes counterproductive.

**Why this priority**: This generates the dependent variables (outcome) required to validate the hypothesis. It confirms whether the "sweet spot" exists and how it shifts with complexity.

**Independent Test**: The system can be tested by running a single batch of [deferred] episodes for Tier 1 at a specific threshold and verifying that a success rate (percentage of ground-truth path completion) and action entropy variance are recorded and stored for analysis.

**Acceptance Scenarios**:

1. **Given** the required [deferred] episodes (see FR-003) are completed for Tier 1 at a specific threshold, **When** the run concludes, **Then** the system must output a success rate (0.0 to 1.0) and the mean variance of action entropy for that run.
2. **Given** the same threshold is applied across all three tiers, **When** the runs conclude, **Then** the system must produce distinct success rate profiles for Tier 1, Tier 2, and Tier 3 that allow for statistical comparison.
3. **Given** the threshold is swept from 0.0 to 1.0 in steps of 0.1, **When** the full sweep completes, **Then** the system must identify the specific threshold value where the success rate for Tier 1 begins to decline relative to lower injection rates.

---

### Edge Cases

- **What happens when** the graph generation results in an unreachable goal node due to stochastic pruning in Tier 2/3?
  - *Handling*: The environment generator must include a validation step to ensure a valid path exists before episode generation; if not, the graph is regenerated.
- **How does the system handle** a threshold value that results in zero skill injection in a high-complexity environment where the baseline policy is known to be ineffective?
  - *Handling*: The system must still record a success rate of 0.0 or near-0.0 and log the "policy rigidity" as the baseline entropy, ensuring the data point is valid for the "no injection" control condition.
- **What happens when** the action entropy variance is mathematically undefined (e.g., only one action taken in all [deferred] episodes)?
  - *Handling*: The variance calculation must default to 0.0 and be flagged in the log as "deterministic policy observed."

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic State-Graph Environments with three distinct complexity tiers: Tier 1 (5-10 nodes, deterministic), Tier 2 (20-50 nodes, stochastic), and Tier 3 (100+ nodes, sparse rewards) to serve as the experimental testbed (See US-1).
- **FR-002**: System MUST implement the OPID algorithm with a configurable "critical-first" routing threshold parameter that scales from 0 (always inject) to 1 (never inject) to control skill injection density (See US-2).
- **FR-003**: System MUST execute exactly 1,000 simulated episodes for each combination of complexity tier and routing threshold setting to ensure statistical power (See US-3). *Justification*: Based on G*Power analysis for a one-way ANOVA (f=0.25, α=0.05, power=0.80), N=1,000 is the minimum required to detect the expected effect size of the "over-supervision" phenomenon with sufficient power.
- **FR-004**: System MUST calculate and record "policy rigidity" defined as the residual variance of action entropy (the variance remaining after regressing out the deterministic effect of the routing threshold) across all episodes for each run (See US-3).
- **FR-005**: System MUST calculate and record "success rate" defined as the percentage of episodes where the agent successfully traverses the ground-truth path in the synthetic graph (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweep of the routing threshold at intervals of 0.1 (0.0, 0.1, ..., 1.0) to identify the inflection point of performance degradation (See US-3).
- **FR-007**: System MUST ensure all graph generation and policy execution logic runs on CPU-only hardware without requiring GPU acceleration or CUDA libraries (See Assumptions).

### Key Entities

- **StateGraph**: A directed graph representing the environment, containing nodes (states) and edges (transitions) with attributes for complexity tier, reward sparsity, and stochasticity.
- **RoutingThreshold**: A scalar value (0.0 to 1.0) controlling the probability of injecting hindsight skill distillation signals during the on-policy trajectory.
- **EpisodeResult**: A data record containing the success status (boolean), action entropy variance (float), and total steps taken for a single simulation run.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The relationship between routing threshold and success rate is measured against the hypothesis of non-monotonicity by fitting a quadratic regression; success is defined as the quadratic term being statistically significant (p < 0.05) and negative, indicating an inverted U-curve (See FR-005, FR-006).
- **SC-002**: The "distillation cost-benefit ratio" is measured by comparing the log-probability shift (advantage) measured on a frozen policy against a held-out validation set, against the actual improvement in task completion to identify the inflection point where added skill density correlates with decreased success in Tier 1 (See FR-005, FR-006).
- **SC-003**: The residual variance in action entropy (policy rigidity) is measured against the complexity tier to verify if higher injection rates in deterministic environments lead to significantly lower entropy (over-constraining) beyond the deterministic effect of the threshold (See FR-004).
- **SC-004**: The statistical significance of the interaction between routing threshold and environment complexity is measured using ANOVA; success is defined as the interaction term yielding a p-value < 0.05 (See FR-006).
- **SC-005**: The computational feasibility of the entire analysis (1,000 episodes × 11 thresholds × 3 tiers) is measured against the 6-hour free-tier CPU limit and 7GB RAM constraint to ensure the experiment completes without resource exhaustion (See FR-007).

## Assumptions

- **Assumption about data source**: The synthetic State-Graph Environment suite generated by NetworkX is sufficient to model the "low-complexity" vs "high-entropy" spectrum required to test the OPID hypothesis, as no real-world RL dataset with labeled "hindsight skill injection" ground truth exists.
- **Assumption about policy head**: A lightweight baseline policy (e.g., a small rule-based agent or a distilled LLM acting as a policy head) is sufficient to demonstrate the "over-constraining" effect of OPID without requiring the training of a full-scale transformer from scratch, ensuring CPU feasibility.
- **Assumption about threshold justification**: The routing threshold sweep interval of 0.1 is based on a standard granularity for hyperparameter sensitivity analysis in RL, balancing resolution with computational cost.
- **Assumption about inference framing**: Since the environment is synthetic and the threshold is manually controlled, the findings regarding the "critical-first" mechanism will be framed as associational observations of policy behavior rather than causal claims about real-world agent performance, unless randomization is explicitly applied to the environment generation process.
- **Assumption about compute constraints**: The total memory footprint of the [deferred] episodes per setting will remain within acceptable limits by processing episodes sequentially and discarding intermediate trajectory data after calculating the success rate and entropy variance.
- **Assumption about measurement validity**: The "success rate" measured against the ground-truth path in the synthetic graph is a valid proxy for task completion, as the graph topology is generated independently of the policy's actions, ensuring metric independence.
- **Assumption about multiplicity**: The analysis of three complexity tiers constitutes a family of tests; a multiple-comparison correction (e.g., Bonferroni) will be applied if individual tier comparisons are reported as statistically significant to control the family-wise error rate.
- **Assumption about collinearity**: The routing threshold and the resulting action entropy are definitionally related (higher injection reduces entropy); therefore, the analysis will frame this as a characterization of the mechanism's effect (via residual variance) rather than claiming independent predictive effects of the threshold on rigidity.