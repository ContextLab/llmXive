# Implementation Plan: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

**Branch**: `001-llmxive-static-distillation` | **Date**: 2026-09-19 | **Spec**: `specs/001-llmxive-static-distillation/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-static-distillation/spec.md`

## Summary

This project implements a static distillation of the dynamic Hierarchical Sparse (HiLS) attention mechanism. The primary requirement is to extract "canonical relevance profiles" from the dynamic HiLS model running on a derived PG-19 validation set, cluster these profiles into a static index using CPU-optimized K-Means (with PCA reduction), and evaluate the resulting "Static-HiLS" model against the dynamic baseline on a held-out test set. The technical approach involves three phases: (1) Dynamic Baseline Extraction to generate ground-truth relevance matrices, (2) Static Index Construction via clustering with dimensionality reduction, and (3) Comparative Evaluation measuring log-perplexity, long-context QA accuracy, and latency on a CPU-only runtime.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `transformers`, `datasets` (HuggingFace), `scikit-learn` (K-Means, PCA), `pandas`, `numpy`, `torch` (CPU-only), `pytest`  
**Storage**: Local `data/` directory for extracted profiles and static indexes; HuggingFace cache for model weights.  
**Testing**: `pytest` for unit tests; `pytest` integration tests for end-to-end pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7GB RAM, ~14GB disk).  
**Project Type**: Research/CLI tool for model evaluation.  
**Performance Goals**: Inference latency reduction factor (target %); static index lookup < 50ms on 2 cores.  
**Constraints**: Must run on CPU-only environment; no GPU usage for training or inference (except optional offload if specified, but plan assumes CPU-first); memory usage < 7GB RAM during clustering.  
**Scale/Scope**: PG-19 (derived splits); $K$ tuned on validation, evaluated on test.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`. Datasets fetched via `datasets.load_dataset` from verified HF URLs. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` restricted to verified dataset URLs. No invented URLs. |
| **III. Data Hygiene** | **Pass** | Raw data (profiles) checksummed. Derivations (static index) written to new files. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | Evaluation metrics derived from `data/` artifacts, not hand-typed. |
| **V. Versioning Discipline** | **Pass** | SHA-256 hashes recorded in `state/projects/PROJ-1018...yaml` and `data/` metadata files for every artifact. |
| **VI. Distillation Fidelity** | **Pass** | Strict separation: Validation set (clustering/tuning) $\neq$ Test set (evaluation). |
| **VII. Hardware-Aware Latency** | **Pass** | Latency measured on -core CPU with large token context, 10 runs, 2 warm-ups. |

## Test Coverage Matrix

| Test File | User Story | Functional Requirements | Description |
| :--- | :--- | :--- | :--- |
| `tests/test_extraction.py` | US-1 | FR-001 | Verifies extraction of non-empty relevance matrices and correct chunk dimensions. |
| `tests/test_clustering.py` | US-2 | FR-002 | Verifies K-Means convergence, PCA dimensionality, and mapping integrity. |
| `tests/test_evaluation.py` | US-3 | FR-003, FR-004, FR-005, FR-006, FR-007, FR-008 | Verifies log-perplexity calculation, Wilcoxon test execution, and latency reporting. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-static-distillation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/
├── src/
│   ├── __init__.py
│   ├── extraction.py        # Dynamic Baseline Extraction (FR-001)
│   ├── clustering.py        # Static Index Construction (FR-002)
│   ├── inference.py         # Static-HiLS Inference Pipeline (FR-003)
│   └── evaluation.py        # Comparative Evaluation & Stats (FR-004, FR-005, FR-006, FR-007, FR-008)
├── tests/
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_clustering.py
│   └── test_evaluation.py
├── data/
│   ├── raw/                 # Downloaded PG-19 (streamed)
│   ├── interim/             # Relevance profiles (JSON)
│   └── processed/           # Static Index (YAML/JSON)
├── requirements.txt
└── run_pipeline.sh
```

**Structure Decision**: Single project structure selected to maintain tight coupling between extraction, clustering, and evaluation phases, ensuring data integrity and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate Validation/Test Splits** | Required by Constitution Principle VI (Distillation Fidelity). | Using the same split for clustering and evaluation would cause data leakage, invalidating the performance comparison. |
| **CPU-Only K-Means + PCA** | Required by Compute Feasibility (GitHub Actions free tier). | GPU-based clustering is unnecessary overhead; PCA is required to mitigate curse of dimensionality in high-dimensional attention vectors. |
| **Log-Perplexity + Wilcoxon Test** | Required by Statistical Rigor (non-normal distribution). | Parametric t-test on raw perplexity violates normality assumptions; Wilcoxon on log-perplexity is robust. |
| **K-Tuning on Validation** | Required by Methodology (avoid multiple testing on test set). | Tuning K on test set would invalidate the final significance test; validation set is used for hyperparameter selection. |
| **Long-Context QA Benchmark** | Required by Scientific Soundness (metric sensitivity). | Generic QA is insensitive to long-context failure modes; Needle-in-Haystack is required. |