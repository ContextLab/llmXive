# Implementation Plan: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Low-Capacity Models

**Branch**: `[001-llmxive-staleness-scaling]` | **Date**: 2026-08-21 | **Spec**: `specs/001-llmxive-staleness-scaling/spec.md`
**Input**: Feature specification from `specs/001-llmxive-staleness-scaling/spec.md`

## Summary

This feature implements a CPU-optimized asynchronous Reinforcement Learning (RL) training loop to empirically determine the staleness tolerance of low-capacity language models (Phi 1.4B and Qwen1.5-1.8B) on the GSM8K dataset. The system simulates network latency via a configurable "staleness queue," monitors for divergence based on **intrinsic variance thresholds** (variance > 2 * mean), and performs **Survival Analysis (Log-Rank test)** to compare stability regimes. The implementation strictly adheres to GitHub Actions free-tier constraints (2 CPU, 7GB RAM, <6h runtime) using 8-bit quantization and streaming data access.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (4.40+), `datasets`, `torch` (CPU build), `bitsandbytes` (CPU quantization), `scipy`, `numpy`, `accelerate`, `lifelines` (for survival analysis)  
**Storage**: Local ephemeral storage (`data/` for cached GSM8K shards, `artifacts/` for logs/manifests)  
**Testing**: `pytest` (unit tests for divergence logic, integration tests for full training loops on sampled data)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research CLI / Simulation Engine  
**Performance Goals**: Complete 500 steps for a 1.4B model in <45 mins on CPU; <6.5 GB peak RAM usage.  
**Constraints**: No GPU; strict memory ceiling; no external API calls for data (must use `datasets` library); deterministic seeds.  
**Scale/Scope**: 2 models × 3 regimes (Low, High, Adaptive) × 5 seeds = 30 full runs per experimental block; ~100k total training steps per model.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: **COMPLIANT**. The plan mandates pinned seeds (`FR-004`), deterministic `torch` settings, and the use of the `datasets` library to fetch GSM8K from a canonical source (`openai/gsm8k`) on every run. No manual data intervention is allowed.
- **Principle II (Verified Accuracy)**: **COMPLIANT**. All citations to the parent paper (arXiv:2607.07508) and dataset sources (HuggingFace GSM8K) will be validated against the `Verified datasets` block. No hallucinated URLs.
- **Principle III (Data Hygiene)**: **COMPLIANT**. The plan includes a data loader that downloads GSM8K, checksums the raw parquet files, and stores them in `data/raw/`. Derived manifests (baseline stats) go to `data/processed/`. No in-place modification.
- **Principle IV (Single Source of Truth)**: **COMPLIANT**. The `data/processed/` logs serve as the single source for all analysis. **All figures in the final paper MUST be generated programmatically** via `generate_plots.py` from these logs, ensuring no hand-calculated statistics.
- **Principle V (Versioning Discipline)**: **COMPLIANT**. The `requirements.txt` pins all dependencies. The `state` YAML will be updated with content hashes of the `code/` and `data/` artifacts upon successful runs.
- **Principle VI (Asynchronous Staleness Sensitivity)**: **COMPLIANT**. The core loop implements the `StalenessQueue` with configurable delay. The plan explicitly includes **Low**, **High**, and **Adaptive** staleness regimes as mandatory experimental conditions.
- **Principle VII (Resource-Constrained Execution Validity)**: **COMPLIANT**. The plan explicitly uses 8-bit quantization (`bitsandbytes` CPU) and streaming to fit within 7GB RAM. The runtime limit (<5.5h) is enforced by the step count (500) and batch size constraints.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-staleness-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── llmxive/
│   ├── __init__.py
│   ├── config.py                # Configuration loading (staleness, seeds, models)
│   ├── data_loader.py           # GSM8K streaming loader with checksum verification
│   ├── model_factory.py         # CPU quantization logic (Phi-2, Qwen1.5)
│   ├── staleness_queue.py       # Implementation of the delay buffer
│   ├── trainer.py               # Main RL loop (async simulation)
│   ├── metrics.py               # Intrinsic divergence detection (variance/mean)
│   ├── stats.py                 # Survival Analysis, Levene's test, t-test implementation
│   └── plot_generator.py        # Programmatic figure generation from data/processed/
├── cli/
│   └── run_experiment.py        # Entry point for execution
├── utils/
│   └── logging.py               # Structured logging for JSON manifests
└── main.py                      # Orchestrator for multi-seed runs

tests/
├── contract/
│   └── test_schemas.py          # Validates output against contracts
├── integration/
│   └── test_training_loop.py    # End-to-end run with mocked small steps
└── unit/
    ├── test_staleness_queue.py
    ├── test_divergence_logic.py
    └── test_stats.py

data/
├── raw/                         # Cached GSM8K parquet files (checksummed)
├── processed/                   # Baseline manifests, divergence logs, aggregated results
└── artifacts/                   # Final plots, summary tables

requirements.txt
```

**Structure Decision**: Single project structure (`src/llmxive`) selected. This minimizes import complexity for a research CLI and keeps the training loop, metrics, and stats tightly coupled, which is essential for the deterministic execution required by the reproducibility principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Custom StalenessQueue** | Required to simulate network latency and asynchronous gradient updates without a distributed system. | Using a real distributed framework (e.g., Ray) would exceed the 2-CPU/7GB RAM budget and introduce non-deterministic network overhead that confounds the staleness variable. |
| **8-bit CPU Quantization** | Essential to fit 1.4B/1.8B models in 7GB RAM on CPU. | Using full precision (FP16/FP32) would cause OOM errors immediately on the target hardware, making the experiment infeasible. |
| **Intrinsic Variance Threshold** | Required to define a seed-specific, stable threshold for divergence without circular validation (not relying on synchronous baseline). | Using a global static threshold would ignore model initialization variance and seed-specific instability, leading to false positives/negatives in divergence detection. |
| **Survival Analysis** | Required to handle censored data (runs that diverge early) and avoid survivorship bias. | Using a t-test on final rewards would be invalid for runs that never reached the final step, introducing significant bias. |