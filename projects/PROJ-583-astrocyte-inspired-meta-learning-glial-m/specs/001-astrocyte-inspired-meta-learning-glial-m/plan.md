# Implementation Plan: Astrocyte-Inspired Meta-Learning: Glial Modulation of Neural Networks

**Branch**: `001-astrocyte-meta-learning` | **Date**: 2026-07-03 | **Spec**: `specs/001-astrocyte-meta-learning/spec.md`
**Input**: Feature specification from `/specs/001-astrocyte-meta-learning/spec.md`

## Summary

This project implements an astrocyte-inspired homeostatic plasticity module to modulate the MAML (Model-Agnostic Meta-Learning) algorithm. The core innovation is a differentiable ODE module (based on Polykretis et al.) that calculates a calcium concentration $Ca_t$ from task history and current activation, deriving a homeostatic factor $h_t = \exp(-\lambda \cdot Ca_t)$. This factor multiplicatively scales the inner-loop learning rate. The system evaluates the stability-plasticity trade-off in a Task-Incremental Learning regime on **Omniglot**, comparing the modulated model against a vanilla MAML baseline using a **Permutation Test** on joint [Stability, Plasticity] vectors across 5 random seeds.

**SCOPE LIMITATION & SPEC GAP**: The source spec (FR-004) mandates execution on both Omniglot and Mini-ImageNet. However, Mini-ImageNet is **NOT feasible** on the GitHub Actions free-tier (2 CPU, 7 GB RAM, 6 h limit) due to memory and runtime constraints. 
- **CI Validation Scope**: Strictly **Omniglot** (grayscale, ≈500 MB for 100 episodes/seed). 
- **Mini-ImageNet Status**: **Deferred** to local/cloud execution. The plan explicitly flags this as a **Spec Gap**: the current CI environment cannot satisfy FR-004's Mini-ImageNet requirement without a spec amendment to exclude it from CI or provision of external resources. The hypothesis validation on CI is therefore strictly Omniglot-based.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: PyTorch (CPU-optimized), `torchvision`, `scipy` (for statistical tests), `numpy`, `pandas`, `scikit-learn` (for metrics), `huggingface/datasets` (optional, for dataset loading).  
**Storage**: Local file system for `data/` (cached datasets) and `results/` (metrics, logs).  
**Testing**: `pytest` (unit tests for ODE module, integration tests for training loop, statistical validation tests).  
**Target Platform**: GitHub Actions Free-tier Runner (Linux, 2 CPU, 7 GB RAM, No GPU).  
**Project Type**: Research Library / CLI  
**Performance Goals**: Complete 5-seed validation run on Omniglot within 6 hours on CPU. Memory footprint < 1 GB.  
**Constraints**: NO GPU/CUDA usage. All ODE solvers must use `torch.autograd` or CPU-safe `scipy`. No external CUDA-dependent libraries.  
**Scale/Scope**: 5-way 1-shot classification tasks on Omniglot. 5 random seeds. 100 episodes per seed (validation subset).

> **Feasibility Note**: The spec mentions `[deferred]` episodes. The plan implements a **validation subset** (100 episodes per seed) sufficient for the statistical pipeline to run within the 6-hour CI limit. Full-scale runs (including Mini-ImageNet) are deferred to local execution.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Action |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins versions. Seeds pinned in config. Data checksums recorded. |
| **II. Verified Accuracy** | PASS | Citations (Polykretis et al., [Year]) will be validated against primary source. |
| **III. Data Hygiene** | PASS | Raw data (Omniglot) downloaded via verified loaders; checksums stored in `state/`. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics logged to CSV/JSON; paper figures generated programmatically from these files. |
| **V. Versioning Discipline** | PASS | Artifact hashes updated in `state/` on code/data changes. |
| **VI. Biologically-Grounded Regularization** | PASS | ODE implementation strictly follows Polykretis Eq 1-3. $h_t$ derived directly from $Ca_t$ without heuristic simplification. Calcium history buffer EXCLUDES tasks N and N to prevent circular validation. |
| **VII. Statistical Rigor** | PASS (FR-005 Override) | **AMENDMENT**: The spec (FR-005) mandates Hotelling's T-squared test; the Constitution requires paired t-tests. Hotelling's T-squared is adopted to account for correlation between Stability and Plasticity metrics, preventing Type I error inflation. However, due to N=5 constraint, the **PRIMARY test is a Permutation Test** (10,000 permutations, non-parametric), which is robust to small sample sizes and does not require covariance matrix inversion. Hotelling's T-squared is retained as a secondary reference. Plasticity is logged at multiple intervals per Constitution Principle VII; the primary metric uses a multi-step value. |

## Project Structure

### Documentation (this feature)

```text
specs/001-astrocyte-meta-learning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── config.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── episode_log.schema.yaml
    ├── metrics.schema.yaml
    └── stat_test.schema.yaml
```

### Source Code (repository root)

```text
src/
├── astrocyte/
│   ├── __init__.py
│   ├── ode_module.py       # Polykretis ODE implementation
│   ├── homeostatic_factor.py # h_t calculation
│   └── maml_wrapper.py     # MAML inner-loop modification
├── data/
│   ├── loaders.py          # Dataset loading (Omniglot)
│   └── task_generator.py   # 5-way 1-shot task creation, deterministic sequence
├── training/
│   ├── trainer.py          # Main training loop (Task-Incremental)
│   ├── metrics.py          # Plasticity/Stability calculation (1, 5, 10 steps)
│   └── ablation.py         # Sensitivity sweep logic
├── analysis/
│   ├── stats.py            # Permutation Test, Hotelling's T-squared (secondary), power analysis
│   └── visualizer.py       # Plot generation
├── cli/
│   └── run_experiment.py   # Entry point
├── config/
│   └── default.yaml        # Hyperparameters, seeds
└── utils/
    ├── logger.py
    └── checkpoint.py

tests/
├── unit/
│   ├── test_ode_module.py
│   └── test_homeostatic_factor.py
├── integration/
│   └── test_training_loop.py
└── contract/
    └── test_output_schema.py

requirements.txt
README.md
```

**Structure Decision**: Single project structure with modular separation of the astrocyte module, training logic, and analysis. This ensures the ODE module can be unit-tested independently of the full training loop, satisfying the reproducibility and verification requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Permutation Test (Primary)** | Required by N=5 constraint. Hotelling's T-squared with df=2 has low power and singular covariance risk. Permutation tests are non-parametric, robust to small N, and do not require matrix inversion. | Hotelling's T-squared alone would fail or be inconclusive with N=5; univariate t-tests would inflate Type I error by ignoring correlation between metrics. |
| **Task-Incremental Regime** | Required by Spec (US-1) to measure "Stability" on N-1. Required by FR-003 to retain task N-1 weights and evaluate on held-out query set. | Standard MAML (task-independent) does not retain task N-1 weights, making the specific stability metric impossible to compute. |
| **Calcium History Buffer (Excludes N-1, N)** | Required to prevent circular validation: h_t must be independent of the Stability metric (N-1) and the current task (N). | If the buffer includes N-1 or N, the homeostatic factor would be tautologically dependent on the outcome it is supposed to predict, making the mechanism a mathematical artifact rather than an emergent property. |
| **Meta-Test Buffer for Stability (3-Task Average)** | Required to address task-instance variance: Stability measured on single-task N-1 is skewed if N-1 is an outlier. Averaging over N-1, N-2, N-3 reduces variance while maintaining Task-Incremental regime. | Single-task Stability would be high-variance and sensitive to task difficulty; averaging over multiple tasks provides more robust measurement. |
| **CPU-Only ODE Solver** | Required by Compute Feasibility constraints (No GPU). | Custom CUDA kernels or GPU-accelerated ODE solvers would fail on the free-tier runner. |

## Statistical Analysis Plan

### Unit of Analysis
- **One [Stability, Plasticity] vector per seed** (n=5), derived by aggregating all 100 episodes per seed into a single mean pair.
- Episodes within a seed are correlated (same initialization, task sequence); only the seed-level vectors are independent observations for the statistical test.
- This ensures n > p (5 > 2) for test validity.

### Primary Test: Permutation Test
- **Test**: Non-parametric permutation test on Euclidean distance between mean [Stability, Plasticity] vectors.
- **Permutations**: 10,000.
- **Null Hypothesis**: No difference in the joint distribution of [Stability, Plasticity] between Baseline and Astrocyte models.
- **Rationale**: Permutation tests are robust to small N, do not require covariance matrix inversion, and do not assume multivariate normality. With N=5, this is more reliable than Hotelling's T-squared.

### Secondary Test: Hotelling's T-squared (Reference)
- **Test**: Hotelling's T-squared statistic (implemented via scipy.stats.f or custom NumPy).
- **Degrees of Freedom**: df = 5 - 2 - 1 = 2.
- **Power**: Approximately 0.60–0.70 for large effects (Cohen's d ≥ 0.8), below the 0.80 threshold.
- **Covariance Singularity**: If singular, apply ridge penalty (λ=1e-4); if still singular, report "undefined".
- **Status**: Secondary reference; not the primary test due to low power with N=5.

### Power Analysis
- **Exploratory Study**: Due to N=5 constraint, this is an exploratory validation, not a powered confirmatory study.
- **Minimum Detectable Effect Size**: Cohen's d ≥ 0.8 (large effect), assumed from the biological hypothesis of homeostatic plasticity.
- **Post-hoc Power Calculation**: After results are obtained, calculate actual power using the observed effect size.
- **Inconclusive Verdict**: If power < 0.80 is confirmed post-hoc, report `verdict: 'inconclusive'`, `reason: 'insufficient_power'`, `confidence_interval: null`, `n_seeds: 5`.

### Ablation & Sensitivity
- **Sweep Parameters**: $\lambda \in \{0.01, 0.05, 0.1\}$.
- **Constant Homeostatic Mode**: Replace dynamic calcium ODE with fixed $h_t = 1.0$ to isolate the effect of dynamic signaling.
- **Reporting**: Summary table showing [Stability, Plasticity] for each parameter value.

## Compute Feasibility Plan

### Hardware Constraints
- **GitHub Actions Free-tier**: 2 CPU cores, 7 GB RAM, ~14 GB disk, ≤6 h per job, NO GPU.

### Dataset & Memory Strategy
- **Omniglot**: Primary dataset. 28×28 grayscale images. Full dataset fits in RAM.
  - **Memory Estimate**: ~500 MB for 100 episodes per seed.
  - **Feasible**: YES, within 6 hours on CPU.
- **Mini-ImageNet**: Secondary dataset. 84×84 RGB images. Full dataset ≈ 6+ GB.
  - **Memory Estimate**: Even a 10-class subset ≈ 2–3 GB.
  - **Feasible**: NO, exceeds CI RAM limit and 6-hour time constraint.
  - **Status**: **DEFERRED** to local/cloud execution. **Spec Gap Note**: FR-004 requires Mini-ImageNet, but CI cannot support it. The plan executes **only** on Omniglot for CI validation. Mini-ImageNet is flagged as a future work item requiring external resources or a spec amendment to remove the CI requirement for this dataset.

### ODE Solver
- **Implementation**: Custom Euler integration in PyTorch (no external `scipy.integrate` dependency for the ODE itself; scipy is used only for statistical tests).
- **Differentiability**: All operations use `torch.autograd` for gradient computation.
- **Clamping**: Calcium concentration $Ca_t$ clamped to [0, 1] to prevent divergence.

### Validation Subset
- **Episodes per Seed**: 100 (sufficient for statistical significance testing with 5 seeds; full-scale runs use [deferred] episodes).
- **Total Runtime**: Estimated 3–4 hours on 2 CPUs for 5 seeds (100 episodes each).
- **Disk Usage**: ~2 GB for logs and results.

## Training Protocol (Task-Incremental)

### Sequence Generation
- **Fixed, Deterministic Sequence**: Tasks are sampled from Omniglot in a fixed order, seeded by the random seed.
- **Preceding Task Definition**: The "immediately preceding task" is always the task directly before the current one in this fixed sequence, ensuring unambiguous Stability measurement.

### Inner Loop (Per Task $T_i$)
1. Sample Support Set ($S$) and Query Set ($Q$) for $T_i$.
2. Compute meta-gradient $\nabla_\theta \mathcal{L}_{S}$.
3. **Calcium History Buffer** (excludes tasks N-1 and N): Retrieve activation signals from tasks N-2, N-3, and earlier.
4. Calculate $Ca_t$ using the ODE module (incorporating $S$ activation and historical buffer).
5. Compute $h_t = \exp(-\lambda \cdot Ca_t)$.
6. Update: $\theta' = \theta - h_t \cdot \alpha_{inner} \cdot \nabla_\theta \mathcal{L}_{S}$.

### Metrics Calculation
- **Plasticity**: Accuracy on $Q$ of $T_i$ at 1, 5, and 10 inner-loop steps. Primary metric: 5-step value. All three logged per Constitution Principle VII.
- **Stability**: Mean accuracy on query sets of tasks $T_{i-1}$, $T_{i-2}$, $T_{i-3}$ (Meta-Test Buffer, held-out from calcium history) after the update for $T_i$. This 3-task buffer reduces task-instance variance while maintaining Task-Incremental regime.
- **Independence**: Meta-Test Buffer is separate from calcium history buffer to prevent circular validation.

### Iteration
- Repeat for a sufficient number of episodes per seed.

## Output Formats

### Results File (`results/metrics.csv`)
- `seed`: Random seed.
- `model_type`: "astrocyte" or "baseline".
- `lambda_scale`: Homeostatic scale parameter (for ablation).
- `mean_plasticity`: Mean accuracy on current tasks (5-step plasticity).
- `mean_stability`: Mean accuracy on Meta-Test Buffer (3-task average stability).
- `std_plasticity`: Standard deviation.
- `std_stability`: Standard deviation.
- `total_episodes`: Number of episodes run.

### Statistical Test Result (`results/stat_test.json`)
- `test_name`: "Permutation Test" (primary) or "Hotelling's T-squared" (secondary).
- `test_statistic`: Float (Euclidean distance or T² value).
- `p_value`: Float.
- `verdict`: "significant", "not_significant", "inconclusive", or "undefined".
- `reason`: If inconclusive, e.g., "insufficient_power".
- `confidence_interval`: [lower, upper] or null.
- `n_seeds`: 5.
- `effect_size`: Estimated Cohen's d or Euclidean distance.
- `baseline_mean`: [Stability, Plasticity] for baseline.
- `astrocyte_mean`: [Stability, Plasticity] for astrocyte.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **ODE Divergence** | Clamp $Ca_t$ to $[0, 1]$. Log warning. |
| **Covariance Singularity** | Apply ridge penalty ($\lambda=1e-4$) in Hotelling's test. If still singular, report "undefined". |
| **Insufficient Power** | Report "inconclusive" with `reason: 'insufficient_power'`, `confidence_interval: null`. Study is exploratory; full-scale validation requires N ≥ 20. |
| **Mini-ImageNet Infeasibility** | **Spec Gap**: FR-004 requires Mini-ImageNet, but CI cannot support it. **Mitigation**: Execute **only** on Omniglot for CI. Flag Mini-ImageNet as "Deferred to Local/Cloud" in all reports. Do not claim CI validation on Mini-ImageNet. |
| **Calcium History Circular Dependency** | Calcium buffer explicitly excludes N-1 and N. Meta-Test Buffer separate from calcium history. |
| **Task-Instance Variance in Stability** | Stability measured as mean over 3-task Meta-Test Buffer (N-1, N-2, N-3) instead of single-task N-1. |

## Requirements Traceability

| Spec Requirement | Plan Section | Implementation Task |
|---|---|---|
| **FR-001**: Calcium ODE from Polykretis et al. | Technical Context, Training Protocol | `src/astrocyte/ode_module.py` |
| **FR-002**: Integrate $h_t$ into MAML inner-loop | Training Protocol | `src/astrocyte/maml_wrapper.py` |
| **FR-003**: Log Plasticity (1, 5, 10 steps) & Stability (N-1 buffer) | Training Protocol, Metrics Calculation | `src/training/metrics.py` |
| **FR-004**: Execute on Omniglot (Mini-ImageNet deferred) | Compute Feasibility Plan, Dataset Strategy | `src/data/loaders.py`, `src/cli/run_experiment.py` |
| **FR-005**: Hotelling's T-squared (Permutation Test primary) | Statistical Analysis Plan | `src/analysis/stats.py` |
| **FR-006**: Sensitivity analysis sweep | Ablation & Sensitivity | `src/training/ablation.py` |
| **FR-007**: Ablation with constant $h_t$ | Ablation & Sensitivity | `src/training/ablation.py` |
| **FR-008**: Output inconclusive with structured JSON | Output Formats | `src/analysis/stats.py` |