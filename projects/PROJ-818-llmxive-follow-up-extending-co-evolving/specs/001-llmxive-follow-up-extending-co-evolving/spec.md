# Feature Specification: llmXive follow-up: extending "Co-Evolving Policy Distillation"

**Feature Branch**: `001-coevolving-policy-distillation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Co-Evolving Policy Distillation' - Does co-evolving policy distillation mitigate catastrophic forgetting in discrete, non-differentiable reasoning tasks more effectively than sequential distillation, independent of total data exposure?"

## User Scenarios & Testing

### User Story 1 - Synthetic Task Environment Generation (Priority: P1)

The researcher MUST be able to generate a synthetic dataset of propositional logic proofs and grid-world navigation tasks using `sympy` and `networkx`, ensuring distinct rule sets per domain and parameterized difficulty levels.

**Why this priority**: This is the foundational data layer. Without a controlled, reproducible environment with known ground-truth rules, no comparison of forgetting rates or distillation strategies is possible. It enables the independent testing of the "data generation" component.

**Independent Test**: The system can be tested by running the generator script and verifying that the output contains valid logical proofs and navigable grids with unique, identifiable rule signatures for each task domain.

**Acceptance Scenarios**:

1. **Given** a request to generate 100 propositional logic proofs, **When** the generator executes, **Then** the output file contains 100 valid proofs where each proof relies on a distinct subset of logical axioms defined in the configuration.
2. **Given** a request to generate 50 grid-world tasks, **When** the generator executes, **Then** the output contains 50 distinct grid configurations where navigation success depends on specific, non-overlapping rule sets (e.g., "avoid red zones" vs. "follow diagonal paths").

---

### User Story 2 - Distillation Strategy Execution Engine (Priority: P2)

The researcher MUST be able to instantiate and run three distinct agent training conditions (Sequential, Mixed-task, Co-evolving) on a CPU-only environment for a fixed number of generations, ensuring equal total data exposure across all conditions.

**Why this priority**: This implements the core experimental manipulation (the independent variable). It allows the researcher to isolate the effect of the "co-evolution" mechanism from total data volume.

**Independent Test**: The system can be tested by running the three conditions in isolation and verifying that the total number of rule evaluations per task is identical across all three runs, while the internal logic of the co-evolving agent successfully exchanges rule-sets between sub-populations.

**Acceptance Scenarios**:

1. **Given** the sequential condition is configured for 50 generations, **When** the training loop completes, **Then** the agent's performance metric is recorded, and the log confirms that only one task domain was active during each generation block.
2. **Given** the co-evolving condition is configured for 50 generations, **When** the training loop completes, **Then** the log confirms that bidirectional rule-set exchanges occurred between sub-populations at every generation step, and the total number of rule evaluations matches the sequential condition exactly.

---

### User Story 3 - Catastrophic Forgetting Measurement & Analysis (Priority: P3)

The researcher MUST be able to evaluate trained agents on held-out test instances from all tasks and calculate the "forgetting rate" (drop in accuracy from initial task-specific performance to multi-task performance), followed by a statistical comparison (ANOVA) across the three conditions.

**Why this priority**: This implements the dependent variable measurement and the final validation step. It directly answers the research question by quantifying the efficacy of the co-evolving strategy.

**Independent Test**: The system can be tested by taking a pre-trained agent (from any condition), running it against a held-out test set, and verifying that the calculated forgetting rate is mathematically derived from the difference between initial and final accuracy scores.

**Acceptance Scenarios**:

1. **Given** a trained agent from the sequential condition, **When** evaluated on held-out instances of Task A and Task B, **Then** the system reports the accuracy drop for each task and aggregates them into a single "forgetting rate" metric.
2. **Given** the forgetting rates for all three conditions (Sequential, Mixed, Co-evolving), **When** the statistical analysis module runs, **Then** the output includes a one-way ANOVA result and post-hoc Tukey test comparisons identifying significant differences between conditions.

### Edge Cases

- What happens if the synthetic generator fails to produce a valid proof due to a logical contradiction in the parameterization? (System should retry generation of that specific instance up to 3 times before logging a warning for that instance; the overall run continues to ensure reproducibility).
- How does the system handle a scenario where the co-evolving exchange results in a rule-set that degrades performance for both sub-populations? (The evolutionary strategy must include a selection pressure to discard non-performing rule-sets, preventing population collapse).
- What if the total data exposure calculation drifts due to floating-point precision errors during the "equal exposure" constraint? (The system must enforce a hard integer cap on rule evaluations per generation to ensure exact parity, verified by a post-run checksum).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic propositional logic proofs and grid-world navigation tasks using `sympy` and `networkx` with distinct, parameterized rule sets per domain (See US-1).
- **FR-002**: System MUST implement a training loop that executes a sufficient number of generations to ensure convergence for all agent types., where each generation is defined as a fixed budget of a predetermined number of rule evaluations, maintaining an identical total count of rule evaluations per task across Sequential, Mixed-task, and Co-evolving conditions (verified by a post-run checksum of rule-evaluation counters) (See US-2).
- **FR-003**: System MUST support a "Co-evolving" mode where sub-populations exchange successful rule-sets bidirectionally at every generation step without gradient-based updates (See US-2).
- **FR-004**: System MUST evaluate trained agents against held-out test sets distinct from the training data to measure retention of logical rules and navigation strategies (See US-3).
- **FR-005**: System MUST calculate the "catastrophic forgetting rate" as the percentage drop in accuracy from initial single-task performance (measured on a held-out test set distinct from training data) to final multi-task performance for each agent (See US-3).
- **FR-006**: System MUST perform a one-way ANOVA (or Kruskal-Wallis if non-parametric assumptions are violated) and post-hoc Tukey tests to statistically compare forgetting rates across the three experimental conditions (See US-3).

### Key Entities

- **TaskDomain**: Represents a specific reasoning domain (e.g., "Propositional Logic", "Grid Navigation") containing a unique set of rules and parameterized difficulty.
- **RuleSet**: A collection of logical or behavioral rules derived from a TaskDomain, used as the unit of exchange in the Co-evolving condition.
- **AgentCondition**: An instance of an agent trained under a specific strategy (Sequential, Mixed, or Co-evolving) with a recorded history of performance and rule retention.
- **ForgettingMetric**: A quantitative value representing the degradation in performance, calculated as the difference between initial and final accuracy.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in forgetting rates between the Co-evolving condition and the Sequential condition is measured against the null hypothesis of no difference using a one-way ANOVA with p < 0.05 (See US-3).
- **SC-002**: The total number of rule evaluations per task is measured against the target value of 50 generations * [deferred] rules per generation to ensure exact parity across all three conditions (See US-2).
- **SC-003**: The retention rate of distinct logical rules in the Co-evolving condition is measured against the retention rate of the Mixed-task condition to isolate the effect of bidirectional exchange (See US-3).
- **SC-004**: The statistical power of the ANOVA is measured against the requirement to detect a medium effect size (Cohen's f = 0.25) with α = 0.05 and power ≥ 0.8, requiring a minimum sample size of N ≥ 30 runs per condition (See US-3).
- **SC-005**: The validity rate of the synthetic dataset is measured against a target threshold of ≥ 99% for logically valid proofs and solvable grid tasks (See US-1).

## Assumptions

- **Assumption about data/environment**: The synthetic data generation using `sympy` and `networkx` will fit entirely within the available RAM limit of the free-tier CI runner, as the datasets are generated on-the-fly and do not require storing large pre-computed corpora.
- **Assumption about scope boundaries**: The study is limited to propositional logic and grid-world navigation; results are not assumed to generalize to high-dimensional continuous control tasks or natural language generation without further validation.
- **Assumption about target users**: The primary users are researchers in symbolic AI and evolutionary computation who require a CPU-tractable environment to test non-differentiable policy transfer mechanisms.
- **Assumption about methodological validity**: Since the design is observational (comparing distinct training protocols without random assignment of agents to "genetic" lineages in a way that eliminates all confounds), findings will be framed as associational evidence of mechanism efficacy rather than definitive causal proof of "co-evolution" as a universal law.
- **Assumption about compute feasibility**: The evolutionary strategies and statistical analysis (ANOVA/Tukey) will complete within the job limit on a 2-core CPU, as they rely on closed-form computations and lightweight simulation rather than deep learning training.