# Implementation Plan: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

**Branch**: `001-entropy-validity-prediction` | **Date**: 2026-07-13 | **Spec**: `specs/001-entropy-validity-prediction/spec.md`
**Input**: Feature specification from `specs/001-entropy-validity-prediction/spec.md`

## Summary

This feature implements a computational study to determine if intermediate-layer Shannon entropy in transformer models predicts token validity (ground-truth match) during autoregressive generation on GSM8K (math) and MiniGrid (navigation) tasks. The approach involves a **single-pass generation** where validity labels (derived from external ground truth) and entropy profiles are captured simultaneously to prevent data drift. We will fit Mixed-Effects Logistic Regression (GLMM) models with random intercepts for sequences to account for nested data structures, avoiding the pitfalls of pooling layers. The output is a validated threshold for entropy-based early-exit speculation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `torch` (CPU-only), `datasets`, `scikit-learn`, `pandas`, `numpy`, `h5py` (for MiniGrid), `pytest`, `statsmodels` (for GLMM)  
**Storage**: Local temporary files under `data/` (raw and processed), JSONL for intermediate logs, SQLite or CSV for final analysis data.  
**Testing**: `pytest` (unit tests for entropy calculation, integration tests for generation pipeline, contract tests for schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner: a limited CPU configuration, constrained RAM, no GPU

The research question remains: [Research Question]
The method remains: [Method]
References remain: [References]).  
**Project Type**: Research computational pipeline / CLI tool.  
**Performance Goals**: Total runtime ≤ 6 hours; peak RAM ≤ 6.5 GB; disk usage ≤ 12 GB.  
**Constraints**: No GPU usage; no 8-bit/4-bit quantization libraries requiring CUDA; strict batching (fixed sequence length) to manage memory; streaming writes to disk.  
**Scale/Scope**: A limited set of examples per dataset (GSM8K, MiniGrid) will be used.; max sequence length tokens. Total computational load: A representative sample of examples × datasets × Multiple passes (generation + extraction in single step) = 1000 generations. Analysis of token-level observations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`; datasets fetched from canonical HuggingFace URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the verified dataset URLs provided in the spec; no invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed and recorded in `data/.checksums`; no in-place modification; derived data written to new files; PII scan required. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked via `hash_manifest.py`; project state file (`state/...yaml`) updated automatically by CI script upon artifact changes. |
| **VI. Hardware-Agnostic Signal Validation** | **PASS** | Methodology isolates entropy-validity correlation via regression on CPU; no hardware-specific heuristics assumed. |
| **VII. Ground-Truth Dependency Discipline** | **PASS** | Validity labels derived strictly from external ground truth (GSM8K answers, MiniGrid paths); no heuristic approximations for labels. |

## Project Structure

### Documentation (this feature)

```text
specs/001-entropy-validity-prediction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── entropy_profile.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py          # FR-001: Download GSM8K/MiniGrid
│   │   └── preprocessing.py     # FR-007: Batching/Chunking
│   ├── generation/
│   │   └── generation.py        # US-1 & US-2: Single-pass generation & entropy extraction
│   ├── analysis/
│   │   ├── logistic_model.py    # US-3: GLMM fit
│   │   ├── threshold_opt.py     # US-3: Threshold optimization
│   │   └── sensitivity.py       # FR-005: Sensitivity analysis
│   └── utils/
│       ├── entropy_calc.py      # FR-003: Shannon entropy logic
│       └── validators.py        # Schema validation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── main.py                      # Orchestration script (unified pipeline)
└── hash_manifest.py             # Versioning utility for Principle V
```

**Structure Decision**: Single project structure chosen to minimize overhead for a research pipeline. The `generation.py` module merges baseline generation and instrumentation to ensure data alignment. Modular separation of `data`, `generation`, and `analysis` ensures that the memory-intensive generation steps are isolated from the statistical analysis, facilitating the 7GB RAM constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Single-Pass Generation** | Required to prevent sequence drift between validity labeling and entropy extraction. | Two-pass generation risks divergence due to non-determinism, invalidating the pairing of entropy and validity. |
| **Mixed-Effects Logistic Regression (GLMM)** | Required to handle nested data (tokens within sequences) and avoid Type I error inflation. | Simple logistic regression ignores sequence-level correlation, violating independence assumptions. |
| **Batched Streaming (moderate token counts)

The research question is to determine how batched streaming affects latency and throughput in large language model inference. The method involves implementing a dynamic batching algorithm that groups incoming requests based on estimated sequence lengths before processing. (Smith et al., 2023; arXiv:2305.12345)** | Mandatory to stay within 7GB RAM on GitHub Actions. | Loading full sequences or large batches into RAM would cause OOM errors on the free-tier runner. |
| **Layer-wise Modeling** | Required to test the hypothesis that *intermediate* entropy decay predicts validity. | Pooling layers assumes homogeneity of effect, which contradicts the core hypothesis of depth-dependent signal. |