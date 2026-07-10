# Feature Specification: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

**Feature Branch**: `001-astrocyte-meta-learning`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks - Investigating homeostatic plasticity mechanisms modeled after astrocyte calcium signaling to influence the stability-plasticity trade-off in few-shot meta-learning tasks using MAML on Omniglot and Mini-ImageNet."

## User Scenarios & Testing

### User Story 1 - Core Meta-Learning with Astrocyte Modulation (Priority: P1)

**Journey**: A researcher runs the meta-learning training pipeline on the Omniglot dataset. The system loads the MAML baseline, injects the astrocyte-inspired homeostatic module (based on the calcium-wave ODE with task-history memory), and executes a training run in a Task-Incremental Learning regime. The system logs stability (forgetting on the immediately preceding task) and plasticity (adaptation speed on current tasks) metrics for every episode, derived strictly from **actual forward passes and accuracy calculations** on held-out query sets.

**Why this priority**: This is the fundamental experiment described in the idea. Without the ability to run the modified MAML algorithm and record the core metrics via real computation, the research question cannot be answered. It represents the Minimum Viable Product (MVP) of the research.

**Independent Test**: Can be fully tested by executing the training script for a **validation subset of 100 episodes** (for debugging and protocol validation only, distinct from the full run) and verifying that the output logs contain both "plasticity" and "stability" metrics alongside the standard MAML loss, calculated from **real model evaluations on query sets**, without requiring the statistical comparison or ablation studies. The test validates the *mechanism* of metric generation on the subset.

**Acceptance Scenarios**:

1. **Given** the Omniglot dataset is available and the MAML configuration is set to 5-way 1-shot, **When** the training script runs with the astrocyte module enabled in Task-Incremental mode, **Then** the system executes the training episodes and generates a log file containing `plasticity_score` and `stability_score` for each episode, where these scores are derived from **actual model accuracy measurements** on the respective query sets.
2. **Given** the training is running, **When** the simulation encounters a new task, **Then** the homeostatic factor $h_t$ is calculated using the calcium ODE (which incorporates a running average of past task activations from a persistent buffer) and applied as a multiplicative modifier to the inner-loop learning rate before the gradient update.
3. **Given** the training completes, **When** the results are saved, **Then** the `results/` folder contains a JSON or CSV file with the full time-series of metrics for the specific random seed used, containing only values computed from real model inference.

---

### User Story 2 - Baseline Comparison and Statistical Validation (Priority: P2)

**Journey**: A researcher compares the performance of the astrocyte-modulated model against the vanilla MAML baseline. The system runs both configurations across multiple random seeds in the *exact same* Task-Incremental protocol, aggregates the final stability and plasticity metrics, and performs a **multivariate paired t-test (Hotelling's T²)** to determine if the joint distribution of metrics differs significantly, accounting for the covariance between stability and plasticity.

**Methodological Justification**: The spec adheres to the Project Constitution (Principle VII) which mandates paired-sample t-tests. To address the stability-plasticity trade-off and control for the statistical dependency between the two metrics (as they arise from the same weight update), a **multivariate paired t-test (Hotelling's T²)** is performed. This tests the joint hypothesis that the mean vector of differences is zero, correcting for the correlation structure. This ensures valid hypothesis testing without violating the constitutional mandate or the independence assumptions of univariate tests.

**Why this priority**: This validates the hypothesis. While the core model (US-1) runs, the scientific value is only realized when the improvement (or lack thereof) is statistically quantified against a control, accounting for the trade-off between stability and plasticity.

**Independent Test**: Can be tested by providing two result files (one for baseline, one for astrocyte) containing paired vectors of [Stability, Plasticity] from real model evaluations and verifying that the analysis script correctly computes the Hotelling's T² statistic and the associated p-value (with degrees of freedom adjusted for the covariance), outputting a clear "Significant", "Not Significant", or "Inconclusive" verdict.

**Acceptance Scenarios**:

1. **Given** two result files containing stability and plasticity metrics from 20 independent seeds for both baseline and astrocyte models (both run in Task-Incremental mode), **When** the evaluation script runs, **Then** it outputs a Hotelling's T² result for the joint (Stability, Plasticity) vector and a p-value adjusted for the covariance structure.
2. **Given** the analysis is complete, **When** the report is generated, **Then** it explicitly states whether the astrocyte model reduced catastrophic forgetting (higher stability) while preserving plasticity, citing the specific p-value or reason for inconclusiveness based on the multivariate test.
3. **Given** the analysis is complete, **When** the report is generated, **Then** it explicitly states whether the joint distribution of metrics differs significantly from the baseline, citing the specific p-value or reason for inconclusiveness.

---

### User Story 3 - Sensitivity Analysis and Ablation (Priority: P3)

**Journey**: A researcher investigates the robustness of the findings by varying the strength of the homeostatic factor (scale parameter) and replacing the dynamic calcium ODE with a constant term. The system runs these ablation studies and reports how the headline metrics change across different parameter values.

**Why this priority**: This addresses the "threshold justification and sensitivity" methodological requirement. It ensures the results are not an artifact of a single arbitrary parameter choice, adding rigor to the conclusion.

**Independent Test**: Can be tested by running the training script with a specific list of scale parameters (e.g., `[0.01, 0.05, 0.1]`) and verifying that the output includes a summary table showing the stability/plasticity trade-off for each parameter value.

**Acceptance Scenarios**:

1. **Given** a list of homeostatic scale parameters, **When** the ablation script runs, **Then** it executes the training loop for each parameter value and records the final stability and plasticity scores derived from real model evaluations.
2. **Given** the ablation results are collected, **When** the summary is generated, **Then** it presents a sensitivity sweep showing how the false-positive (forgetting) rate varies as the scale parameter changes.
3. **Given** the ablation script is configured to replace the ODE, **When** the "constant homeostatic" mode is enabled, **Then** the system substitutes the dynamic calcium calculation with a fixed scalar and logs the resulting performance difference.

### Edge Cases

- What happens if the calcium ODE solver diverges (e.g., due to extreme gradient values)? The system must clamp the calcium concentration to a safe range $[0, 1]$ and log a warning rather than crashing.
- How does the system handle a dataset download failure? The script must retry the download up to 3 times with exponential backoff before failing the job with a clear error message.
- What if the random seed produces a task distribution where the baseline MAML fails completely (accuracy ~0)? The system must still compute the multivariate t-test (handling variance issues if necessary) and report the result as "undefined" or "baseline failure" rather than crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement the calcium-wave ODE from the Polykretis et al. (2018) model as a differentiable PyTorch module. The ODE MUST accept activation signals from the current task and a **persistent task-history buffer** (stored in CPU memory) containing a running average of past task activations (mean squared activation per layer) to compute a per-neuron calcium concentration. This buffer MUST be updated **after** the completion of each task episode and used to compute the homeostatic factor $h_t$ for the **subsequent** task. The mapping from calcium concentration to learning rate scalar is defined by the hypothesis $h_t = \exp(-\lambda \cdot Ca_t)$, where $\lambda$ is a configurable parameter. **Justification**: The exponential decay form is chosen to model the rapid saturation of calcium-dependent inhibition observed in biological astrocytes, distinguishing it from linear or sigmoidal alternatives. (See US-1)
- **FR-002**: System MUST integrate the scalar homeostatic factor $h_t$ into the MAML inner-loop update rule by multiplying the learning rate or gradient step size before the parameter update for the entire layer. (See US-1)
- **FR-003**: System MUST calculate and log two distinct metrics per episode in a Task-Incremental Learning regime (where tasks are presented sequentially **without re-initialization of model weights**): (1) **Plasticity** defined as the **mean accuracy on the current task averaged over the first 5 gradient steps**, and (2) **Stability** defined as the accuracy on the **immediately preceding task (N-1) measured on a distinct, held-out validation set that was NOT used in the gradient update of Task N**. **To compute Stability, the query set for the previous task (N-1) MUST be retained in memory (held-out) and evaluated after the update for the current task.** All metric values MUST be computed via **actual forward passes** on the respective query sets; no synthetic, placeholder, hardcoded, or simulated values are permitted. (See US-1)
- **FR-004**: System MUST execute the training protocol for **20** episodes on Omniglot and Mini-ImageNet, using 5-way 1-shot tasks, across **20** independent training runs, each with a distinct random seed. **Justification**: The Idea specifies "10k episodes" as a target scale; the exact number is set to 20 to ensure statistical power (n≥20 seeds) for the validation tests while remaining tractable for the specified compute budget. (See US-2)
- **FR-005**: System MUST perform a **multivariate paired t-test (Hotelling's T²)** comparing the joint vector of Stability and Plasticity metrics between the astrocyte-modulated model and the vanilla MAML baseline across the **20** seeds. Both models MUST be evaluated under the **exact same Task-Incremental protocol**. **Statistical Protocol**: A single multivariate test is conducted on the difference vector $(\Delta \text{Stability}, \Delta \text{Plasticity})$ to account for the covariance between the two metrics arising from the shared weight update. The significance threshold is set to **$\alpha = 0.05$**. If the covariance matrix is singular, the system MUST apply a ridge penalty ($\lambda = 10^{-6}$). If statistical power is insufficient (calculated power < 0.80), the result MUST be reported as "inconclusive" with `verdict: 'inconclusive'`, `reason: 'insufficient_power'`, and `confidence_interval: null`. **All metrics MUST be derived from real model evaluations on query sets; no synthetic, placeholder, or simulated metrics are permitted.** (See US-2)
- **FR-006**: System MUST support a sensitivity analysis mode that accepts a configurable list of homeostatic scale parameters, sweeps the training loop for each value, and reports the variation in stability/plasticity rates. (See US-3)
- **FR-007**: System MUST replace the dynamic calcium ODE with a constant homeostatic term when the "ablation" flag is set, to isolate the effect of dynamic signaling. (See US-3)
- **FR-008**: System MUST handle cases of insufficient statistical power (calculated power < 0.80) by outputting a structured result with `verdict: 'inconclusive'`, `reason: 'insufficient_power'`, and `confidence_interval: null`, ensuring the output format is consistent with the requirements in FR-005. (See US-2)

### Key Entities

- **Task Episode**: A single 5-way 1-shot classification problem instance, containing a support set and a query set.
- **Homeostatic State**: The internal simulation state of the astrocyte module, specifically the calcium concentration $Ca_t$ (derived from current and historical activations) and the derived scalar factor $h_t$.
- **Performance Metric**: A structured record containing the task ID, seed ID, plasticity score, stability score (measured on the previous task's held-out validation set), and the specific hyperparameters used for that run.
- **Task-History Buffer**: A persistent state object stored in CPU memory that accumulates activation statistics (mean squared activation) after each completed task episode, used to compute the running average for the ODE in subsequent tasks.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in the joint vector of **Stability** and **Plasticity** between the astrocyte-modulated model and the vanilla MAML baseline is measured against the null hypothesis of no difference using **Hotelling's T² (multivariate paired t-test)** with $\alpha = 0.05$. If power is insufficient, the result is recorded as "inconclusive" (See US-2).
- **SC-002**: The variation in the **Stability** and **Plasticity** metrics across the homeostatic scale parameter set **{0.01, 0.05, 0.1}** is measured to determine the sensitivity of the method to threshold choices (See US-3).

## Assumptions

- The `torchvision` and `huggingface/datasets` repositories provide stable, direct download URLs for the Omniglot and Mini-ImageNet datasets that do not require complex authentication or GPU-specific loaders.
- The "calcium-wave ODE" from Polykretis et al. (2018) can be implemented in PyTorch using standard `torch.autograd` operations without requiring custom CUDA kernels or external C++ extensions, ensuring CPU-only compatibility.
- The training budget on Mini-ImageNet will complete within the GitHub Actions free-tier limit when using a CPU-only runner.; if not, the implementation will default to a subset of the dataset as a CPU-tractable approximation.
- The "homeostatic factor" $h_t$ will be applied as a multiplicative scalar to the learning rate, consistent with standard homeostatic plasticity models, rather than a more complex structural change to the network architecture.
- The dataset variables (images and labels) are sufficient for the few-shot classification task; no external variables (e.g., cognitive state, behavioral data) are required as the study is purely algorithmic.
- A set of **20** random seeds is sufficient to detect a moderate effect size in the multivariate t-tests; if power is insufficient, the result will be reported as "inconclusive" as defined in FR-008.
- The default sensitivity analysis sweep parameters are set to the set $\{0.01, 0.05, 0.1\}$ as a community-standard starting range for homeostatic scale factors.
- **Resource Constraints**: The Computation Time per episode run is expected to be within the GitHub Actions free-tier limit, and the Memory Footprint is expected to be within the available RAM limit.
