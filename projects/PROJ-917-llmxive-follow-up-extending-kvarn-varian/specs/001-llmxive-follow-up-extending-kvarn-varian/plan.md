# Implementation Plan: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Branch**: `001-llmxive-kvarn-static-prior` | **Date**: 2026-07-10 | **Spec**: `specs/001-llmxive-follow-up-extending-kvarn-varian/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-kvarn-varian/spec.md`

## Summary

This project investigates whether the mapping from input attention statistics (mean, variance, skewness, kurtosis) to optimal variance-normalization scaling factors (derived via **Sequential** KVarN Sinkhorn optimization) is learnable via a static prior (2-layer MLP). The goal is to eliminate the iterative optimization step in long-horizon autoregressive generation to reduce latency while maintaining accuracy.

**Key Methodological Update**: Unlike a static analysis, this project models the **temporal evolution** of attention statistics. We generate synthetic **trajectories** (sequences of [deferred] steps) where variance and higher-order moments drift to simulate error accumulation. The ground truth is computed using a **Sequential Sinkhorn Solver** that maintains a cumulative error state, ensuring the "long-horizon" aspect is modeled dynamically. The static prior is trained on these trajectories and evaluated against a Sequential Baseline and an **Analytical Noise Floor** (independent ground truth).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (for Sinkhorn), `torch` (CPU-only, version pinned to CPU wheels), `scikit-learn`, `pandas`, `pyarrow` (for Parquet), `pytest`, `matplotlib`  
**Storage**: Local filesystem (`data/`, `code/`); Parquet/JSON/CSV for artifacts.  
**Testing**: `pytest` (unit tests for data generation, model training, simulation logic; integration tests for full pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Research artifact (Python scripts, simulation engine, analysis notebooks).  
**Performance Goals**: Total runtime ≤ 6 hours; memory usage < 6 GB during peak simulation; per-token latency reduction target: significant improvement vs. Sequential Sinkhorn.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization libraries requiring CUDA; all data must fit in RAM; Sequential Sinkhorn solver must be optimized for CPU (e.g., using `scipy.optimize` or a custom NumPy implementation).  
**Scale/Scope**: 10,000 synthetic attention **trajectories** ([deferred] steps each) for training; multiple independent simulation runs of sufficient steps each.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and re-runnable scripts. Data fetched/generated deterministically. |
| **II. Verified Accuracy** | ✅ | Plan restricts dataset citations to the "Verified datasets" block (none for KVarN, synthetic for others). No external URLs invented. |
| **III. Data Hygiene** | ✅ | Plan requires checksumming of generated data (`data/`), immutable raw data, and new filenames for derivations. |
| **IV. Single Source of Truth** | ✅ | Plan defines `data/` as the source for all figures/statistics in the final report. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ | Plan includes content hashes for artifacts and updates `state/` timestamps on changes. |
| **VI. Numerical Stability** | ✅ | Plan explicitly addresses epsilon floors (FR-007) and tracks accumulated KL-divergence [deferred] steps with paired t-tests (FR-006). |
| **VII. Hardware-Aware Profiling** | ✅ | Plan mandates wall-clock timing on CPU-only hardware, isolating the Sinkhorn overhead. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-kvarn-static-prior/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── data_generation/
│   ├── __init__.py
│   ├── synthetic_attention.py   # Generates 128x128 trajectories + Sequential Sinkhorn labels
│   └── utils.py                 # Moment extraction, epsilon handling, drift models
├── model_training/
│   ├── __init__.py
│   ├── mlp_model.py             # 2-layer MLP definition (4 inputs: mean, var, skew, kurt)
│   ├── train.py                 # Training loop, MSE reporting
│   └── baselines.py             # Closed-form s = 1/variance
├── simulation/
│   ├── __init__.py
│   ├── autoregressive_loop.py   # -step simulation engine with cumulative error state
│   ├── kl_divergence.py         # Error accumulation logic
│   ├── profiler.py              # Wall-clock timing
│   └── sequential_sinkhorn.py   # Sequential Sinkhorn solver with state update
├── analysis/
│   ├── __init__.py
│   ├── stats.py                 # Paired t-test, sensitivity analysis, theoretical lower bound
│   └── visualizations.py        # Plotting accumulated error vs. steps
├── tests/
│   ├── test_data_generation.py
│   ├── test_model_training.py
│   └── test_simulation.py
├── main.py                      # Orchestration script
└── requirements.txt             # Pinned dependencies
```

**Structure Decision**: Single project structure (`code/` root) selected. The workflow is linear: Data Generation -> Model Training -> Simulation -> Analysis. This avoids unnecessary abstraction layers (e.g., separate services) and fits the research artifact nature of the project.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Sequential Sinkhorn** | Required to model the feedback loop of quantization error [deferred] steps. | A static Sinkhorn solver would fail to capture the "long-horizon" error accumulation, invalidating the core research question. |
| **Trajectory Generation** | Required to match the dynamic distribution of the simulation. | Static i.i.d. generation would create a distribution shift between training and evaluation, leading to invalid results. |
| **Higher-Order Moments** | Required to test non-trivial learnability beyond $s=1/\sigma^2$. | Using only mean/variance would risk a null result where the MLP learns nothing beyond the closed-form baseline. |
| **Real-World Proxy** | Required to validate generalization beyond synthetic data. | Relying solely on synthetic data creates a "sim-to-sim" loop that may not generalize to real LLMs. |
| **Theoretical Lower Bound** | Required to break circular validation. | Comparing only against Sinkhorn creates a tautological validation where the static prior is only as good as the Sinkhorn solver's definition of optimality. |
| **None** | The scope is strictly bounded by the spec (synthetic trajectories, 2-layer MLP, 1k steps). The 6-hour CPU limit is tight but manageable with efficient NumPy/PyTorch CPU usage. | N/A |

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate 10,000 synthetic **attention trajectories** (sequences of [deferred] steps each, 128x128 per step) with controlled sparsity, outlier magnitudes, and **temporal drift** in statistical moments. For each step, the system MUST compute ground-truth scaling factors using a **Sequential Sinkhorn Optimizer** that maintains a cumulative error state from previous steps in the trajectory. (See US-1)
- **FR-002**: The system MUST train a multi-layer perceptron (MLP) on a CPU using **four input features** (mean, variance, skewness, kurtosis) of input attention matrices to predict the ground-truth scaling factors, minimizing Mean Squared Error. (See US-2)
- **FR-003**: The system MUST simulate an autoregressive decoding loop of [deferred] steps, where the static prior replaces the iterative Sinkhorn optimization for variance normalization, **processing full trajectories** rather than independent steps. (See US-3)
- **FR-004**: The system MUST measure and record the **accumulated KL-divergence** between the quantized output distribution and the full-precision distribution at each step of the simulation, explicitly tracking the **cumulative error state** propagated from previous steps. (See US-3)
- **FR-005**: The system MUST profile and report the wall-clock time per token for both the static prior method and the original KVarN method on the same CPU hardware. (See US-3)
- **FR-006**: The system MUST perform a paired t-test on the final accumulated KL-divergence (scalar value) across multiple independent runs (n=30) to determine statistical significance (p < 0.05). (See US-3)
- **FR-007**: The system MUST implement a sensitivity analysis that sweeps the epsilon floor for variance normalization over a set of values and reports how the accumulated KL-divergence error rate varies. (See US-2, US-3)
- **FR-008**: The system MUST compute and report the **theoretical lower bound of KL-divergence** based on an **analytical quantization noise model** (independent of the Sinkhorn solver, derived from uniform quantization variance $\Delta^2/12$), and measure the static prior's performance against this independent ground truth to avoid circular validation. (See US-3)
- **FR-009**: The system MUST compare the MLP prediction error against a simple closed-form baseline (s = 1/variance) to verify that the learned mapping captures non-trivial, context-dependent relationships beyond the deterministic identity. (See US-2)
- **FR-010**: The system MUST extract attention matrices from a **real-world pre-trained model** (e.g., DistilBERT) on a standard dataset, and evaluate the trained static prior on these real-world maps to validate generalization beyond synthetic distributions. (See US-4)

### Key Entities

- **AttentionTrajectory**: Represents a sequence of 128x128 attention matrices evolving over time, characterized by drift parameters and cumulative error state.
- **ScalingFactor**: A scalar value representing the optimal variance-normalization factor for a specific attention step, derived from the **Sequential** Sinkhorn optimization.
- **SimulationRun**: An instance of the [deferred]-step autoregressive generation, storing the sequence of KL-divergence values and timing metrics.
- **ModelError**: A record of the prediction error (MSE) for a specific attention step when using the static prior versus the ground truth.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction accuracy (MSE) of the static prior is measured against the ground-truth scaling factors generated by the **Sequential** KVarN Sinkhorn optimizer. (See FR-002)
- **SC-002**: The accumulated KL-divergence [deferred] steps is measured against the baseline KVarN method, the **Analytical Noise Floor**, and standard uniform quantization methods. (See FR-004, FR-008)
- **SC-003**: The per-token latency of the static prior method is measured against the original KVarN method to quantify the reduction in optimization overhead. (See FR-005)
- **SC-004**: The statistical significance of the difference in final accumulated error is measured against a p-value threshold of 0.05 using a paired t-test on 30 independent runs. (See FR-006)
- **SC-005**: The sensitivity of the error rate to the variance floor threshold is measured across a range of threshold values to validate robustness. (See FR-007)
- **SC-006**: The improvement of the MLP over the closed-form baseline (s = 1/variance) is measured to confirm the non-triviality of the learned mapping. (See FR-009)
- **SC-007**: The generalization performance of the static prior is measured on **real-world attention maps** extracted from a pre-trained model, comparing MSE against synthetic test sets. (See FR-010)

## Assumptions

- **Assumption about data/environment**: The synthetic dataset generation and the shallow MLP training will fit within the RAM and disk limits of the GitHub Actions free-tier runner without requiring sampling or chunking.
- **Assumption about scope boundaries**: The research is limited to CPU-only execution; no GPU acceleration, CUDA, or 8-bit/4-bit quantization libraries requiring GPU drivers are used.
- **Assumption about target users**: The primary user is a researcher evaluating the feasibility of static priors for KV-cache quantization; the output is a research artifact (spec, code, results) rather than a production API.
- **Assumption about methodological validity**: The relationship between input moments and optimal scaling factors is not deterministic; the study treats the mapping as an empirical learning problem, and the "ground truth" is defined strictly by the KVarN Sinkhorn output.
- **Assumption about threshold justification**: The epsilon floor for variance normalization is set to 1e-6 based on standard numerical stability practices in deep learning, and the sensitivity analysis (FR-007) will verify this choice.
- **Assumption about compute feasibility**: The total compute time for multiple independent simulation runs (each of a sufficient number of steps) will not exceed the time limit per GitHub Actions job.