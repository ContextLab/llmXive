# Implementation Plan: Reproduce & Validate MemLens Benchmark

**Branch**: `578-reproduce-memlens-benchmark` | **Date**: 2026-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/578-reproduce-memlens-benchmark/spec.md`

## Summary

This feature implements a CPU-only reproduction and validation pipeline for the "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models" paper. The technical approach involves vendoring the MemLens codebase, patching it for CPU execution (removing CUDA dependencies), implementing an image-ablation mode to test visual evidence dependency, and creating a robust evaluation runner that handles API rate limits and memory constraints on free-tier CI. The plan ensures every functional requirement (FR-001 to FR-006) is mapped to a specific implementation phase.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU wheel), `transformers`, `datasets`, `accelerate` (CPU mode), `pytest`, `pyyaml`, `bitsandbytes` (for 4-bit quantization on CPU if available, otherwise native CPU inference)  
**Storage**: Local filesystem for dataset caching and JSON result artifacts  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: CLI / Benchmarking Tool  
**Performance Goals**: Complete evaluation run on sample data within 60 minutes; handle large context windows via chunking if necessary  
**Constraints**: No GPU/CUDA; moderate RAM requirements; limited runtime; no new un-spec'd constraints  
**Scale/Scope**: Supports K, 64K, 128K, 256K context windows; memory ability categories  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

**Note**: No formal `constitution.md` was supplied for this project. The plan aligns with general scientific principles of reproducibility, validation rigor, resource awareness, and data integrity, as these are the de facto standards for the project's domain.

1.  **Reproducibility**: The plan mandates a CPU-only execution path (FR-001) to ensure results are reproducible on standard CI without specialized hardware, aligning with the general principle of accessible science.
2.  **Validation Rigor**: The plan explicitly includes the image-ablation experiment (FR-002) to validate the paper's core hypothesis, satisfying the general demand for hypothesis-driven testing.
3.  **Resource Awareness**: The plan incorporates memory monitoring and graceful OOM handling (FR-006), adhering to the general principle of robust system design under constraints.
4.  **Data Integrity**: The plan requires categorization of results by memory ability (FR-004), ensuring data is structured for valid statistical analysis as per general guidelines.

## Project Structure

### Documentation (this feature)

```text
specs/578-reproduce-memlens-benchmark/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── evaluation_run.schema.yaml
│   ├── result_metric.schema.yaml
│   └── question.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── memlens_runner.py    # Main entry point, CLI args handling
├── ablation.py          # Image-ablation logic
├── context_manager.py   # Token counting and windowing
├── api_client.py        # Retry logic for external APIs
├── memory_monitor.py    # OOM detection and logging
└── utils.py             # Logging, path handling

tests/
├── contract/
│   └── test_schemas.py  # Validates JSON output against YAML schemas
├── integration/
│   └── test_eval_flow.py
└── unit/
    └── test_ablation.py
```

**Structure Decision**: A modular Python CLI structure is selected to separate concerns (evaluation, ablation, API handling) and facilitate unit testing. This aligns with the spec's requirement for distinct experimental modes (US-2, US-3) and robust error handling (Edge Cases).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within the existing MemLens codebase with targeted patches. | N/A |

## Plan Completeness & Mapping

- **FR-001 (CPU Only)**: Addressed in Phase 1 (Environment Setup) by installing CPU-only torch and configuring `accelerate` for CPU.
- **FR-002 (Image Ablation)**: Addressed in Phase 2 (Ablation Logic) where `ablation.py` replaces image inputs with null tokens.
- **FR-003 (Context Windows)**: Addressed in Phase 2 (Context Management) via `context_manager.py` supporting 32K-256K slicing.
- **FR-004 (Ability Categories)**: Addressed in Phase 3 (Aggregation) where results are grouped by the 5 defined abilities.
- **FR-005 (Retry Mechanism)**: Addressed in Phase 2 (API Client) with exponential backoff logic.
- **FR-006 (OOM Handling)**: Addressed in Phase 2 (Memory Monitor) with peak logging and graceful termination.
- **SC-001 to SC-005**: Each success criterion is validated by:
    - **Schema Validation**: `contracts/*.yaml` ensure structural integrity of `results.json` and `questions.jsonl`.
    - **Logic Checks**: Contract tests in `tests/contract/test_schemas.py` verify specific values (e.g., SC-002's <2% accuracy in ablation, SC-003's degradation trend) against the aggregated metrics.

## Contract Tests & Success Criteria Mapping

| Success Criterion | Schema Validation | Logic/Aggregate Validation |
| :--- | :--- | :--- |
| **SC-001** (Reproducibility) | `results.json` is valid JSON with `run_id`, `status="completed"` | `run_id` is unique, `status` is not "oom" or "rate_limited" |
| **SC-002** (Visual Dependency) | `results.json` has `ablation_accuracy` field | `ablation_accuracy` < 0.02 for image-dependent subset |
| **SC-003** (Scaling Trends) | `results.json` has `ability_breakdown` by context length | Accuracy decreases as `context_length` increases (32K > 256K) |
| **SC-004** (Robustness) | `results.json` has `error_code` if status != "completed" | No OOM crashes; graceful termination with distinct error code |
| **SC-005** (Data Validity) | `questions.jsonl` is valid per `question.schema.yaml` | All questions categorized into 5 memory ability types |
