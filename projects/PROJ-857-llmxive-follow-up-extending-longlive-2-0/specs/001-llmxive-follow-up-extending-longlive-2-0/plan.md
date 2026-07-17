# Implementation Plan: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

**Branch**: `001-llmxive-precision-threshold` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-precision-threshold/spec.md`
**Input**: Feature specification from `specs/001-llmxive-precision-threshold/spec.md`

## Summary

This project implements a CPU-only simulation loop to model the effects of NVFP4 (and lower) precision on video generation models. The approach uses **true integer quantization emulation** (`torch.quantize_per_tensor`) on standard 32-bit floats to simulate the *reduced dynamic range, underflow, and integer-accumulation behavior* of low-bit arithmetic (2-bit, 3-bit, 4-bit, 5-bit, and 6-bit). The system evaluates generated video clips using a frozen CLIP-ViT model to measure temporal coherence, aggregating results across the mandated A set of bit-widths spanning the range from 2 to 6 and seeds to identify the non-linear degradation threshold where narrative consistency collapses. The simulation explicitly emulates hardware-level quantization effects, acknowledging it as a proxy for hardware behavior rather than an exact replica.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `torch` (CPU-only mode), `transformers`, `datasets`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `bayesian-optimization`, `psutil`
**Storage**: Local filesystem (temporary), HuggingFace Datasets cache
**Testing**: `pytest` (unit tests for quantization logic, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier: limited vCPU, moderate RAM, 14GB disk)
**Project Type**: Computational research / Simulation pipeline
**Performance Goals**: Complete 15 runs (5 bit-widths × 3 seeds) within 6 hours; memory usage ≤ 7GB per run.
**Constraints**: No GPU/CUDA instructions; strict memory limits; no access to gated datasets; simulation must validate against theoretical noise distribution.
**Scale/Scope**: A a range of bit-widths as mandated by Constitution Principle VII and FR-005, multiple seeds, and Short-duration video clips

The research question, the method, and the references remain unchanged as per the planning document requirements. from Kinetics-400 subset (or UCF101 fallback).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned seeds in `code/`, explicit dataset fetching via `datasets.load_dataset` (no local caching assumptions), and a single `requirements.txt`. All artifacts are derived from code execution.
- **II. Verified Accuracy**: Citations to the "LongLive-2.0" paper and Kinetics-400 dataset will be validated against primary sources. The plan relies on verified HuggingFace dataset URLs where available.
- **III. Data Hygiene**: The plan uses the HuggingFace API to stream Kinetics-400 subsets. No raw data modification is allowed; downsampling creates new derived files. Checksums will be recorded for derived subsets.
- **IV. Single Source of Truth**: All consistency scores and memory estimates are calculated programmatically and stored in CSVs. The paper will reference these CSV rows, not hand-typed numbers.
- **V. Versioning Discipline**: The plan includes a `state/` update step for artifact hashes. The `requirements.txt` ensures dependency versioning.
- **VI. Simulation Fidelity and Validation Independence**: The plan strictly separates the "student" model (simulation) from the "evaluator" (frozen CLIP-ViT). Memory claims are derived from the formula `(Params × Bits / 8) + 1.2GB`, not runtime profiling, as per the requirement. A lightweight runtime profiling step is added *only* to satisfy SC-005 for comparison purposes.
- **VII. Precision-Threshold Linearity Analysis**: The experimental design explicitly includes **5 bit-widths (2, 3, 4, 5, 6)** (per Constitution Principle VII and FR-005) with Multiple seeds each. Statistical analysis (paired t-tests between adjacent levels, Bayesian Model Comparison) is mandated to detect the threshold. The plan acknowledges the low sample size (data points) and frames the threshold as a "probabilistic degradation point" rather than a statistically rigorous "knee".

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-precision-threshold/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/
├── __init__.py
├── requirements.txt
├── config.py            # Configuration for seeds, bit-widths, paths
├── simulation/
│   ├── __init__.py
│   ├── quantization_emulator.py  # Core FR-001 logic (torch.quantize_per_tensor)
│   ├── student_model.py        # Simplified diffusion model wrapper
│   └── training_loop.py        # CPU-only training loop
├── evaluation/
│   ├── __init__.py
│   ├── clip_evaluator.py       # FR-003 frozen model logic
│   └── metrics.py              # Consistency score calculation
├── analysis/
│   ├── __init__.py
│   ├── aggregation.py          # FR-005, FR-008: stats & regression
│   └── visualization.py        # Plotting precision-consistency curve
├── data/
│   ├── __init__.py
│   └── loader.py               # FR-002: Kinetics-400 streaming
└── tests/
    ├── test_quantization_emulator.py
    ├── test_evaluator.py
    └── test_memory_footprint.py
```

**Structure Decision**: Single project structure under `code/` with modular sub-packages for simulation, evaluation, and analysis. This keeps the pipeline cohesive for the CI runner while separating concerns for testing and maintenance.

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  **CPU-Only Constraint**: By emulating precision via `torch.quantize_per_tensor` rather than actual low-bit hardware, we avoid complex CUDA kernels and stay within the 7GB RAM limit.
2.  **Data Streaming**: Using `datasets.load_dataset(..., streaming=True)` avoids loading the full Kinetics-400 dataset into memory, addressing the 14GB disk constraint.
3.  **Simplified Model**: The "student" model is a simplified diffusion architecture sufficient for the simulation, avoiding the computational cost of training a full-scale video model.
4.  **Statistical Robustness**: Bayesian Model Comparison is used to handle the low sample size for non-linear threshold detection.
5.  **Synthetic Ground Truth**: The validation protocol (FR-007) uses programmatically generated labels (frame swaps/cuts) rather than external human annotations, ensuring feasibility.
6.  **Bit-width Scope**: The plan now covers 5 bit-widths (2, 3, 4, 5, 6) as required by the spec, necessitating a more aggressive clip sampling strategy to fit within the 6-hour window.
