# Implementation Plan: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Branch**: `001-symbolic-bes` | **Date**: 2026-07-12 | **Spec**: `specs/001-symbolic-bes/spec.md`
**Input**: Feature specification from `specs/001-symbolic-bes/spec.md`

## Summary

This project extends the "Self-Improving Language Models with Bidirectional Evolutionary Search" (BES) framework by replacing the neural backward step with a **Symbolic Planner**. The core objective is to test whether symbolic constraint decomposition can match or exceed the performance of learned verifiers while drastically reducing computational cost (CPU vs. GPU). The implementation involves curating a dataset of logic/arithmetic puzzles with deterministic Python verifiers, implementing a rule-based symbolic planner for sub-goal generation, and executing a hybrid evolutionary loop where a small CPU-tractable LLM handles forward trajectory recombination guided by symbolic sub-goals. Success is measured by success rates (TOST for equivalence) and computational overhead (t-test) against a neural-verifier baseline.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (statistical tests), `numpy` (data handling), `transformers` (CPU-only inference, default precision), `datasets` (data loading), `pyyaml` (config), `pytest` (testing), `optimum` (CPU-optimized quantization fallback).  
**Storage**: Local filesystem (`data/` for puzzles/verifiers, `code/` for scripts). No external database.  
**Testing**: `pytest` for unit tests of verifiers and symbolic planner; integration tests for the BES loop.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7GB RAM, no GPU).  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: 
- Verifier execution < 100ms per solution.
- Total evolutionary loop runtime ≤ 6 hours for the full experiment.
- Memory usage ≤ 6 GB to allow headroom on 7 GB runner.
**Constraints**: 
- NO GPU usage (no CUDA, no mixed precision).
- NO 8-bit/4-bit quantization via bitsandbytes (requires CUDA). CPU-optimized quantization via `optimum` is allowed as a fallback.
- Symbolic planner must handle all constraint types in the dataset; otherwise, item is excluded (FR-006).
**Scale/Scope**: 
- Dataset: ~500 curated logic/arithmetic puzzles (assumed sufficient for z-test power), with a specific subset for scaling analysis (N=10 to N=500).
- Population size: Tunable (default range) to fit memory.
- Generations: Tunable to fit a feasible runtime.

> Note: Exact dataset size, population size, and generation counts are deferred to `research.md` based on empirical power analysis and resource profiling.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, random seeds in code, and deterministic verification scripts. |
| **II. Verified Accuracy** | PASS | Plan requires all citations in `research.md` to be verified against primary sources. No unverified URLs. |
| **III. Data Hygiene** | PASS | Plan mandates checksums for all data files in `data/` and immutable raw data. |
| **IV. Single Source of Truth** | PASS | All results (success rates, costs) will be derived from `data/` logs and `code/` analysis scripts, not hand-typed. |
| **V. Versioning Discipline** | PASS | Content hashes will be tracked for all artifacts; state file updated on change. |
| **VI. Deterministic Verification Integrity** | PASS | Core requirement: Solution validity determined ONLY by external Python scripts, decoupled from LLM internals. |
| **VII. Computational Efficiency Benchmarking** | PARTIALLY SATISFIED | Plan explicitly compares CPU-seconds (symbolic) vs. *estimated* GPU-hours (baseline). GPU-hours are estimated via a validated conversion factor because the target hardware (GitHub Actions) is CPU-only. This is the best possible approximation given the environment constraints. |

## Project Structure

### Documentation (this feature)

```text
specs/001-symbolic-bes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 0 output (Definitions for Code Gen)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-884-llmxive-follow-up-extending-self-improvi/
├── data/
│   ├── raw/             # Curated puzzle definitions and verifier scripts
│   └── processed/       # Generated logs, evolutionary populations, analysis results
├── code/
│   ├── __init__.py
│   ├── dataset/
│   │   ├── __init__.py
│   │   ├── generator.py      # Puzzle instantiation (including scaling)
│   │   └── verifier.py       # Deterministic Python verification logic
│   ├── symbolic/
│   │   ├── __init__.py
│   │   ├── parser.py         # Constraint parsing to formal language
│   │   └── planner.py        # Sub-goal decomposition logic (with contradiction detection)
│   ├── bes/
│   │   ├── __init__.py
│   │   ├── population.py     # Population management
│   │   ├── forward_step.py   # LLM-based recombination (CPU model)
│   │   └── backward_step.py  # Symbolic planner integration
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py        # Success rate, cost calculation
│   │   └── stats.py          # TOST, t-test implementation
│   └── main.py               # Entry point for experiment execution
├── tests/
│   ├── unit/
│   │   ├── test_verifier.py
│   │   └── test_symbolic_planner.py
│   └── integration/
│       └── test_bes_loop.py
├── requirements.txt
└── README.md
```

**Structure Decision**: 
- **Single Project Structure**: The project is a research experiment, not a distributed web service. A monolithic `code/` directory with modular sub-packages (`dataset`, `symbolic`, `bes`, `analysis`) ensures tight coupling between components while maintaining testability.
- **Data Separation**: `data/raw` holds immutable puzzle definitions; `data/processed` holds generated logs and results to satisfy Data Hygiene (Principle III).
- **Analysis Isolation**: `code/analysis` is separated to ensure statistical tests are reproducible and distinct from the simulation logic.

## Complexity Tracking

No violations identified. The structure aligns with the complexity of a hybrid symbolic-neural research experiment.

## Implementation Phases

### Phase 0: Research & Design
- **Task 0.1**: Finalize Dataset Strategy (Synthetic Curation + Scaling Generation).
- **Task 0.2**: Define Statistical Analysis Plan (TOST for equivalence, t-test for cost).
- **Task 0.3**: Select Baseline Architecture (DistilBERT) and Fallback (TinyBERT/CPU-quantized).
- **Task 0.4**: Validate `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` against design.

### Phase 1: Data & Core Logic
- **Task 1.1**: Implement `code/dataset/generator.py` to create puzzles with systematic complexity scaling (N=10..500).
- **Task 1.2**: Implement `code/dataset/verifier.py` for deterministic validation.
- **Task 1.3**: Implement `code/symbolic/planner.py` with explicit 'CONTRADICTION_DETECTED' and 'PARSE_FAILURE' error codes.
- **Task 1.4**: Implement `code/bes/forward_step.py` (CPU LLM) and `code/bes/backward_step.py` (Symbolic).
- **Task 1.5**: Implement `code/analysis/stats.py` with TOST and t-test.
- **Task 1.6**: **Validate** generated data against `contracts/dataset.schema.yaml`.
- **Task 1.7**: **Validate** output logs against `contracts/output.schema.yaml`.

### Phase 2: Execution & Analysis
- **Task 2.1**: Run Pilot (N=50) to profile runtime and memory.
- **Task 2.2**: Run Full Experiment (Symbolic vs. Neural Baseline) on full dataset.
- **Task 2.3**: Execute Statistical Analysis (TOST, t-test, complexity regression).
- **Task 2.4**: Generate Results and Report.