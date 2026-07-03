# Feature Specification: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

**Feature Branch**: `001-astrocyte-meta-learning`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks - Investigating homeostatic plasticity mechanisms modeled after astrocyte calcium signaling to influence the stability-plasticity trade-off in few-shot meta-learning tasks using MAML on Omniglot and Mini-ImageNet."

## User Scenarios & Testing

### User Story 1 - Core Meta-Learning with Astrocyte Modulation (Priority: P1)

**Journey**: A researcher runs the meta-learning training pipeline on the Omniglot dataset. The system loads the MAML baseline, injects the astrocyte-inspired homeostatic module (based on the calcium-wave ODE with task-history memory), and executes a configurable number of training episodes (default: [deferred]). The system logs stability (forgetting on older tasks) and plasticity (adaptation speed on current tasks) metrics for every episode.

**Why this priority**: This is the fundamental experiment described in the idea. Without the ability to run the modified MAML algorithm and record the core metrics, the research question cannot be answered. It represents the Minimum Viable Product (MVP) of the research.

**Independent Test**: Can be fully tested by executing the training script for a fixed number of episodes (e.g., 100) and verifying that the output logs contain both "plasticity" and "stability" metrics alongside the standard MAML loss, without requiring the statistical comparison or ablation studies.

**Acceptance Scenarios**:

1. **Given** the Omniglot dataset is available and the MAML configuration is set to 5-way 1-shot, **When** the training script runs with the astrocyte module enabled, **Then** the system completes the specified number of episodes (default [deferred]) and generates a log file containing `plasticity_score` and `stability_score` for each episode.
2. **Given** the training is running, **When** the simulation encounters a new task, **Then** the homeostatic factor $h_t$ is calculated using the calcium ODE (which incorporates a running average of past task activations) and applied as a multiplicative modifier to the inner-loop learning rate before the gradient update.
3. **Given** the training completes, **When** the results are saved, **Then** the `results/` folder contains a JSON or CSV file with the full time-series of metrics for the specific random seed used.

---

### User Story 2 - Baseline Comparison and Statistical Validation (Priority: P2)

**Journey**: A researcher compares the performance of the astrocyte-modulated model against the vanilla MAML baseline. The system runs both configurations across 5 random seeds, aggregates the final stability and plasticity metrics, and performs a Hotelling's T-squared test to determine if the joint distribution of metrics differs significantly (p < 0.05).

**Why this priority**: This validates the hypothesis. While the core model (US-1) runs, the scientific value is only realized when the improvement (or lack thereof) is statistically quantified against a control, accounting for the trade-off between stability and plasticity.

**Independent Test**: Can be tested by providing two result files (one for baseline, one for astrocyte) containing paired vectors of [Stability, Plasticity] and verifying that the analysis script correctly computes the Hotelling's T-squared statistic and p-value, outputting a clear "Significant" or "Not Significant" verdict.

**Acceptance Scenarios**:

1. **Given** two result files containing stability and plasticity metrics from 5 independent seeds for both baseline and astrocyte models, **When** the evaluation script runs, **Then** it outputs a Hotelling's T-squared test result with a p-value and a boolean indicating if $p < 0.05$.
2. **Given** the analysis is complete, **When** the report is generated, **Then** it explicitly states whether the astrocyte model reduced catastrophic forgetting (higher stability) compared to the baseline, citing the specific p-value.
3. **Given** the analysis is complete, **When** the report is generated, **Then** it explicitly states whether the astrocyte model preserved or improved adaptation speed (plasticity) compared to the baseline, considering the joint metric distribution.

---

### User Story 3 - Sensitivity Analysis and Ablation (Priority: P3)

**Journey**: A researcher investigates the robustness of the findings by varying the strength of the homeostatic factor (scale parameter) and replacing the dynamic calcium ODE with a constant term. The system runs these ablation studies and reports how the headline metrics change across different parameter values.

**Why this priority**: This addresses the "threshold justification and sensitivity" methodological requirement. It ensures the results are not an artifact of a single arbitrary parameter choice, adding rigor to the conclusion.

**Independent Test**: Can be tested by running the training script with a specific list of scale parameters (e.g., `[0.01, 0.05, 0.1]`) and verifying that the output includes a summary table showing the stability/plasticity trade-off for each parameter value.

**Acceptance Scenarios**:

1. **Given** a list of homeostatic scale parameters, **When** the ablation script runs, **Then** it executes the training loop for each parameter value and records the final stability and plasticity scores.
2. **Given** the ablation results are collected, **When** the summary is generated, **Then** it presents a sensitivity sweep showing how the false-positive (forgetting) rate varies as the scale parameter changes.
3. **Given** the ablation script is configured to replace the ODE, **When** the "constant homeostatic" mode is enabled, **Then** the system substitutes the dynamic calcium calculation with a fixed scalar and logs the resulting performance difference.

### Edge Cases

- What happens if the calcium ODE solver diverges (e.g., due to extreme gradient values)? The system must clamp the calcium concentration to a safe range $[0, 1]$ and log a warning rather than crashing.
- How does the system handle a dataset download failure? The script must retry the download up to 3 times with exponential backoff before failing the job with a clear error message.
- What if the random seed produces a task distribution where the baseline MAML fails completely (accuracy ~0)? The system must still compute the Hotelling's T-squared test (handling covariance matrix singularity if necessary) and report the result as "undefined" or "baseline failure" rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the calcium-wave ODE from the Polykretis et al. (2018) model as a differentiable PyTorch module. The ODE MUST accept activation signals from the current task and a running average of past task activations (task-history buffer) to compute a per-neuron calcium concentration, which is then aggregated via mean to produce a single scalar homeostatic factor $h_t$ per layer. (See US-1)
- **FR-002**: System MUST integrate the scalar homeostatic factor $h_t$ into the MAML inner-loop update rule by multiplying the learning rate or gradient step size before the parameter update for the entire layer. (See US-1)
- **FR-003**: System MUST calculate and log two distinct metrics per episode: (1) Plasticity (accuracy on current task after 1, 5, 10 steps) and (2) Stability (accuracy on a held-out buffer of older tasks, not just the immediate predecessor, after training on the current task). (See US-1)
- **FR-004**: System MUST execute the training protocol for [deferred] episodes on Omniglot and Mini-ImageNet, using 5-way 1-shot tasks, across 5 independent training runs, each with a distinct random seed. (See US-2)
- **FR-005**: System MUST perform a Hotelling's T-squared test comparing the joint [Stability, Plasticity] metric vectors of the astrocyte-modulated model against the vanilla MAML baseline across the 5 seeds, outputting p-values. (See US-2)
- **FR-006**: System MUST support a sensitivity analysis mode that accepts a configurable list of homeostatic scale parameters, sweeps the training loop for each value, and reports the variation in stability/plasticity rates. (See US-3)
- **FR-007**: System MUST replace the dynamic calcium ODE with a constant homeostatic term when the "ablation" flag is set, to isolate the effect of dynamic signaling. (See US-3)

### Key Entities

- **Task Episode**: A single 5-way 1-shot classification problem instance, containing a support set and a query set.
- **Homeostatic State**: The internal simulation state of the astrocyte module, specifically the calcium concentration $Ca_t$ (derived from current and historical activations) and the derived scalar factor $h_t$.
- **Performance Metric**: A structured record containing the task ID, seed ID, plasticity score, stability score (measured on older tasks), and the specific hyperparameters used for that run.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in the **joint [Stability, Plasticity] vector** between the astrocyte-modulated model and the vanilla MAML baseline is measured against the null hypothesis of no difference using a Hotelling's T-squared test (See US-2).
- **SC-002**: The variation in the **joint [Stability, Plasticity] vector** across the homeostatic scale parameter set (default: {0.01, 0.05, 0.1}) is measured to determine the sensitivity of the method to threshold choices (See US-3).
- **SC-003**: The **Computation Time** per episode run is measured against the GitHub Actions free-tier limit of 6 hours to ensure feasibility (See Assumptions).
- **SC-004**: The **Memory Footprint** of the training process is measured against the 7 GB RAM limit of the GitHub Actions runner to ensure the dataset and model fit (See Assumptions).

## Assumptions

- The `torchvision` and `huggingface/datasets` repositories provide stable, direct download URLs for the Omniglot and Mini-ImageNet datasets that do not require complex authentication or GPU-specific loaders.
- The "calcium-wave ODE" from Polykretis et al. (2018) can be implemented in PyTorch using standard `torch.autograd` operations without requiring custom CUDA kernels or external C++ extensions, ensuring CPU-only compatibility.
- The training budget on Mini-ImageNet will complete within the GitHub Actions free-tier limit. when using a CPU-only runner; if not, the implementation will default to a subset of the dataset (e.g., [deferred] episodes) as a CPU-tractable approximation.
- The "homeostatic factor" $h_t$ will be applied as a multiplicative scalar to the learning rate, consistent with standard homeostatic plasticity models, rather than a more complex structural change to the network architecture.
- The dataset variables (images and labels) are sufficient for the few-shot classification task; no external variables (e.g., cognitive state, behavioral data) are required as the study is purely algorithmic.
- The statistical power of multiple random seeds is sufficient to detect a moderate effect size (Cohen's d ≈ 0.5) in the multivariate test.; if power is insufficient, the result will be reported as "inconclusive" rather than false-negative.
- The default sensitivity analysis sweep parameters are set to the set $\{0.01, 0.05, 0.1\}$ as a community-standard starting range for homeostatic scale factors.