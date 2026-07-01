# Implementation Plan: Mega-ASR Reproduction & Validation

**Branch**: `615-mega-asr-reproduction` | **Date**: 2026-05-23 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/615-mega-asr-reproduction/spec.md`

## Summary

This project reproduces and validates the "Mega-ASR" paper claims by executing the vendored `Voices-in-the-Wild-Bench` inference pipeline on CPU-only hardware. The primary technical approach involves streaming audio data to avoid RAM overflow, running the pre-trained model on the free-tier GitHub Actions runner (CPU, 7GB RAM), and calculating Word Error Rate (WER) against ground truth labels. The plan explicitly addresses the reviewer's concern regarding allometric scaling by collecting **metric stability data points** (WER variance across sample sizes) rather than attempting to validate a scaling law, which requires training data. The plan strictly adheres to the constraint that no new model training occurs—only inference and evaluation.

## Technical Context

**Language/Version**: Python 3.11 (derived from `requirements.txt` in `external/Voices-in-the-Wild-Bench`)  
**Primary Dependencies**: `torch` (CPU-only), `librosa` (audio processing), `jiwer` (WER calculation), `pandas` (data handling), `scipy` (bootstrap)  
**Storage**: Local file system (temporary artifacts), JSONL/Parquet datasets (streamed)  
**Testing**: `pytest` (unit/contract tests), shell scripts (integration smoke tests)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM, no GPU)  
**Project Type**: Computational Research / Reproduction Pipeline  
**Performance Goals**: Complete inference on a representative sample within 6 hours; peak RAM < 7GB  
**Constraints**: No GPU/CUDA usage; no model training; strict memory limits; strict dataset variable fit (must contain audio path + text).  
**Scale/Scope**: Reproduction of VOiCES and NOIZEUS benchmarks on a sampled subset due to memory constraints.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `constitution.md` (Principles I-V).*

1.  **Reproducibility (Principle I)**: The plan mandates the use of the exact vendored code (`external/Voices-in-the-Wild-Bench`) and pre-trained checkpoints to ensure the reproduction is faithful to the original work.
2.  **Scientific Rigor (Principle II)**: The plan explicitly addresses the "allometric scaling" concern by designing the evaluation to report WER stability across sample sizes (N=100, 500, 1000), acknowledging that this measures metric stability, not scaling laws.
3.  **Resource Feasibility (Principle III)**: The plan enforces CPU-only execution and batch processing/streaming to guarantee the job completes within the designated CI window and RAM limit.
4.  **Data Integrity (Principle IV)**: The plan requires validation of input JSONL/Parquet structures and audio path accessibility before processing to prevent silent failures.

## Project Structure

### Documentation (this feature)

```text
specs/615-mega-asr-reproduction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks agent)
```

### Source Code (repository root)

```text
external/
└── Voices-in-the-Wild-Bench/  # Vendored submodule (read-only execution)

src/
├── mega_asr/
│   ├── __init__.py
│   ├── inference.py           # Wrapper for run_inference.py
│   ├── evaluation.py          # Wrapper for evaluate_predictions.py
│   └── data_loader.py         # Streaming/batching logic
├── cli/
│   └── main.py                # Entry point for CI scripts

tests/
├── contract/
│   ├── test_inference_schema.py
│   └── test_evaluation_schema.py
├── integration/
│   └── test_smoke_sample.py   # US-1 smoke test
└── unit/
    └── test_wer_calculation.py

data/
└── examples.jsonl             # Sample dataset for P1/P2

results/
└── [generated artifacts]
```

**Structure Decision**: The project adopts a **Wrapper/Integration** structure. The core logic remains in the vendored `Voices-in-the-Wild-Bench` to ensure fidelity to the paper's codebase. The `src/mega_asr` directory contains thin wrappers and data loaders specifically designed to adapt the vendored code to the CI constraints (CPU, streaming, batching). This separates the "reproduction logic" from the "research logic," allowing the implementation to focus on environment adaptation without modifying the original algorithm.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Streaming/Batching Logic | The `Voices-in-the-WildM` dataset exceeds 7GB RAM. | Loading the full dataset would cause an immediate OOM crash on the free-tier runner, preventing any validation. |
| CPU-Only Model Loading | The runner lacks GPU. | Using GPU-accelerated libraries (e.g., `load_in_8bit`, `device_map="cuda"`) would fail or hang, violating the CI constraints. |
| WER Metric Validation | The paper's WER calculation might differ from standard implementations. | **Validation Method**: Unit tests will compare `jiwer` output against a known ground truth set to ensure alignment with the paper's reported values. |

## User Story Alignment

- **US-1 (Smoke Test)**: Covered by Phase 1 (Data Loading & Inference on Sample).
- **US-2 (WER Calculation)**: Covered by Phase 2 (Evaluation & Metric Calculation).
- **US-3 (Benchmark Reproduction)**: Covered by Phase 3 (Scaled Evaluation on R4-B-F subset).
  - *Note*: The acceptance criteria for US-3 now explicitly compare the WER of the **sampled subset** against the paper's reported value for that specific subset (or note the limitation if comparing to a full-dataset claim).
