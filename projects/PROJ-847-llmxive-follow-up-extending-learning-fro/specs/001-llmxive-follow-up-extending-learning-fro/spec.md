# Feature Specification: llmXive follow-up: extending "Learning from the Self-future: On-policy Self-distillation for dLLMs"

**Feature Branch**: `001-llmxive-density-analysis`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Learning from the Self-future: On-policy Self-distillation for dLLMs'"

## User Scenarios & Testing

### User Story 1 - Fixed-Density Baseline Convergence (Priority: P1)

The research team must be able to execute a controlled training simulation using the d-OPSD framework with fixed retaining ratios ($\rho_{\text{teacher}}$) to establish a performance baseline and observe the effect of static supervision density on logical reasoning convergence.

**Why this priority**: This is the foundational experiment. Without establishing how fixed densities behave (linear improvement, plateau, or degradation), the adaptive hypothesis cannot be contextualized. It validates the core pipeline (data loading, diffusion model inference on CPU, loss tracking) before introducing dynamic logic.

**Independent Test**: The system runs five distinct training jobs (one for each $\rho \in \{0.1, 0.3, 0.5, 0.7, 0.9\}$) on a subset of GSM8K. The test passes if all five jobs complete within the 6-hour CPU limit and the system successfully writes a structured results file (JSON/CSV) containing the loss trajectory and final accuracy metric for each ratio.

**Acceptance Scenarios**:

1. **Given** a pre-trained lightweight discrete diffusion model and the GSM8K dataset split into train/test sets, **When** the system executes the training loop with $\rho_{\text{teacher}} = 0.5$, **Then** the training completes within 6 hours on a 2-core CPU runner and outputs a final test accuracy and loss curve to a structured file.
2. **Given** the same setup as above, **When** the system iterates through all five fixed ratios in sequence or parallel (within resource limits), **Then** the system generates a comparative summary table (in JSON format) showing the final accuracy for each ratio.
3. **Given** the training process, **When** the model reaches a predefined number of epochs (e.g., 10) or early-stopping criteria, **Then** the system logs the step-level accuracy and records the specific density value used for that step in the metadata file.

---

### User Story 2 - Adaptive Density Scheduler Implementation (Priority: P2)

The system must implement a heuristic scheduler that dynamically adjusts the retaining ratio $\rho_{\text{teacher}}$ during training based on the model's prediction entropy, aiming to maintain supervision density near the hypothesized critical threshold.

**Why this priority**: This addresses the core research hypothesis regarding the "inverted-U" relationship. It moves beyond static baselines to test if an adaptive strategy can outperform the best fixed baseline by tracking the optimal density in real-time. Note: The adaptive run demonstrates the *utility* of tracking the peak; the *existence* of the peak (inverted-U shape) is validated exclusively by the fixed-density baselines in User Story 1 to avoid circular reasoning.

**Independent Test**: The system runs a single training job where $\rho_{\text{teacher}}$ changes every step based on calculated entropy. The test passes if the scheduler logic executes without crashing, the density values vary over time, and the final test accuracy is recorded in a results file distinct from the fixed-baseline results.

**Acceptance Scenarios**:

1. **Given** the training loop is active and the model has generated predictions for a batch, **When** the scheduler calculates the entropy of these predictions, **Then** the system updates $\rho_{\text{teacher}}$ for the next step according to the defined heuristic (e.g., higher entropy $\to$ higher density) without exceeding the bounds $[0.0, 1.0]$.
2. **Given** the adaptive training run, **When** the process completes, **Then** the system outputs a time-series plot (or data file) of $\rho_{\text{teacher}}$ vs. training steps, demonstrating that the density was not constant and fluctuated in response to model confidence.
3. **Given** the final test set, **When** the adaptive model evaluates logical accuracy, **Then** the result is stored in a results file distinct from the fixed-baseline results to enable independent statistical comparison.

---

### User Story 3 - Statistical Validation and Threshold Analysis (Priority: P3)

The system must perform statistical analysis to determine if the adaptive strategy significantly outperforms a *pre-specified* fixed baseline (ρ=0.5) and to characterize the "inverted-U" shape of the density-performance relationship using the full set of fixed baselines.

**Why this priority**: This transforms raw performance numbers into scientific conclusions. It validates the "non-monotonic" hypothesis via the fixed baselines and provides evidence for the adaptive strategy's efficacy via comparison to the pre-specified control, avoiding selection bias.

**Independent Test**: The system takes the final accuracy metrics from the P1 and P2 runs, performs a paired t-test against the pre-specified baseline (ρ=0.5), fits a quadratic model to the fixed baselines, and generates a sensitivity analysis report. The test passes if the system outputs the calculated statistics (p-value, coefficients) in the required format.

**Acceptance Scenarios**:

1. **Given** the final accuracy metrics for the adaptive run and the fixed baseline with $\rho=0.5$, **When** the system executes a paired t-test, **Then** it outputs a JSON object containing the p-value, degrees of freedom, and t-statistic.
2. **Given** the performance curve across the five fixed ratios, **When** the system fits a quadratic model, **Then** it outputs the regression coefficients and the identified peak density value to confirm the "inverted-U" shape.
3. **Given** the optimal density identified from the fixed baselines, **When** a sensitivity analysis is run by sweeping the ratio $\pm 0.05$ and $\pm 0.1$, **Then** the system reports the accuracy degradation (slope of the performance curve) across these deviations.

### Edge Cases

- **What happens when** the entropy calculation results in `NaN` or `Infinity` due to numerical instability in the diffusion model?
  - *Handling*: The scheduler MUST clamp the entropy to a valid range $[0, \ln(N)]$ and default $\rho_{\text{teacher}}$ to the global mean (0.5) for that step to prevent training collapse.
- **How does the system handle** a scenario where the 6-hour CPU runtime limit is reached before the model converges?
  - *Handling*: The training loop MUST implement a hard timeout check at the start of every epoch. If exceeded, it MUST save the current checkpoint and final metrics immediately, marking the run as "TIMEOUT" in the metadata rather than failing silently.
- **What happens when** the GSM8K subset size exceeds the available 7GB RAM?
  - *Handling*: The data loader MUST implement chunked loading or down-sampling to ensure the active batch plus model weights never exceed 6GB RAM, logging a warning if the effective dataset size is reduced.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess the GSM8K dataset and a synthetic logical-deduction subset (e.g., from `bigbench_lite`) ensuring the total active dataset size fits within 7GB RAM (See US-1).
- **FR-002**: System MUST initialize a lightweight discrete diffusion model (≤100M parameters) compatible with CPU-only inference without requiring CUDA or quantization libraries (See US-1).
- **FR-003**: System MUST implement a training loop that supports five distinct fixed retaining ratios ($\rho_{\text{teacher}} \in \{0.1, 0.3, 0.5, 0.7, 0.9\}$) for baseline comparison (See US-1).
- **FR-004**: System MUST implement an adaptive scheduler that calculates prediction entropy at each step and dynamically adjusts $\rho_{\text{teacher}}$ within the bounds $[0.0, 1.0]$ (See US-2).
- **FR-005**: System MUST enforce a hard runtime limit of 6 hours on the training process, saving intermediate checkpoints and final metrics upon timeout (See US-1, US-2).
- **FR-006**: System MUST perform a paired t-test comparing the final test accuracy of the adaptive strategy against the *pre-specified* fixed baseline ($\rho=0.5$) and output a JSON object containing the p-value, degrees of freedom, and t-statistic (See US-3).
- **FR-007**: System MUST execute a sensitivity analysis sweeping the optimal density threshold by $\pm 0.05$ and $\pm 0.1$ to report the accuracy degradation (slope of the performance curve) (See US-3).
- **FR-008**: System MUST fit a quadratic regression model to the accuracy values of the five fixed ratios and output the regression coefficients and the identified peak density to validate the "inverted-U" shape (See US-3).

### Key Entities

- **TrainingConfig**: Represents the hyperparameters for a run, including $\rho_{\text{teacher}}$ (fixed or adaptive), model checkpoint path, and dataset split.
- **TrainingRun**: Represents a single execution instance, containing the loss trajectory, final accuracy, runtime duration, and a log of dynamic density values (if adaptive).
- **StatisticalResult**: Represents the outcome of the analysis, including p-values, confidence intervals, regression coefficients, and the identified peak density threshold.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Final logical accuracy is measured against the held-out test set ground truth to determine the peak performance point across the density spectrum (See US-1, US-2).
- **SC-002**: The functional shape of the relationship between density and performance is measured by fitting a curve to the accuracy values of the five fixed ratios to confirm the "inverted-U" hypothesis (See US-3).
- **SC-003**: Statistical significance of the adaptive strategy is measured by the p-value from a paired t-test comparing it to the pre-specified fixed baseline ($\rho=0.5$) (See US-3).
- **SC-004**: The stability of the identified critical threshold is measured by the rate of accuracy degradation in the sensitivity analysis sweep (See US-3).
- **SC-005**: Computational feasibility is measured by the total wall-clock time of the full experiment suite against the 6-hour limit (See US-1, US-2).
- **SC-006**: System success is defined as the generation of all required output artifacts (JSON/CSV result files, regression coefficients, t-test statistics) in the specified format without runtime errors (See US-1, US-2, US-3).

## Assumptions

- **Assumption about dataset variables**: The GSM8K and `bigbench_lite` subsets contain sufficient ground-truth reasoning chains to serve as an independent gold standard for evaluating "logical accuracy" without requiring additional annotation.
- **Assumption about model tractability**: A pre-trained discrete diffusion model with ≤100M parameters is available on HuggingFace and can perform inference on a 2-core CPU within the 6-hour window without requiring GPU acceleration or 8-bit quantization.
- **Assumption about inference framing**: The study is observational regarding the density-performance relationship; findings will be framed as associational (correlation between density and accuracy) rather than causal, as no random assignment of density to specific reasoning tasks is performed in the training loop.
- **Assumption about threshold justification**: The heuristic for the adaptive scheduler is based on the community-standard assumption that higher prediction entropy correlates with higher uncertainty, necessitating denser supervision; this rationale is sufficient for the initial prototype.
- **Assumption about power and multiplicity**: The sample size (number of fixed ratios = 5) is limited by the 6-hour runtime constraint; while this limits statistical power for detecting small effects, the use of a paired t-test on the adaptive run vs. the pre-specified baseline (ρ=0.5) is the most rigorous approach feasible within the compute budget.
- **Assumption about measurement validity**: The "logical accuracy" metric derived from exact string matching of reasoning steps on GSM8K is a valid proxy for the emergence of reasoning capabilities in this specific diffusion context.