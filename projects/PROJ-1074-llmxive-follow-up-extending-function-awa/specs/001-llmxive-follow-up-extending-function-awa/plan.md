# Implementation Plan: Function-Aware FIM for Non-Code Domains

**Branch**: `001-fim-non-code-transfer` | **Date**: 2026-07-21 | **Spec**: `spec.md`
**Input**: Feature specification for transferring Function-Aware Fill-in-the-Middle (FIM) inductive bias from code to logical/math reasoning traces.

## Summary

This feature implements a mid-training experiment to determine if the "function-call" inductive bias learned via Function-Aware FIM transfers to non-code domains. The approach involves:
1.  **Synthetic Data Construction**: Converting the GSM8K math dataset into pseudo-code blocks (`def step_N(): return fact`) with explicit dependency graphs. Crucially, this includes a **Graph Complexity Injection** phase to ensure non-linear dependencies (branching/merging) exist, preventing the task from collapsing into simple sequence prediction.
2.  **CPU-Tractable Mid-Training**: Fine-tuning a ≤150M parameter model (TinyLlama-110M) on this synthetic data using a custom FIM masking strategy that targets *missing steps* (signature + body) to force dependency resolution, strictly on CPU. A **Convergence Check** ensures the model learns the signal.
3.  **Statistical Evaluation**: Comparing the FIM-trained model against a Natural Language (NL) Control (which preserves the *same* graph structure but uses plain text) and a Baseline on the independent LogiQA benchmark using bootstrap confidence intervals and permutation tests.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `datasets`, `scikit-learn`, `torch` (CPU build), `networkx` (dependency graphs), `pytest`, `scipy`.  
**Storage**: Local ephemeral storage on GitHub Actions runner (temp files for datasets, models, artifacts).  
**Testing**: `pytest` with unit tests for data conversion, integration tests for training loop, and **contract tests** for `dataset.schema.yaml`, `masking_map.schema.yaml`, and `evaluation_results.schema.yaml`.  
**Target Platform**: GitHub Actions free-tier runner (Linux, multiple vCPU, ~7 GB RAM).  
**Project Type**: Research experiment / Data pipeline.  
**Performance Goals**: Mid-training ≤6 hours; Evaluation ≤2 hours; Memory peak ≤7 GB.  
**Constraints**: No GPU/CUDA; No data leakage between GSM8K (train) and LogiQA (test); Strict topological sort validation for synthetic data; Non-linear graph requirement.  
**Scale/Scope**: Single epoch (or until convergence) on [deferred] examples (subset of GSM8K); Evaluation on full LogiQA test set.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | All seeds pinned; `requirements.txt` pins versions; datasets fetched via canonical HuggingFace IDs. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` will be validated against primary sources (GSM8K, LogiQA papers) before acceptance. |
| **III. Data Hygiene** | PASS | Raw GSM8K/LogiQA preserved; synthetic derivative has unique checksum; no in-place modification. |
| **IV. Single Source of Truth** | PASS | Results traced to `data/` artifacts and `code/` scripts; no hand-typed stats in paper. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; state updated on change. |
| **VI. Structural Generalization** | PASS | Plan enforces pseudo-code formatting (`def step_N`), non-linear graph injection, and **explicit statistical significance validation against both NL Control and Baseline** as a mandatory pass condition. |
| **VII. Synthetic Data Leakage** | PASS | Pipeline includes overlap check for **raw GSM8K vs LogiQA** AND **derived synthetic dataset vs LogiQA**, plus format-based leakage verification to ensure no test-set info is encoded in the pseudo-code structure. |

## Project Structure

### Documentation (this feature)

```text
specs/001-fim-non-code-transfer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── masking_map.schema.yaml
│   └── evaluation_results.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_gsm8k.py
│   ├── download_logiqa.py
│   ├── convert_to_pseudo_code.py
│   ├── inject_graph_complexity.py  # New: ensures non-linear dependencies
│   └── validate_dependencies.py
├── training/
│   ├── train_fim.py
│   ├── train_nl_control.py
│   ├── masking_utils.py
│   └── convergence_checker.py      # New: monitors loss/fit
├── evaluation/
│   ├── eval_logiqa.py
│   └── statistical_analysis.py     # New: bootstrap/permutation tests
├── utils/
│   └── common.py
├── tests/
│   ├── test_data_conversion.py
│   ├── test_masking.py
│   ├── test_stats.py
│   └── test_contracts.py           # Validates all 3 schema files
├── requirements.txt
└── main.py

data/
├── raw/
│   ├── gsm8k/
│   └── logiqa/
├── processed/
│   ├── synthetic_logical_dataset.jsonl
│   └── masking_map.json
└── artifacts/
    └── results/
```

**Structure Decision**: Single project structure selected. The workflow is linear: Data Download → Conversion → Complexity Injection → Training → Evaluation. Separation into `data/`, `training/`, and `evaluation/` directories ensures modularity and aligns with the reproducibility principle (Principle I).

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  **CPU-First Constraint**: Limits model size and batch size, forcing a focused experimental design.
2.  **Synthetic Data Pipeline**: The conversion logic is isolated in `convert_to_pseudo_code.py` and `inject_graph_complexity.py` with strict validation (topological sort), preventing downstream training failures.
3.  **Statistical Rigor**: Using standard `scikit-learn`/`scipy` for bootstrap/permutation tests avoids complex custom inference code.
4.  **Convergence Guard**: The `convergence_checker.py` ensures the model actually learns before evaluation, preventing null results due to underfitting.