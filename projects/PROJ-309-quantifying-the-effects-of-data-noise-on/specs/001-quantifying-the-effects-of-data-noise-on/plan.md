# Implementation Plan: Quantifying the Effects of Data Noise on Dynamical Systems Reconstruction

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-quantifying-the-effects-of-data-noise-on/spec.md`

## Summary

This feature implements a computational pipeline to quantify how measurement noise (Gaussian and uniform quantization) degrades phase space reconstruction metrics (Correlation Dimension, Lyapunov Exponents, False Nearest Neighbors) for canonical chaotic systems (Lorenz, Rössler). The approach involves generating synthetic ground-truth trajectories via `scipy.integrate.solve_ivp`, injecting controlled noise at defined Signal-to-Noise Ratios (SNR), computing non-linear time-series metrics using CPU-tractable algorithms (Grassberger-Procaccia, Rosenstein), and analyzing error propagation to identify critical SNR thresholds. The implementation strictly adheres to the runtime and RAM constraints of the free-tier CI environment.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `scipy` (integration, signal processing), `numpy` (numerical operations), `pandas` (data aggregation, statistical analysis, CSV export), `matplotlib` (visualization), `pyyaml` (schema validation), `nolds` (non-linear time series analysis, CPU-optimized).  
**Storage**: Local file system (`data/` for generated trajectories, `results/` for metrics). No external database.  
**Testing**: `pytest` with `pytest-randomly` for seed reproducibility.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Scientific computing library / CLI pipeline.  
**Performance Goals**: Complete full sweep (7 SNR levels × 2 noise types × 2 systems × 50 realizations) within 6 hours on 2 CPU cores.  
**Constraints**: No GPU usage; double-precision arithmetic only; memory footprint <7GB; deterministic execution via pinned random seeds.  
**Scale/Scope**: A substantial number of time steps per system (A scalable number of steps × 7 SNR × 2 noise types × 50 realizations × 1 system).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Principle I (Reproducibility)**: **COMPLIANT**. The plan mandates pinned random seeds in `code/`, deterministic `scipy` integration settings, and explicit version pinning in `requirements.txt`. All artifacts are derived from the same canonical synthetic generation logic.
2.  **Principle II (Verified Accuracy)**: **COMPLIANT**. Ground-truth metrics (Lyapunov exponent, Correlation Dimension) are validated against established literature values for standard Lorenz/Rössler parameters during the clean-data validation phase. The degradation analysis compares noisy estimates against a robust internal baseline (mean of clean realizations).
3.  **Principle III (Data Hygiene)**: **COMPLIANT**. Generated trajectories will be checksummed upon creation. No data modification in place; noisy versions are new files. No PII exists in synthetic data.
4.  **Principle IV (Single Source of Truth)**: **COMPLIANT**. All figures and statistics in the final output will be generated programmatically from the `results/` CSV/JSON artifacts, which trace back to the `code/` execution and `data/` inputs.
5.  **Principle V (Versioning Discipline)**: **COMPLIANT**. The plan includes a step to record content hashes of all generated data and code artifacts in the project state YAML.
6.  **Principle VI (Numerical Stability & Resource Management)**: **COMPLIANT**. The plan explicitly restricts methods to CPU-tractable algorithms (Grassberger-Procaccia, Rosenstein with denoising) and double-precision arithmetic. Memory usage is managed by processing trajectories in batches and avoiding large matrix allocations. The runtime budget is **≤ 6 hours** on 2 CPU cores.
7.  **Principle VII (Benchmark & Synthetic Data Consistency)**: **COMPLIANT**. The plan relies on `scipy.integrate.solve_ivp` for synthetic data generation with standard parameters (σ=10, ρ=28, β=8/3) **or** validated UCI datasets, ensuring a single, immutable source for ground truth.

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-effects-of-data-noise-on/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── trajectory.schema.yaml
    ├── metric_result.schema.yaml
    └── lookup_table.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Constants, seeds, SNR levels
├── generators/
│   ├── __init__.py
│   ├── lorenz.py        # Lorenz attractor generation
│   └── rossler.py       # Rössler attractor generation
├── noise/
│   ├── __init__.py
│   ├── gaussian.py      # Gaussian noise injection
│   └── quantization.py  # Uniform quantization noise
├── metrics/
│   ├── __init__.py
│   ├── correlation_dim.py # Grassberger-Procaccia
│   ├── lyapunov.py      # Rosenstein's algorithm (with denoising)
│   └── fnn.py           # False Nearest Neighbors
├── analysis/
│   ├── __init__.py
│   └── error_analysis.py # Error calculation, statistical aggregation, threshold detection
├── utils/
│   ├── __init__.py
│   ├── io.py            # CSV export (pandas), checksumming
│   └── plotting.py      # Visualization generation
├── main.py              # Orchestration script
└── requirements.txt

tests/
├── __init__.py
├── test_generators.py
├── test_noise.py
├── test_metrics.py
└── test_integration.py

data/
├── raw/                 # Generated clean trajectories
└── processed/           # Noisy trajectories and metrics
```

**Structure Decision**: A modular, function-oriented structure is selected. This separates concerns (generation, noise, metrics, analysis) to facilitate unit testing of each component independently. The `main.py` script orchestrates the pipeline, ensuring the computational order (Generate → Inject → Compute → Analyze) is strictly followed. This structure supports the "Single Source of Truth" principle by keeping all data flow explicit and traceable.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The problem scope is well-bounded by the spec (2 systems, 2 noise types, 3 metrics). The chosen structure is minimal yet sufficient for modularity and testing. | A monolithic script would violate the "Reproducibility" principle by making unit testing of specific noise/metric interactions difficult. |