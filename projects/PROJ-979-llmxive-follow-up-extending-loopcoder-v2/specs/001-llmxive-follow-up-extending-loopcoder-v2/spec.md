# Feature Specification: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

## User Scenarios & Testing

### User Story 1 - Core Correlation Analysis (Priority: P1)

The researcher needs to determine if the initial semantic uncertainty (entropy) of a hidden state in an iterative refinement model predicts its convergence trajectory on complex tasks. This is the primary scientific hypothesis; without this correlation data, the project cannot validate or refute the disconnect between internal confidence and reasoning capability.

**Why this priority**: This directly addresses the research question. If this analysis fails or is incomplete, the core motivation (dynamic routing vs. calibration flaws) remains unaddressed.

**Independent Test**: Can be fully tested by running the model on a stratified dataset (HumanEval/MBPP) for $k=1$ (entropy extraction via sampling) and $k=1,2,3$ (convergence tracking), then computing the Spearman rank correlation between the two metrics.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] stratified code/reasoning problems, **When** the system extracts initial semantic entropy (via sampling) and tracks convergence steps, **Then** a correlation coefficient (Spearman's $\rho$) is calculated and reported with a p-value.
2. **Given** the correlation result, **When** the researcher compares it against the null hypothesis, **Then** the system outputs a binary flag indicating whether the correlation is statistically significant ($p < 0.05$).

---

### User Story 2 - Dynamic Router Simulation (Priority: P2)

The researcher needs to evaluate the practical utility of the correlation findings by simulating a lightweight dynamic routing strategy. This determines if the theoretical insight translates to actual FLOPs savings without sacrificing accuracy. The router must predict the *efficiency-convergence trade-off*, not just the convergence step, to avoid tautological validation.

**Why this priority**: While the correlation (US-001) is the scientific finding, the router simulation (US-002) answers the "So what?" question regarding efficiency and deployment feasibility. It is secondary to establishing the existence of the correlation.

**Independent Test**: Can be fully tested by training a logistic regression model on the entropy proxy data to predict optimal loop counts, then evaluating the FLOPs savings vs. accuracy against a static $k=2$ baseline and a random baseline.

**Acceptance Scenarios**:

1. **Given** the entropy and convergence data from US-001, **When** a logistic regression model is trained to predict the optimal loop count, **Then** the model's prediction accuracy is reported and tested for statistical significance ($p < 0.05$) against a random baseline (predicting $k=1$ for all samples).
2. **Given** the trained router, **When** it is applied to a test set, **Then** the system reports the percentage reduction in FLOPs compared to a static $k=2$ baseline and the accuracy difference, testing for statistical non-inferiority (e.g., via a one-sided t-test or equivalence test) rather than asserting a fixed tolerance.

---

### User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

The researcher needs to ensure the findings are robust to methodological choices, specifically regarding multiple comparisons and the sensitivity of the analysis to the definition of "convergence."

**Why this priority**: This ensures the scientific validity of the results (methodological soundness). It is a validation step that supports US-001 and US-002 but is not the primary data generation step itself.

**Independent Test**: Can be fully tested by re-running the correlation analysis with multiple-comparison corrections and varying the convergence threshold to observe rate stability.

**Acceptance Scenarios**:

1. **Given** multiple hypothesis tests (e.g., correlations across different difficulty strata), **When** the system applies a family-wise error correction (e.g., Bonferroni or Holm-Bonferroni), **Then** the adjusted p-values are reported and the significance conclusion is updated.
2. **Given** a specific convergence threshold (e.g., "correct at $k=3$"), **When** the threshold is swept over a small set (e.g., $k \in \{2, 3, 4\}$), **Then** the system reports the variation in the correlation coefficient to confirm stability.

---

### Edge Cases

- **What happens when** the initial semantic entropy is undefined (e.g., deterministic output with zero entropy)? The system must handle this by assigning a minimal non-zero entropy value or excluding the sample, documenting the exclusion rate (See **FR-007**).
- **How does the system handle** inputs where the model fails to converge even at the maximum loop count ($k_{max}$)? These must be treated as "non-convergence" events and included in the correlation analysis as a distinct trajectory category (See **FR-007**).
- **What happens when** the dataset subset for a specific difficulty stratum is too small to yield a reliable correlation? The system must flag the stratum as "underpowered" based on a configurable minimum sample size parameter (default 50) and exclude it from the primary correlation calculation (See **FR-007**).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract the initial semantic entropy from the model for each input. This MUST be computed by generating $N=10$ samples per input, clustering them by semantic equivalence (e.g., exact code match or execution result), and calculating the Shannon entropy over the cluster probabilities (See US-001).
- **FR-002**: System MUST execute iterative refinement runs for loop counts $k \in \{1, 2, 3\}$ on the same inputs to record the convergence trajectory (See US-001).
- **FR-003**: System MUST compute the Spearman rank correlation coefficient between the initial entropy values and the convergence step (or binary success metric) (See US-001).
- **FR-004**: System MUST implement a lightweight logistic regression model trained on entropy proxies to predict optimal loop counts for dynamic routing simulation (See US-002).
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Holm-Bonferroni) to all reported p-values when testing correlations across multiple difficulty strata (See US-003).
- **FR-006**: System MUST evaluate the trained router from FR-004 by reporting its prediction accuracy against a random baseline and testing the accuracy improvement for statistical significance ($p < 0.05$), and by reporting FLOPs savings and accuracy differences against the static $k=2$ baseline with a non-inferiority test (See US-002).
- **FR-007**: System MUST handle edge cases by: (1) assigning a minimal non-zero entropy or excluding samples with undefined entropy; (2) treating non-convergence at $k_{max}$ as a distinct category; and (3) flagging strata with sample counts below a configurable threshold (default $\ge 50$) as underpowered (See Edge Cases).

### Key Entities

- **InputProblem**: Represents a code generation or reasoning problem from HumanEval/MBPP, containing the prompt and the reference solution.
- **ConvergenceTrajectory**: Represents the sequence of model outputs for a single problem across loop counts, including the step at which the correct solution first appears or a failure flag.
- **EntropyProxy**: Represents the scalar semantic entropy value computed via a sampling procedure (generate $N=10$ samples, cluster by semantic equivalence, compute entropy over cluster probabilities) rather than a single forward pass hidden state (See FR-001).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The degree of alignment between initial semantic entropy and convergence trajectory is measured against the null hypothesis of no correlation (Spearman's $\rho = 0$) (See US-001).
- **SC-002**: The FLOPs savings of the dynamic routing strategy is measured against the static $k=2$ baseline accuracy (See US-002).
- **SC-003**: The statistical robustness of the correlation is measured against the family-wise error rate after applying multiple-comparison corrections (See US-003).
- **SC-004**: The sensitivity of the convergence definition is measured by sweeping the maximum loop count threshold over a small concrete set (e.g., $k \in \{2, 3, 4\}$) and reporting the variation in correlation strength (See US-003).
- **SC-005**: The computational feasibility of the analysis is measured by reporting the total runtime and resource usage (RAM/GPU memory) for the full dataset run on a standard GPU instance (See Assumptions).

## Assumptions

- **Dataset-variable fit**: The HumanEval and MBPP datasets contain sufficient reference solutions to serve as independent ground truth for correctness, and the LoopCoder-v2-2B checkpoint is available via HuggingFace for inference.
- **Compute feasibility**: The analysis of [deferred] samples with $k \le 3$ loops per sample fits within the memory limits of a single GPU (e.g., T4/V100 with $\ge 16$ GB VRAM), and the total execution time will not exceed 24 hours on a standard GPU instance. (Note: CPU-only inference for a 2B model on this scale is infeasible).
- **Inference framing**: Since the study is observational (no random assignment of model architecture), all findings regarding the relationship between entropy and convergence will be framed as associational, not causal.
- **Threshold justification**: The convergence definition (first correct answer at loop count $k$) uses the benchmark's reference solution as a binary ground truth, which is a community-standard metric for code generation; a sensitivity analysis sweeping $k \in \{2, 3, 4\}$ is included to validate stability.
- **Measurement validity**: The semantic entropy is computed using the standard method (Kuhn et al., 2023): generating $N=10$ samples, clustering by semantic equivalence, and computing Shannon entropy over cluster probabilities.
- **Predictor collinearity**: Initial entropy and convergence trajectory are treated as distinct variables; no claim of independent predictive effects is made if they are definitionally related, and collinearity diagnostics will be reported if multiple predictors are used in the router simulation.