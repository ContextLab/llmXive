# Implementation Plan: Reproduce & Validate VideoKR

**Branch**: `667-reproduce-validate-videokr` | **Date**: 2026-06-12 | **Spec**: `specs/667-reproduce-validate-videokr/spec.md`
**Input**: Feature specification from `/specs/667-reproduce-validate-videokr/spec.md`
**Governing Document**: `constitution.md` (Principles I, V) - Single Source of Truth (SSoT).

## Summary

This feature implements a CPU-only validation pipeline to reproduce the core data processing and training loop logic of the VideoKR repository. The approach involves initializing a constrained environment (skipping GPU-only dependencies), subsampling the VideoKR dataset to fit within 7 GB RAM, and executing a "dry-run" training step using a small, CPU-compatible Vision-Language Model. 

Crucially, the plan includes a **Pre-flight Memory Budget Check** to prevent OOM failures, a **CPU-Optimized Loading Protocol** (using `device_map='cpu'` and `low_cpu_mem_usage=True`) to ensure model feasibility, and a **Video I/O Stress Test** to validate temporal sampling logic if real data exists. If real data is missing, the plan switches to **Synthetic Mock Mode** (Constitutional Exception to Principle V) to validate the *API contract* and *schema adherence* of the data loader. Success is defined by the generation of valid output artifacts and logs without CUDA-related errors, confirming the codebase's structural integrity and data pipeline logic.

## Technical Context

**Language/Version**: Python 3.10+ (compatible with `llamafactory` and `lmms_eval` defaults)  
**Primary Dependencies**: `llamafactory`, `lmms_eval`, `transformers`, `torch` (CPU-only build), `accelerate`, `pandas`, `pyarrow`  
**Storage**: Local file system (temporary CI workspace) for subsampled JSONL/Parquet and logs  
**Testing**: `pytest` (unit), CI smoke tests (integration), **Contract Tests** (schema validation)  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7 GB RAM, No GPU)  
**Project Type**: Research/Validation Pipeline  
**Performance Goals**: Data prep < 5 min; Dry-run training < 20 min; Total CI job < 6 h  
**Constraints**: 
- **RAM**: < 7 GB peak usage (requires aggressive subsampling, e.g., 100 examples).
- **Memory Budget Gate**: Abort model loading if estimated footprint > 6.5 GB (leaving 0.5 GB for OS/runtime).
- **Compute**: CPU-only; no CUDA, no `bitsandbytes`, no `flash-attn`.  
- **Disk**: < 14 GB; subsampled data must be < 10 MB.  
- **Time**: Single job ≤ 6 hours.  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `constitution.md` (Principles I, V).*

1.  **Principle I (SSoT)**: The plan explicitly documents the "dry-run" nature and the subsampling strategy to ensure the validation is transparent and reproducible on limited hardware. The `constitution.md` is cited as the governing input for all constraints. The plan adheres strictly to the requirements in `constitution.md` regarding resource limits and validation scope.
2.  **Principle V (Real-call testing)**: **Constitutional Exception**: The plan relies on synthetic/mock data if the real VideoKR submodule is missing or too large. This is a *mitigation* for resource constraints, explicitly approved for this "Reproduce & Validate" phase to ensure the *code logic* is tested without violating the "runnable" requirement. The plan explicitly states that Synthetic Mode validates the *API contract* but not the *real-world data distribution*.
3.  **Resource Constraints**: The plan strictly adheres to the 7 GB RAM limit by mandating a subsample size of ≤100 examples and a small model (1.5B-2B parameters), preventing OOM failures. A **Pre-flight Memory Budget Check** (abort if > 6.5 GB) is implemented to ensure safety.
4.  **Error Handling**: The plan includes specific steps to detect and skip GPU-only dependencies (`bitsandbytes`) and to fail gracefully with clear messages if data paths are missing or memory is insufficient.
5.  **Validation First**: The plan prioritizes validating the *logic* (data pipeline, import, loop) over *results* (model accuracy), aligning with the "Reproduce & Validate" scope.
6.  **Artifact Generation**: The plan ensures the generation of structured logs and output schemas as proof of execution, satisfying the requirement for a reproducibility report.

## Project Structure

### Documentation (this feature)

```text
specs/667-reproduce-validate-videokr/
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
├── videokr_validation/
│   ├── __init__.py
│   ├── data_prep.py           # Subsampling, schema validation, synthetic data generation
│   ├── train_dryrun.py        # CPU-compatible training loop wrapper with memory check
│   └── utils.py               # Dependency checks, logging helpers, memory budget calculator
├── tests/
│   ├── contract/
│   │   ├── test_data_schema.py
│   │   └── test_log_schema.py
│   ├── integration/
│   │   └── test_full_pipeline.py
│   └── unit/
│       └── test_imports.py
├── scripts/
│   └── setup_env_cpu.sh       # Dependency installation script
└── artifacts/
    ├── data/                  # Subsampled JSONL/Parquet
    └── logs/                  # train.log, eval.log
```

**Structure Decision**: A modular `src/videokr_validation` package is chosen to encapsulate the validation logic, separating it from the main `VideoKR` submodule (which will be imported as a dependency or vendored). This allows for isolated testing of the CPU compatibility and subsampling logic without modifying the original repository. The `scripts` directory handles environment setup, and `artifacts` stores the transient outputs required for the CI report.

## Plan Steps

1.  **Environment Initialization**: Install dependencies, skip GPU-only libraries, verify imports.
2.  **Submodule Integrity Check**: Verify `VideoKR` submodule is present and contains data. If missing, switch to **Synthetic Mock Mode**.
3.  **Data Preparation**: Generate subsampled data (≤100 examples). If real data is missing, generate synthetic video tensors to test decoding logic.
4.  **Contract Validation**: **Gate Step**: Run `pytest` against the generated data and logs. **Gate**: If contract tests fail, abort pipeline. This explicitly validates the generated artifacts against `contracts/*.schema.yaml` before proceeding.
5.  **Memory Budget Check**: Calculate estimated memory footprint (Model Weights + Overhead). If > 6.5 GB, abort model loading and switch to **Data-Only Validation** or downgrade model.
6.  **Video I/O Stress Test**: Attempt to decode a single real video frame (if available) to verify temporal sampling logic. If no real video, log "Real video I/O not available; API contract validated via synthetic data."
7.  **Dry-Run Training**: Execute training with a small model (if memory permits) or validate data pipeline only.
8.  **Artifact Generation**: Generate logs and validation report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Subsampling Logic** | The full VideoKR dataset (a large-scale collection of examples) exceeds a substantial memory footprint. | Loading the full dataset or even a [deferred] sample would cause OOM on the free-tier runner, failing the "runnable" requirement. |
| **Dependency Patching** | `llamafactory`/`lmms_eval` often default to GPU requirements. | Simply installing the requirements would fail on CPU runners; a patching script is needed to explicitly skip `bitsandbytes` and force CPU backends. |
| **Dry-Run Training** | Full training is impossible within 6 hours on CPU. | A "dry-run" (1 step) is the only way to verify the training loop integration without exceeding time/memory limits. |
| **Memory Budget Gate** | 2B models may OOM on 7 GB RAM. | A static limit is insufficient; a pre-flight check ensures the pipeline adapts (aborts model loading) to prevent a hard crash. |
| **Synthetic Mock Mode** | Real data may be missing or too large. | Relying on real data risks pipeline failure; synthetic data ensures the *code logic* (decoding, batching) is validated regardless of data availability. |