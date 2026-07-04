# Implementation Plan: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Branch**: `001-evaluating-the-effectiveness-of-llms-for` | **Date**: 2026-07-04 | **Spec**: `specs/001-evaluating-the-effectiveness-of-llms-for/spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-effectiveness-of-llms-for/spec.md`

## Summary

This project evaluates the complementarity of rule-based (Pylint) and semantic (LLM) code smell detection. The technical approach involves: (1) sampling Python functions from `codeparrot/github-code`, (2) computing structural metrics (LOC, Cyclomatic Complexity) via `radon`, (3) generating static smell labels via Pylint (normalized to canonical smell names), (4) generating semantic embeddings and LLM-based smell labels via a CPU-quantized CodeLlama-7B model (batch size 10, with GC), and (5) performing statistical analysis (McNemar's test per smell category, two binary logistic regression models) to compare detection modes. The implementation strictly adheres to CPU-only constraints (≤7 GB RAM, 2 cores) and reproducible research principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pandas`, `radon`, `pylint`, `sentence-transformers`, `llama-cpp-python`, `scikit-learn`, `statsmodels`, `numpy`, `gc` (standard)  
**Storage**: Local filesystem (`data/`, `results/`), HuggingFace Hub (dataset caching)  
**Testing**: `pytest` (unit), contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions Free Tier)  
**Project Type**: Research Data Pipeline & Analysis  
**Performance Goals**: Complete 800-function analysis in ≤6 hours; Peak RAM ≤7 GB  
**Constraints**: No GPU; no CUDA; no 8-bit/4-bit quantization requiring CUDA-specific backends (use CPU-compatible `llama-cpp-python`); dataset sampling to fit memory; batch size reduced to a lower value for LLM inference.  
**Scale/Scope**: A set of sampled functions; detection categories; statistical report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Reference in Plan |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned seeds, `requirements.txt`, and deterministic dataset sampling from `codeparrot/github-code`. |
| **II. Verified Accuracy** | PASS | Plan uses the canonical HuggingFace path `codeparrot/github-code` and records checksums for all derived artifacts. |
| **III. Data Hygiene** | PASS | Plan mandates checksums for raw data and immutable derivations in `data/`. |
| **IV. Single Source of Truth** | PASS | Plan defines strict mapping from `data/` rows to `results/` statistics. |
| **V. Versioning Discipline** | PASS | Plan requires content hashes for artifacts and timestamp updates. |
| **VI. Resource-Constrained Execution** | PASS | Plan explicitly restricts LLM inference to CPU, batch size ≤10, and RAM monitoring with GC. |
| **VII. Dual-Mode Detection Validation** | PASS | Plan mandates McNemar's test (per smell category) and two binary logistic regression models for all three detection sets. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-effectiveness-of-llms-for/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data_pipeline.py       # FR-001, FR-002, FR-003: Sampling, Radon, Pylint, Normalization
│   ├── semantic_analysis.py   # FR-004, FR-005: Embeddings, LLM Inference (Batch 10)
│   ├── statistical_analysis.py# FR-006, FR-007, FR-009, FR-010: McNemar, VIF, Logistic
│   └── main.py                # Orchestrator
├── data/
│   ├── raw/                   # Downloaded parquet (immutable)
│   ├── processed/             # static_baseline.csv, embeddings.json
│   └── checksums.txt          # SHA256 hashes
├── results/
│   ├── statistical_significance.json
│   ├── logistic_regression.json
│   └── sensitivity_report.md
├── tests/
│   ├── unit/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with clear separation of data processing, analysis, and orchestration. `code/` contains the executable pipeline; `data/` holds immutable artifacts; `results/` holds derived statistics. This aligns with Constitution Principle III (Data Hygiene) and IV (Single Source of Truth).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Detection Modes** | Required by Spec (FR-003, FR-004) to answer the research question. | A single-mode analysis cannot measure complementarity or perform McNemar's test. |
| **Statistical Rigor (VIF/McNemar)** | Required by Spec (FR-006, FR-007, FR-010) to address multicollinearity and paired significance. | Simple correlation ignores paired nature of data and predictor collinearity risks. |
| **CPU-Only LLM** | Required by Spec (FR-004) and Constitution Principle VI. | GPU-based inference is infeasible on free-tier CI; CPU quantization is the only viable path. |
| **Batch Size Reduction** | Required to fit 7 GB RAM (Constitution Principle VI). | Batch size 50 risks OOM; batch size 10 with GC ensures safety. |
| **Smell Normalization** | Required to align Pylint codes with LLM categories (Methodology). | Without normalization, overlap analysis is impossible. |