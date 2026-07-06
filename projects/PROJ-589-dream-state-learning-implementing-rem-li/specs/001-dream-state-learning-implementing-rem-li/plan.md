# Implementation Plan: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Branch**: `001-dream-state-learning-rem-consolidation` | **Date**: 2026-07-01 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-dream-state-learning-rem-consolidation/spec.md`

## Summary

This project implements a bio-inspired training protocol for small language models (SLMs) that alternates between "wake" (standard supervised fine-tuning on real data) and "dream" (Denoising Autoencoder reconstruction on masked real data) phases. The primary technical approach involves a custom PyTorch training loop using DistilBERT or TinyLlama (CPU-optimized) to test if this oscillatory schedule improves few-shot generalization on GLUE/SuperGLUE subsets compared to a continuous training baseline. The plan strictly adheres to the GitHub Actions free-tier constraints (2 CPU, 7GB RAM, no GPU).

**Critical Revision**: The "dream" phase is implemented as a Denoising Autoencoder (DAE) on *real* training data (masked input -> original input), not generative replay of hallucinated text. This eliminates the risk of training on garbage generations while preserving the consolidation mechanism (reconstruction of latent structure).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU wheel), `transformers`, `datasets`, `scikit-learn`, `accelerate` (CPU-only config), `pytest`  
**Storage**: In-memory tensors; checkpoints saved to `data/checkpoints/`; logs to `stdout` and `data/logs/`  
**Testing**: `pytest` (unit tests for loop logic, integration tests for full run on a sufficient number of steps)  
**Target Platform**: Linux (GitHub Actions runner: `ubuntu-latest`), CPU-only  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Complete 500-step training + evaluation within 4 hours on 2-core CPU; peak memory < 6.5 GB  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization requiring CUDA; dataset size limited to fit in RAM; strict: wake/dream ratio  
**Scale/Scope**: Small models (≤100M params), small datasets (≤1000 samples for evaluation), Multiple random seeds for statistical power.

> Empirical specifics (exact model weights, final accuracy values) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, explicit `requirements.txt`, and execution of `code/` against `data/` on fresh runners. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` will be restricted to the verified dataset list. A mandatory step for the **Reference-Validator Agent** is included in the workflow to verify all external sources before `research_complete`. |
| **III. Data Hygiene** | **PASS** | Raw data (GLUE subsets) will be downloaded via `datasets` library (canonical source). Upon download, the `datasets` library will compute SHA-256 checksums of the cached parquet files. These checksums will be programmatically extracted and recorded in `state/projects/PROJ-589-dream-state-learning-implementing-rem-li.yaml` under the `artifact_hashes` key. No in-place modification of raw data is permitted; any derived splits will be written to new files with corresponding hash updates. |
| **IV. Single Source of Truth** | **PASS** | All metrics in the final report will be generated programmatically from `data/` rows, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | The **Advancement-Evaluator Agent** computes content hashes for all artifacts in `code/` and `data/` and updates the `updated_at` timestamp in the project state file upon any change. |
| **VI. Oscillatory Training Protocol** | **PASS** | The plan implements an asymmetric wake/dream ratio and a multi-step warm-up. The "dream" phase uses masked reconstruction (DAE) as the specific realization of the "knowledge-distillation" principle, ensuring alignment with the technical design without altering the constitutional principle. |
| **VII. Few-Shot Generalization Validation** | **PASS** | Evaluation is restricted to GLUE/SuperGLUE subsets (≤1000 samples) with Wilcoxon signed-rank tests across multiple seeds. |

## Project Structure

### Documentation (this feature)

```text
specs/001-dream-state-learning-rem-consolidation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── training_config.schema.yaml
    └── evaluation_result.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Hyperparameters, paths, seed management
├── models/
│   ├── __init__.py
│   └── trainer.py       # Core Wake/Dream loop logic (DAE implementation)
├── data/
│   ├── __init__.py
│   ├── loader.py        # GLUE/SuperGLUE loading and preprocessing
│   └── augment.py       # Dream-phase masking logic (DAE)
├── eval/
│   ├── __init__.py
│   └── metrics.py       # Few-shot accuracy, Wilcoxon test computation
├── main.py              # Entry point: runs experiment + baseline
└── utils/
    ├── memory_monitor.py # FR-005: Peak RSS monitoring
    └── logger.py

tests/
├── __init__.py
├── contract/            # Schema validation tests
├── integration/         # Full -step run test
└── unit/
    ├── test_trainer.py
    └── test_memory_monitor.py

data/
├── raw/                 # Downloaded GLUE subsets (cached, checksummed)
├── checkpoints/         # Model weights
└── results/             # JSON logs, accuracy reports
```

**Structure Decision**: Single project structure (`code/`) selected. This is a computational experiment, not a web service or library. The separation of `models`, `data`, and `eval` ensures modularity while keeping the codebase small enough for the constrained CI environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-Loop Architecture (Wake/Dream)** | Required by FR-001 and US-1 to test the bio-inspired hypothesis. | A single continuous training loop (Baseline only) would fail to test the core hypothesis of consolidation. |
| **Memory Monitor (FR-005)** | Required to enforce the 6.5 GB hard limit on GitHub Actions free tier. | Relying on OS OOM killer would result in silent failures and non-reproducible crashes; explicit abort allows checkpoint saving. |
| **Warm-up Protocol (FR-007)** | Required to prevent "garbage" dream phases in early training. | Starting dream phase immediately leads to low-entropy collapse and training instability (Edge Case handling). Increased to a sufficient number of steps to ensure robust prior. |
| **Wilcoxon Test** | Required due to unequal variance in stochastic dream phase. | Paired t-test assumes equal variance (homoscedasticity), which is violated by the stochastic nature of the dream phase. |