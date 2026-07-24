# Implementation Plan: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

**Branch**: `001-llmxive-kvarn-static-prior` | **Date**: 2026-07-10 | **Spec**: `specs/001-llmxive-follow-up-extending-kvarn-varian/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-kvarn-varian/spec.md`

## Summary

This project investigates whether the mapping from input attention statistics (mean, variance) to optimal variance-normalization scaling factors (derived via KVarN's iterative Sinkhorn optimization) is learnable via a static prior (a lightweight MLP). The technical approach involves:
1. Generating 10,000 synthetic 128x128 attention matrices with controlled sparsity and outlier magnitudes.
2. Computing ground-truth scaling factors using a CPU-optimized Sinkhorn solver.
3. Training a 2-layer MLP to predict these factors from the first two moments (mean, variance) of the input matrices.
4. Simulating a multi-step autoregressive generation loop (using a dynamic drift model) to measure accumulated KL-divergence and latency trade-offs between the static prior and the iterative KVarN baseline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (for Sinkhorn), `torch` (CPU-only MLP), `pandas`, `scikit-learn` (for t-tests/analysis), `pytest`  
**Storage**: Local file system (`data/` directory for synthetic datasets and simulation logs)  
**Testing**: `pytest` with `pytest-cov` for unit and integration tests  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Research artifact / CLI tool  
**Performance Goals**: < 6 hours total runtime on CI; < 200ms per token latency measurement precision  
**Constraints**: 
- CPU-only execution; no GPU acceleration.
- Strict adherence to synthetic data generation (no external dataset dependencies).
- Numerical stability via epsilon floors.
- **Input Features**: MLP inputs restricted strictly to mean and variance (FR-002).
- **Simulation**: Dynamic attention matrices generated via DriftModel to simulate evolving patterns.
**Scale/Scope**: A large set of synthetic matrices; Multiple independent simulation runs; -step autoregressive horizon per run.

> **Note on Compute Feasibility**: All methods are designed for CPU execution. The Sinkhorn solver is implemented with early stopping and vectorization to fit within RAM limits. The MLP is shallow (2 layers) and trained on CPU. The simulation loop uses efficient NumPy operations. No GPU escape hatch is required as the scope is strictly CPU-bound research.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `requirements.txt` pins versions; data checksums enforced (SHA-256). |
| **II. Verified Accuracy** | **PASS** | KVarN implementation verified against the primary paper (Citation II); all formulas derived in `research.md`. |
| **III. Data Hygiene** | **PASS** | `data/` directory structure with SHA-256 checksums stored in `state/` map; raw data immutable; derivations versioned. |
| **IV. Single Source of Truth** | **PASS** | All results trace to `data/simulation/` CSVs and `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; `state/` updates on change. |
| **VI. Numerical Stability** | **PASS** | Epsilon floor implemented to prevent numerical instability.; sensitivity analysis (FR-007) planned to validate this choice. |
| **VII. Hardware-Aware Latency** | **PASS** | Wall-clock timing isolated to CPU; no GPU variance. |

## Project Phases & Tasks

### Phase 1: Data Generation & Verification
- **Phase 1.1: Dataset Generation & Verification**
  - Generate 10,000 synthetic 128x128 attention matrices with controlled sparsity and outlier magnitudes.
  - **Verification**: Assert `count == 10000` before proceeding.
- **Phase 1.2: Non-Convergence Handling**
  - Compute ground-truth scaling factors using the Sinkhorn solver.
  - **Edge Case**: Flag and exclude non-convergent matrices (US-1 Edge Case).

### Phase 2: Model Training
- **Phase 2.1: MLP Training**
  - Train a 2-layer MLP on CPU using **only** mean and variance as inputs (FR-002).
  - **Constraint**: Higher-order moments (skewness, kurtosis) are explicitly excluded.
- **Phase 2.2: Baseline Comparison**
  - Compare MLP MSE against the closed-form baseline $s = 1/\sigma^2$ (FR-009).

### Phase 3: Simulation
- **Phase 3.1: Autoregressive Loop Execution**
  - Simulate a multi-step autoregressive generation loop.
  - **Dynamic Data**: Use a DriftModel to generate evolving attention matrices at each step (Methodology Update).
  - **Fallback**: Implement fallback to KVarN solver for extreme outliers (Edge Case 2).
  - **Output**: Record per-step KL-divergence history.
- **Phase 3.2: Latency Profiling**
  - Measure wall-clock time per token for **both** static prior and KVarN baseline separately on the same hardware (FR-005).
- **Phase 3.3: Batch Execution**
  - Execute 30 independent simulation runs (n=30) with unique seeds (0-29) for statistical power (FR-006).

### Phase 4: Analysis
- **Phase 4.1: Baseline Comparison**
  - Compare MLP prediction error against the closed-form baseline (FR-009).
- **Phase 4.2: Theoretical Lower Bound**
  - Compute the theoretical lower bound of KL-divergence based on the quantization noise model ($\Delta^2/12$) (FR-008).
- **Phase 4.3: Sensitivity Analysis**
  - Sweep epsilon floor values [1e-9, 1e-6, 1e-3] to validate robustness (FR-007).
- **Phase 4.4: Statistical Significance Testing**
  - Perform a **paired t-test** on final accumulated KL-divergence (scalar) across 30 runs (FR-006).
  - **Pairing Logic**: Run $i$ (Static) paired with Run $i$ (KVarN) using the same seed.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-kvarn-static-prior/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── attention_matrix.schema.yaml
    ├── scaling_factor.schema.yaml
    ├── simulation_run.schema.yaml
    └── model_error.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data_generation/
│   ├── __init__.py
│   ├── synthetic_matrix_generator.py  # Generates 10k matrices
│   └── sinkhorn_solver.py             # Computes ground-truth labels
├── model_training/
│   ├── __init__.py
│   ├── mlp_model.py                   # 2-layer MLP definition
│   └── train_and_eval.py              # Training loop and MSE reporting
├── simulation/
│   ├── __init__.py
│   ├── autoregressive_loop.py         # Extended simulation
│   ├── drift_model.py                 # Dynamic attention generation
│   └── latency_profiler.py            # Wall-clock timing
├── analysis/
│   ├── __init__.py
│   ├── statistical_tests.py           # Paired t-test, sensitivity analysis
│   └── theoretical_bounds.py          # KL-divergence lower bound calculation
├── tests/
│   ├── test_data_generation.py
│   ├── test_model_training.py
│   └── test_simulation.py
├── data/
│   ├── raw/                           # Generated synthetic matrices
│   ├── processed/                     # Training splits, labels
│   └── simulation/                    # Simulation logs, KL-divergence curves
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to align with the research artifact nature. All components are modular but tightly coupled via the `data/` directory.

## Complexity Tracking

> **No violations detected.** The scope is strictly limited to synthetic data generation and CPU-based simulation, adhering to the spec's constraints. No scope expansion (e.g., real-world data, trajectories) is included. The fallback mechanism for extreme outliers is explicitly within scope.