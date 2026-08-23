# Feature Specification: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

## User Scenarios & Testing

### User Story 1 - Core Correlation Analysis (Priority: P1)

The researcher needs to determine if the initial semantic uncertainty (entropy) of a hidden state in an iterative refinement model predicts its convergence trajectory on complex tasks. This is the primary scientific hypothesis; without this correlation data, the project cannot validate or refute the disconnect between internal confidence and reasoning capability.

**Why this priority**: This directly addresses the research question. If this analysis fails or is incomplete, the core motivation (dynamic routing vs. calibration flaws) remains unaddressed.

**Independent Test**: Can be fully tested by running the model on a stratified dataset (HumanEval/MBPP) for $k=1$ (entropy extraction via sampling) and $k=1,2,3$ (convergence tracking), then computing the Spearman rank correlation between the two metrics, handling censored data via survival analysis.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] stratified code/reasoning problems, **When** the system extracts initial semantic entropy (via sampling) and tracks convergence steps, **Then** a correlation coefficient (Spearman's $\rho$) is calculated and reported with a p-value, and censored data (non-convergence) is handled via Kaplan-Meier survival analysis.
2. **Given** the correlation result, **When** the researcher compares it against the null hypothesis, **Then** the system outputs a binary flag indicating whether the correlation is statistically significant ($p < 0.05$), supported by a power analysis confirming the minimum detectable effect size (MDES) for the sample size.

---

### User Story 2 - Dynamic Router Simulation (Priority: P2)

The researcher needs to evaluate the practical utility of the correlation findings by simulating a lightweight dynamic routing strategy. This determines if the theoretical insight translates to actual FLOPs savings without sacrificing accuracy. The router must predict the *efficiency-convergence trade-off*, not just the convergence step, to avoid tautological validation.

**Why this priority**: While the correlation (US-001) is the scientific finding, the router simulation (US-002) answers the "So what?" question regarding efficiency and deployment feasibility. It is secondary to establishing the existence of the correlation.

**Independent Test**: Can be fully tested by training a logistic regression model on the entropy proxy data to predict optimal loop counts using 5-fold cross-validation, then evaluating the FLOPs savings vs. accuracy against an optimal static baseline (oracle) and a random baseline.

**Acceptance Scenarios**:

1. **Given** the entropy and convergence data from US-001, **When** a logistic regression model is trained to predict the optimal loop count using 5-fold cross-validation, **Then** the model's prediction accuracy is reported and tested for statistical significance ($p < 0.05$) against a random baseline (predicting $k=1$ for all samples).
2. **Given** the trained router, **When** it is applied to a test set, **Then** the system reports the percentage reduction in FLOPs compared to an optimal static baseline (oracle) and the accuracy difference, testing for statistical non-inferiority (e.g., via a one-sided t-test or equivalence test) with a defined margin (delta = 0.05) rather than asserting a fixed tolerance.

---

### User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

The researcher needs to ensure the findings are robust to methodological choices, specifically regarding multiple comparisons and the sensitivity of the analysis to the definition of "convergence."

**Why this priority**: This ensures the scientific validity of the results (methodological soundness). It is a validation step that supports US-001 and US-002 but is not the primary data generation step itself.

**Independent Test**: Can be fully tested by re-running the correlation analysis with multiple-comparison corrections and varying the convergence threshold to observe rate stability, using a hierarchical model to handle small strata.

**Acceptance Scenarios**:

1. **Given** multiple hypothesis tests (e.g., correlations across different difficulty strata), **When** the system applies a family-wise error correction (e.g., Holm-Bonferroni) on fixed a priori strata, **Then** the adjusted p-values are reported and the significance conclusion is updated.
2. **Given** a specific convergence threshold (e.g., "correct at $k=3$"), **When** the threshold is swept over a small set (e.g., $k \in \{2, 3, 4\}$), **Then** the system reports the variation in the correlation coefficient to confirm stability, using a hierarchical mixed-effects model to account for strata uncertainty.

---

### Edge Cases

- **What happens when** the initial semantic entropy is undefined (e.g., deterministic output with zero entropy)? The system must handle this by assigning a minimal non-zero entropy value or excluding the sample, documenting the exclusion rate (See **FR-007**).
- **How does the system handle** inputs where the model fails to converge even at the maximum loop count ($k_{max}$)? These must be treated as censored data points in a survival analysis (Kaplan-Meier estimator) rather than assigned a fixed scalar value, ensuring unbiased correlation estimation (See **FR-003**).
- **What happens when** the dataset subset for a specific difficulty stratum is too small to yield a reliable correlation? The system must include these strata in a hierarchical mixed-effects model with appropriate uncertainty weighting rather than excluding them, ensuring generalizability (See **FR-007**).

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract the initial semantic entropy from the model for each input. This MUST be computed by generating $N=10$ samples per input, clustering them by semantic equivalence using ONLY AST normalization and functional equivalence on *unseen* inputs (strictly excluding the benchmark's test suite used for convergence), and calculating the Shannon entropy over the cluster probabilities (See US-001).
- **FR-002**: System MUST execute iterative refinement runs for loop counts $k \in \{1, 2, 3\}$ on the same inputs to record the convergence trajectory (See US-001).
- **FR-003**: System MUST compute the correlation between the initial entropy values and the convergence step using a survival analysis (Kaplan-Meier estimator) to handle censored data (non-convergence at $k_{max}$), ensuring unbiased estimation (See US-001).
- **FR-004**: System MUST implement a lightweight logistic regression model trained on entropy proxies to predict optimal loop counts for dynamic routing simulation, using 5-fold cross-validation and including baseline pass@1 as a control variable for problem difficulty (See US-002).
- **FR-005**: System MUST apply multiple-comparison correction (e.g., Holm-Bonferroni) to all reported p-values when testing correlations across multiple difficulty strata, where strata are defined as fixed a priori bins based on baseline pass@1 rates from literature (See US-003).
- **FR-006**: System MUST evaluate the trained router from FR-004 by reporting its prediction accuracy against a random baseline and testing the accuracy improvement for statistical significance ($p < 0.05$), and by reporting FLOPs savings and accuracy differences against an optimal static baseline (oracle) with a non-inferiority test (equivalence margin $\delta = 0.05$, $\alpha = 0.05$) (See US-002).
- **FR-007**: System MUST handle edge cases by: (1) assigning a minimal non-zero entropy or excluding samples with undefined entropy; (2) treating non-convergence at $k_{max}$ as censored data in survival analysis; and (3) including strata with sample counts below a configurable threshold (default $\ge 50$) in a hierarchical mixed-effects model rather than excluding them (See Edge Cases).

### Key Entities

- **InputProblem**: Represents a code generation or reasoning problem from HumanEval/MBPP, containing the prompt and the reference solution.
- **ConvergenceTrajectory**: Represents the sequence of model outputs for a single problem across loop counts, including the step at which the correct solution first appears or a failure flag (censored if $k_{max}$ reached).
- **EntropyProxy**: Represents the scalar semantic entropy value computed via a sampling procedure (generate $N=10$ samples, cluster by semantic equivalence using AST/unseen inputs only, compute entropy over cluster probabilities) rather than a single forward pass hidden state (See FR-001).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The degree of alignment between initial semantic entropy and convergence trajectory is measured against the null hypothesis of no correlation (Spearman's $\rho = 0$) using survival analysis, supported by a power analysis confirming the minimum detectable effect size (MDES) for the sample size (See US-001).
- **SC-002**: The FLOPs savings of the dynamic routing strategy is measured against an optimal static baseline (oracle) accuracy, with a non-inferiority test (equivalence margin $\delta = 0.05$, $\alpha = 0.05$) (See US-002).
- **SC-003**: The statistical robustness of the correlation is measured against the family-wise error rate after applying multiple-comparison corrections on fixed a priori strata (See US-003).
- **SC-004**: The sensitivity of the convergence definition is measured by sweeping the maximum loop count threshold over a small concrete set (e.g., $k \in \{2, 3, 4\}$) and reporting the variation in correlation strength using a hierarchical mixed-effects model (See US-003).
- **SC-005**: The computational feasibility of the analysis is measured by reporting the total runtime and resource usage (RAM/GPU memory) for the full dataset run on a standard GPU instance (See Assumptions).

## Assumptions

- **Dataset-variable fit**: The HumanEval and MBPP datasets contain sufficient reference solutions to serve as independent ground truth for correctness, and the CodeLlama-7b-Instruct-hf checkpoint (HuggingFace ID: meta-llama/CodeLlama-7b-Instruct-hf) is available for inference. The research question (internal confidence vs. reasoning) remains valid for a larger-scale model compared to the original hypothesis.
- **Compute feasibility**: The analysis of [deferred] samples with $k \le 3$ loops per sample fits within the memory limits of a single GPU (e.g., T4/V100 with $\ge 16$ GB VRAM), and The total execution time will be constrained within a feasible duration suitable for standard GPU instances.. (Note: CPU-only inference for a 7B model on this scale is infeasible).
- **Inference framing**: Since the study is observational (no random assignment of model architecture), all findings regarding the relationship between entropy and convergence will be framed as associational, not causal.
- **Threshold justification**: The convergence definition (first correct answer at loop count $k$) uses the benchmark's reference solution as a binary ground truth, which is a community-standard metric for code generation; a sensitivity analysis sweeping $k \in \{2, 3, 4\}$ is included to validate stability.
- **Measurement validity**: The semantic entropy is computed using the standard method (Kuhn et al., 2023): generating $N=10$ samples, clustering by semantic equivalence (AST/unseen inputs only), and computing Shannon entropy over cluster probabilities, strictly decoupled from the ground-truth oracle used for convergence.
- **Predictor collinearity**: Initial entropy and convergence trajectory are treated as distinct variables; no claim of independent predictive effects is made if they are definitionally related, and collinearity diagnostics will be reported if multiple predictors are used in the router simulation.
- **Statistical power**: A power analysis is conducted to ensure the sample size (N=164 for HumanEval) is sufficient to detect a minimum effect size (MDES) of interest (e.g., $\rho = 0.2$) with power $\ge 0.8$ at $\alpha = 0.05$.
- **Strata definition**: Difficulty strata are defined as fixed a priori bins based on baseline pass rates from the original HumanEval/MBPP papers, ensuring the number of tests is fixed and independent of the current dataset's performance.