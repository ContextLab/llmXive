# Implementation Plan: Cortical Column LLMs

**Branch**: `001-cortical-column-llms` | **Date**: 2026-07-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-cortical-column-llms/spec.md`

## Summary

This project implements a hybrid neural architecture that replaces standard Transformer MLP layers with parameterized "Cortical Column" microcircuits. The goal is to quantify the "cost of biological plausibility" by comparing approximation error (MAE) against a baseline Transformer on synthetic function tasks (Lorenz, Fourier, polynomials). The implementation strictly adheres to CPU-only constraints (limited core count, restricted RAM, and time limit) and validates generalization across distinct dynamical regimes.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU-only wheel), numpy, scipy, pytest, psutil  
**Storage**: Local filesystem (`data/`), in-memory tensors  
**Testing**: `pytest` with `pytest-timeout` and a custom `conftest.py` (using `psutil`) for resource monitoring.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7GB RAM)  
**Project Type**: Research Library / CLI  
**Performance Goals**: Training < 6 hours for largest configuration; MAE < 0.05 for baseline; < 10% degradation for generalization.  
**Constraints**: No GPU/CUDA; no spiking neural networks (rate-based only); parameter parity (±1%) between baseline and microcircuit models; strict excitatory/inhibitory ratio enforcement

The research question remains: How does the balance between excitatory and inhibitory inputs affect network stability? The method involves simulating neural networks with constrained synaptic weights. References: [DOI/arXiv/author-year].  
**Scale/Scope**: baseline variants, ablation variants, scaling variants (2x, 4x columns); synthetic dataset size N < 10,000.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched/generated deterministically. |
| **II. Verified Accuracy** | **PASS** | The 'Reference-Validator Agent' is configured as a CI gate to run before `research.md` is promoted to `research_review`. Citations in `research.md` will be validated against primary sources; no unverified claims in `plan.md`. |
| **III. Data Hygiene** | **PASS** | Synthetic data generation scripts produce checksummed outputs in `data/`; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final report will trace to `data/` rows and `code/` execution logs. |
| **V. Versioning Discipline** | **PASS** | A `scripts/hash_artifacts.sh` script will run on every commit to update `state/` YAML files with SHA256 hashes of `data/` and `code/` artifacts, invalidating stale records as required. |
| **VI. Biological Constraint Fidelity** | **PASS** | `MicrocircuitModule` enforces L2/3, L4, L5, L6 topology and 4:1 E/I ratio by construction; deviations are explicit ablation flags. |
| **VII. Independent Distribution Validation** | **PASS** | Training on Lorenz (chaotic); Testing on Polynomials/Fourier (statistically independent) to prevent overfitting. Claims are framed as "generalization across regimes" rather than strict mathematical universality. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cortical-column-llms/
├── plan.md              # This file (Phase 0)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Required Phase 1 Deliverables
    ├── dataset.schema.yaml
    ├── model.schema.yaml
    └── experiment.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-590-cortical-column-llms-implementing-canoni/code/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline_transformer.py   # Standard Transformer baseline
│   │   ├── microcircuit.py           # FR-001: Parameterized Cortical Column
│   │   └── hybrid_network.py         # Integration of Microcircuit into Transformer
│   ├── data/
│   │   ├── __init__.py
│   │   └── benchmarks.py             # FR-006: Synthetic function generators (Lorenz, Poly)
│   ├── training/
│   │   ├── __init__.py
│   │   ├── trainer.py                # FR-004: CPU-optimized training loop
│   │   └── homeostasis.py            # FR-007: Scaling mechanism
│   └── experiments/
│       ├── __init__.py
│       ├── ablation.py               # FR-003: Ablation variants
│       └── scaling.py                # FR-008: Scaling law analysis
├── tests/
│   ├── unit/
│   │   ├── test_microcircuit.py      # US-002: Connectivity & ratio checks
│   │   └── test_benchmarks.py        # Data generation sanity checks
│   └── integration/
│       └── test_training_pipeline.py # US-001: End-to-end CPU feasibility
├── scripts/
│   ├── hash_artifacts.sh             # For Constitution Principle V
│   ├── run_baseline.sh
│   ├── run_microcircuit.sh
│   └── run_ablation.sh
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure chosen to minimize I/O overhead on the constrained runner. All modules are local to `code/src/` to avoid import path issues.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Hybrid Architecture** | Required to isolate the "cost of biological plausibility" by swapping only MLP layers while keeping attention and parameter count constant. | Pure Transformer (no microcircuit) fails to test the hypothesis; Pure Microcircuit (no baseline) lacks a control for universal approximation. |
| **Homeostatic Scaling** | Required to maintain the 4:1 E/I ratio dynamically (FR-002) and prevent vanishing gradients (Edge Case 1). | Static weight initialization fails to maintain ratio during training; standard weight decay does not enforce biological constraints. |
| **Independent Distribution Test** | Required by SC-006 and Constitution Principle VII to validate "universality" claims. | In-distribution testing (training and testing on Lorenz) risks overfitting and false positive "universal" claims. |
| **Paired Statistical Testing** | Required because ablation variants share the same random seeds and dataset. | Two-sample t-tests assume independence and would yield invalid p-values. |
| **Padding for Parameter Parity** | Required to maintain exact parameter count (±1%) despite 4:1 E/I constraints. | Without padding, the architectural mismatch would confound the "biological cost" measurement. |