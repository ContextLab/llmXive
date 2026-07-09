# Implementation Plan: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Branch**: `001-consciousness-bootstrapping-self-aware-ai` | **Date**: 2026-07-03 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-consciousness-bootstrapping-self-aware-ai/spec.md`

## Summary

This project implements a computational investigation into whether recursive self-attention mechanisms can bootstrap meta-cognitive behaviors (self-consistency, error detection, uncertainty calibration) in a small language model. The technical approach involves modifying a small transformer architecture (e.g., Qwen1.5-0.5B) to include a temporal recursive self-attention module that attends to confidence distributions from previous generation steps. We will train both a recursive variant and a standard baseline on a sampled subset of the Pile dataset (arXiv domain) using a joint loss function, where the confidence signal is derived from pre-computed teacher model labels (external truth). The models will be evaluated on MMLU, GSM8K, and Self-Consistency benchmarks, followed by rigorous statistical analysis (paired t-tests, sensitivity analysis, multiple-comparison correction) across five random seeds to determine if the recursive architecture yields statistically significant improvements in the correlation between consistency and accuracy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only, pinned to 2.1.0+), `transformers` (4.40+), `datasets` (2.18+), `scikit-learn`, `numpy`, `pandas`, `pytest`, `jsonschema`  
**Storage**: Local filesystem (`data/` for datasets, `artifacts/` for checkpoints and evaluation results).  
**Testing**: `pytest` for unit tests; `GitHub Actions` for end-to-end integration and reproducibility.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU cores, ~7 GB RAM, ~14 GB disk, no GPU).  
**Project Type**: Computational research / Machine Learning experiment  
**Performance Goals**: Training must complete within 2 hours per seed; total CI job time ≤ 4 hours for 5 seeds (aligned with Constitution Principle VII). Memory usage must remain < 7 GB.  
**Constraints**: No GPU/CUDA usage; no 8-bit/4-bit quantization requiring CUDA; no large-LLM inference; strict adherence to 7 GB RAM limit.  
**Scale/Scope**: Training on a representative subset of tokens from the Pile (arXiv subset); evaluation on standard benchmark test sets (GSM8K, MMLU).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned seeds, canonical dataset sources (HuggingFace), and deterministic evaluation scripts.
- **II. Verified Accuracy**: All dataset URLs cited in `research.md` are drawn exclusively from the verified list. No hallucinated URLs.
- **III. Data Hygiene**: Raw data will be downloaded to `data/raw/` with checksums recorded in `data/manifest.json`. Derived data (e.g., training splits, teacher labels) will be stored in `data/processed/` with versioning.
- **IV. Single Source of Truth**: All metrics in the final report will be generated directly from `data/` artifacts by `code/` scripts.
- **V. Versioning Discipline**: Artifacts (checkpoints, JSON results) will be named with content hashes. A `sha256sum` script in CI will update `state/...yaml` with the hashes.
- **VI. Statistical Rigor**: Plan explicitly includes multiple random seeds., paired t-tests, Cohen's d, and Bonferroni correction as required by the constitution and spec.
- **VII. Resource-Constrained Architectural Fidelity**: Plan strictly limits training to a small subset of tokens, uses a small model (<300M params), and enforces a max recursion depth of a fixed, configurable limit to fit within 7 GB RAM.

## Project Structure

### Documentation (this feature)

```text
specs/001-consciousness-bootstrapping-self-aware-ai/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   ├── processed/       # Preprocessed training splits & teacher labels
│   └── manifest.json    # SHA256 checksums for all data files
├── code/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_llama.py        # Standard small transformer wrapper
│   │   └── recursive_llama.py   # Modified with temporal recursive attention
│   ├── training/
│   │   ├── __init__.py
│   │   ├── train.py             # Main training script
│   │   └── loss_functions.py    # Joint loss implementation
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── run_benchmarks.py    # MMLU, GSM8K, Self-Consistency runner (with contract validation)
│   │   └── metrics.py           # Brier, ECE, ROC-AUC, Consistency calc
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── stats.py             # T-tests, sensitivity, plots
│   └── utils/
│       ├── __init__.py
│       ├── data_loader.py       # Dataset fetching logic (updates manifest)
│       └── config.py            # Hyperparameter config
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── artifacts/
│   ├── checkpoints/
│   └── results/
└── requirements.txt
```

**Structure Decision**: A monolithic Python package structure within `code/` is selected to minimize overhead and simplify dependency management on the constrained CI runner. The separation into `models`, `training`, `evaluation`, and `analysis` ensures modularity while keeping the execution flow linear: Train -> Evaluate -> Analyze.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Recursive Self-Attention Module | Required by FR-001 to implement the core hypothesis of temporal recursion. | A standard attention mechanism cannot model the "confidence distribution of the previous generation step" as required. |
| Joint Loss Function | Required by FR-002 to train the model on self-consistency proxies. | Standard cross-entropy alone does not optimize for confidence calibration or error detection. |
| 5 Random Seeds | Required by Constitution Principle VI and FR-005 for statistical rigor. | A single seed or fewer seeds would not provide sufficient power for paired t-tests or control for stochastic variance. |
| Teacher-Student Distillation | Required to break the tautological loop of self-consistency proxies. | Internal consistency proxies create circular validation and cannot measure true error detection. |
| Small Model (<300M params) | Required to fit the 7GB RAM and 2-hour CPU budget. | Larger models are computationally infeasible on the target hardware. |
| Pre-computed Teacher Labels | Required to avoid triple inference cost during training. | On-the-fly generation for labels is too slow and memory-intensive. |