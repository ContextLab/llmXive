# Feature Specification: Dendritic Computation in Transformers: Beyond Point Neurons

**Feature Branch**: `001-dendritic-computation-in-transformers`  
**Created**: 2026-06-08  
**Status**: Draft  
**Input**: User description: "Do artificial neurons with biologically realistic dendritic compartmentalization enable more efficient hierarchical feature detection in transformer architectures compared to standard point-neuron designs, when trained on equivalent natural-language or visual tasks?"

## User Scenarios & Testing

### User Story 1 - Implement and Match Baseline Architectures (Priority: P1)

As a researcher, I need a baseline transformer using standard point-neuron feedforward layers and a variant using dendritic compartmentalization (local nonlinearities, plateau potentials) with strictly matched parameter counts and FLOPs per forward pass, so that I can isolate the effect of dendritic mechanics from raw model capacity.

**Why this priority**: Without a rigorously controlled baseline and variant with identical computational budgets, any observed difference in performance could be attributed to parameter count or FLOP disparity rather than the dendritic mechanism. This is the foundational step for all subsequent analysis.

**Independent Test**: Can be fully tested by instantiating both models with a fixed random seed, running a single forward pass on a dummy batch, and verifying via a script that the total parameter count differs by <0.1% and the theoretical FLOP count (calculated via `torchinfo` or equivalent) differs by <1%.

**Acceptance Scenarios**:

1. **Given** a standard transformer encoder configuration, **When** the system generates the dendritic variant by replacing feedforward layers with compartmentalized units, **Then** The parameter count of both models must be identical within a tight tolerance, and the FLOP count per forward pass must match within a minimal tolerance.
2. **Given** the two model definitions, **When** a forward pass is executed on a batch of random tokens, **Then** the system must log the exact FLOP count and parameter count for both models, confirming they are within the defined matching thresholds.

---

### User Story 2 - Train and Evaluate on Standard Benchmarks (Priority: P2)

As a researcher, I need to train both the baseline and dendritic variants on a standard benchmark (GLUE SST-2) for a fixed wall-clock time (≤6 hours) on CPU-only hardware (2 CPU cores, 7GB RAM), recording accuracy and loss curves, so that I can compare sample efficiency and convergence behavior.

**Why this priority**: This story validates whether the dendritic mechanism actually provides an advantage in learning efficiency under realistic resource constraints. It moves from theoretical architecture to empirical evidence.

**Independent Test**: Can be fully tested by running the training script on the specified hardware constraints (2 CPU cores, 7GB RAM), ensuring the job completes or is stopped within 6 hours, and verifying that the output logs contain accuracy and loss metrics for both models at regular intervals (e.g., every 100 steps).

**Acceptance Scenarios**:

1. **Given** the matched baseline and dendritic models, **When** training is initiated on the GLUE sentiment analysis dataset with identical optimization schedules, **Then** the The research question is whether the system can enforce a hard stop within a practical time window on a CPU-only runner (limited compute resources). The method involves implementing a runtime timeout mechanism to terminate execution if the process exceeds this threshold. References: [Citation Placeholder]. and save checkpoint files for both models to enable downstream probing (See US-3).
2. **Given** the training logs, **When** the system extracts the accuracy at the final step or hard stop, **Then** the dendritic model's accuracy must be reported alongside the baseline's accuracy, allowing for a direct numerical comparison.

---

### User Story 3 - Perform Hierarchical Feature Probing and Statistical Analysis (Priority: P3)

As a researcher, I need to train linear classifiers on intermediate layer representations (probing) for each layer individually and perform paired statistical tests (e.g., Wilcoxon signed-rank) across multiple random seeds to determine if the dendritic variant yields superior hierarchical feature detection or sample efficiency.

**Why this priority**: This story addresses the core research question regarding "hierarchical feature detection" and provides the statistical rigor required to claim a significant difference, moving beyond anecdotal observation.

**Independent Test**: Can be fully tested by running the probing script on the saved checkpoints from multiple seeds, generating p-values and effect sizes for each layer, and verifying that the results are stored in a structured format (e.g., JSON or CSV) for review.

**Acceptance Scenarios**:

1. **Given** the trained checkpoints from 3-5 random seeds, **When** linear probes are trained on intermediate layer representations for syntactic/semantic tasks for each layer individually, **Then** the system must output the probing accuracy for each layer and each seed for both model types.
2. **Given** the collection of probing accuracies and sample-efficiency metrics, **When** a paired statistical test is performed on the per-layer results, **Then** the system must report a p-value and effect size, explicitly stating whether the difference is statistically significant at α=0.05.

---

### Edge Cases

- **What happens when** the dendritic nonlinearity causes gradient explosion during training? The system must implement gradient clipping (threshold ≤ 1.0) and log the frequency of clipped gradients to ensure training stability without masking the architectural effect.
- **How does the system handle** a scenario where the dendritic variant converges slower initially but overtakes the baseline later? The statistical analysis must include time-series comparison (e.g., area under the learning curve) rather than just final accuracy.
- **What happens when** the CPU-only constraint causes the training to exceed 6 hours before convergence? The system must enforce a hard stop at 6 hours and report the final state as "incomplete," ensuring fair comparison by stopping both models at the same wall-clock time.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a dendritic transformer variant where feedforward layers are replaced by compartmentalized units featuring local nonlinearities and plateau potential gating, ensuring the architecture is distinct from standard point-neuron MLPs (See US-1).
- **FR-002**: System MUST enforce strict parameter and FLOP matching between the baseline and dendritic variants, with a tolerance of <0.1% for parameters and <1% for FLOPs, to ensure fair comparison (See US-1).
- **FR-003**: System MUST train both model variants on the GLUE SST-2 benchmark for a maximum of 6 hours on CPU-only hardware (2 cores, 7GB RAM), recording accuracy and loss curves at regular intervals (See US-2).
- **FR-004**: System MUST implement a probing analysis pipeline that trains linear classifiers on intermediate layer representations to measure hierarchical feature quality across multiple random seeds (3-5 seeds) (See US-3).
- **FR-005**: System MUST perform paired statistical tests (e.g., Wilcoxon signed-rank or paired t-tests) on sample efficiency and probing accuracy metrics across seeds, reporting p-values and effect sizes (See US-3).
- **FR-006**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) when evaluating per-layer statistical tests to control family-wise error rate, as required for methodological validity in hierarchical analysis (See US-3).
- **FR-007**: System MUST include a sensitivity analysis for the dendritic nonlinearity threshold, sweeping the cutoff over a set of values (e.g., low, moderate, and high thresholds) and reporting the variance in probing accuracy and stability of effect sizes to validate the robustness of the dendritic advantage (See US-3).

### Key Entities

- **Dendritic Unit**: A computational unit replacing the standard neuron, containing sub-units (branches) with local nonlinearities and a global soma that integrates these signals via plateau potentials.
- **Probing Task**: A downstream linear classification task applied to frozen intermediate representations to assess the quality of learned features (e.g., part-of-speech tagging, semantic role labeling).
- **Training Run**: A single execution of the training process for one model variant on one random seed, bounded by a 6-hour wall-clock limit.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in final accuracy between the dendritic and baseline models is measured against the null hypothesis of no difference using a paired t-test or Wilcoxon signed-rank test across multiple seeds (See US-2, US-3).
- **SC-002**: The sample efficiency (steps to reach % of the baseline model's final accuracy) is measured against the baseline model's steps, with the reduction measured relative to the baseline (See US-2).
- **SC-003**: The hierarchical feature detection capability is measured by the probing accuracy on intermediate layers, comparing the area under the accuracy-vs-depth curve for dendritic vs. baseline models (See US-3).
- **SC-004**: The robustness of the dendritic advantage is measured by the stability of the effect size across the sensitivity analysis of the nonlinearity threshold (See US-3).
- **SC-005**: The computational cost is measured by the wall-clock time to convergence or hard stop, ensuring it remains ≤6 hours on the specified CPU-only hardware (See US-2).

## Assumptions

- The public benchmark datasets (e.g., GLUE SST-2) contain all necessary variables (input tokens, labels) for training and evaluation, and no external data collection is required.
- The dendritic compartmentalization mechanism can be implemented using standard PyTorch operations without requiring CUDA or GPU acceleration, fitting within the available RAM constraint.
- The "local nonlinearities" and "plateau potentials" described in the literature can be approximated by a differentiable function (e.g., a two-layer sub-network with a gating mechanism) that is computationally tractable on CPU.
- A wall-clock time limit on GitHub Actions free-tier runners (2 CPU cores, 7GB RAM) is sufficient to train both model variants to a stable state on the GLUE SST-2 dataset subset.
- The statistical power provided by 3-5 random seeds is sufficient to detect a meaningful effect size (d ≥ 0.5) given the expected variance in training dynamics.
- The sensitivity analysis for the dendritic threshold will be performed on a small, representative subset of the data to ensure CPU feasibility, as sweeping over the full dataset for every threshold value is computationally prohibitive.
- The "matched FLOPs" assumption holds that the overhead of the dendritic sub-units (e.g., extra gating logic) is negligible compared to the main matrix multiplications, allowing for a fair comparison of parameter count.