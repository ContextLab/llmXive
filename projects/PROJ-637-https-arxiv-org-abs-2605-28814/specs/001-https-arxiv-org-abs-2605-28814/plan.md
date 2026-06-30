# Implementation Plan: Reproduce & Validate Bidirectional Evolutionary Search (BES)

**Branch**: `637-reproduce-validate-bes` | **Date**: 2026-06-01 | **Spec**: `specs/637-reproduce-validate-bes/spec.md`
**Input**: Feature specification from `specs/637-reproduce-validate-bes/spec.md`

## Summary

This project reproduces and validates the "Bidirectional Evolutionary Search" (BES) algorithm described in the target paper, specifically focusing on the `circle_packing` benchmark task. The primary requirement is to execute the BES inference pipeline in a CPU-only CI environment (no GPU, ≤7GB RAM) to verify functional correctness, solution validity, and the presence of bidirectional search dynamics (forward expansion + backward decomposition). The technical approach involves vendoring the external BES repository, configuring it for CPU execution, running the `circle_packing` task with strict timeout and retry logic, and validating outputs against the paper's metrics and internal geometric constraints.

## Technical Context

**Language/Version**: Python 3.11 (required for modern `datasets` and `transformers` CPU wheels)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `pytest`, `llama-cpp-python` (for CPU-optimized LLM inference if local), `pyyaml`  
**Storage**: Local file system (`inference/results/`, `external/BES/`)  
**Testing**: `pytest` (contract tests for schema validation, integration tests for pipeline execution)  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 vCPU, ~7 GB RAM, No GPU)  
**Project Type**: Computational research pipeline / CLI tool  
**Performance Goals**: Execution of `circle_packing` task within 30 minutes; Memory footprint < 6 GB; Graceful timeout handling.  
**Constraints**: No GPU usage; No CUDA libraries; No 8-bit/4-bit quantization requiring CUDA; Strict adherence to spec-defined metrics (no invented constraints).  
**Scale/Scope**: Single benchmark task (`circle_packing`); 3 candidate solutions per run; 5+ backward decomposition events required for validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle 1: Run the Computation** (Wolfram): The plan prioritizes executing the actual BES code over theoretical analysis. The "smoke test" (US-1) ensures the computation runs end-to-end on the target hardware.
**Principle 2: Operational Test for Improvement** (Turing): The plan defines "improvement" strictly via the `evaluate.py` script's return value and geometric constraints, avoiding vague claims of "self-improvement" without a metric.
**Principle 3: Bidirectional Verification**: The plan explicitly requires logging and counting "backward decomposition" events (US-3, SC-005) to prove the search is not merely greedy.
**Principle 4: Resource Fidelity**: The plan strictly adheres to the 7GB RAM / CPU-only constraints, selecting CPU-tractable libraries and sampling strategies if necessary.

## Project Structure

### Documentation (this feature)

```text
specs/637-reproduce-validate-bes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── BES/                 # Vendored repository (git submodule)

inference/
├── results/             # Output directory for solutions
│   └── circle_packing/
├── scripts/
│   ├── run_evo.py       # Entry point for BES execution
│   └── evaluate.py      # Validation script
└── config/
    └── local_openai_config.py # LLM provider configuration

tests/
├── contract/
│   └── test_schema.py   # Validates output against contracts
├── integration/
│   └── test_bes_pipeline.py # End-to-end execution test
└── unit/
    └── test_evaluator.py # Logic tests for evaluate.py
```

**Structure Decision**: The structure isolates the vendored `BES` code in `external/` to prevent contamination of the main project, while placing the orchestration logic (`run_evo.py`, `evaluate.py`) in `inference/` to align with the spec's directory requirements. `contracts/` is dedicated to schema validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Bidirectional Logging | Required to verify the core novelty (US-3). | Standard logging is insufficient; explicit event markers are needed to count decomposition depth. |
| CPU-Only Constraint | Mandatory for CI feasibility (Assumptions). | GPU-based methods would fail the "runnable on free CPU-only CI" requirement. |
| Retry Logic with Backoff | Required for LLM provider instability (Edge Cases). | Simple crash-on-error would cause flaky CI results. |
