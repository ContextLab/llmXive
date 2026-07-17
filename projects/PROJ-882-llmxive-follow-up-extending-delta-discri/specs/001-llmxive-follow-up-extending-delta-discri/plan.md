# Implementation Plan: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

**Branch**: `001-delta-static-approximation` | **Date**: 2026-07-14 | **Spec**: `specs/001-delta-static-approximation/spec.md`
**Input**: Feature specification from `specs/001-delta-static-approximation/spec.md`

## Summary

This project extends the "DelTA" algorithm by investigating whether the discriminative token credit assignment signal (DelTA Coefficients) can be predicted using only **static input features** (n-grams, POS tags, semantic similarity) without access to the model's internal hidden states or gradients. The plan involves: (1) generating ground-truth DelTA Coefficients for a subset of the GSM8K dataset using a small LLM (Phi-mini, B parameters) as an "Oracle"; (2) extracting static features from the prompt text using a distinct embedding model (sentence-transformers/all-MiniLM-L6-v2); (3) training a lightweight 2-layer MLP on CPU to predict the coefficients; and (4) evaluating the rank correlation at the example level against baselines and performing permutation tests. The implementation strictly adheres to CPU-only constraints (no GPU/CUDA) and avoids circularity by ensuring feature extraction uses a model distinct from the Oracle.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers` (for tokenizer/embedding extraction), `datasets` (HuggingFace), `scikit-learn` (MLP, metrics, SHAP), `pandas`, `numpy`, `spacy` (POS tagging), `sentence-transformers` (semantic similarity, CPU-compatible).  
**Storage**: Local filesystem under `data/` (raw GSM8K, generated coefficients, feature vectors); no external database.  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline steps).  
**Target Platform**: GitHub Actions free-tier runner (Linux, multiple CPUs, ~7 GB RAM, no GPU).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: End-to-end pipeline execution < 6 hours; memory footprint < 7 GB RAM.  
**Constraints**: No GPU/CUDA usage; no 8-bit/4-bit quantization requiring CUDA; strict separation between Oracle (DelTA generation using Phi-3-mini) and Predictor (Static features using sentence-transformers) to prevent data leakage.  
**Scale/Scope**: Subset of GSMK (a representative sample of examples); token-level analysis for each prompt, aggregated to example level for evaluation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Details |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds (`seed=42`), explicit dataset versioning (HuggingFace `parquet`), deterministic subset size (N=200), and full re-runnability of `code/` on fresh runners. No adaptive timeouts or non-deterministic fallbacks. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs in `research.md` are restricted to the verified list provided in the spec. No fabricated citations. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw GSM8K data in `data/`; derived files (coefficients, features) are new files with documented derivation paths. |
| **IV. Single Source of Truth** | **PASS** | All metrics (Spearman correlation, p-values) will be computed from `data/` artifacts and traced back to specific code blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; state updates will be automated upon code changes. |
| **VI. Static-Input Independence** | **PASS** | Plan explicitly mandates using sentence-transformers/all-MiniLM-L6-v2 (a model distinct from the Oracle, Phi-3-mini) for semantic similarity feature extraction. This ensures strict independence of static features from the Oracle model's internal states. |
| **VII. Oracle Ground-Truth** | **PASS** | Ground truth is generated via DelTA algorithm on Phi-3-mini on a controlled, deterministic subset (N=200, seed=42), as required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-delta-static-approximation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── delta_oracle.schema.yaml
    ├── static_features.schema.yaml
    └── predictions.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-882-llmxive-follow-up-extending-delta-descri/
├── code/
│   ├── __init__.py
│   ├── config.py                 # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download_gsm8k.py     # FR-001: Download and filter GSM8K
│   │   ├── generate_oracle.py    # FR-002: DelTA Oracle generation (Phi-3-mini)
│   │   └── extract_features.py   # FR-003: Static feature extraction (sentence-transformers)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mlp.py                # FR-004: 2-layer MLP definition
│   │   └── train.py              # FR-004: Training loop (CPU)
│   ├── eval/
│   │   ├── metrics.py            # FR-005/006: Spearman (example-level), Permutation test
│   │   └── interpret.py          # FR-008: Feature importance (SHAP), collinearity analysis
│   └── main.py                   # End-to-end pipeline orchestrator
├── data/
│   ├── raw/                      # Raw GSM8K parquet
│   ├── processed/                # Coefficients, feature matrices
│   └── checksums.json            # Data integrity hashes
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt              # Pinned dependencies
```

### Contract Conformance

- **`code/data/generate_oracle.py`** outputs conform to **`contracts/delta_oracle.schema.yaml`**
- **`code/data/extract_features.py`** outputs conform to **`contracts/static_features.schema.yaml`**
- **`code/eval/metrics.py`** outputs conform to **`contracts/predictions.schema.yaml`**

**Structure Decision**: Selected the "Single project" structure with modular sub-packages (`data`, `models`, `eval`) to align with the linear pipeline nature of the research (Download -> Oracle -> Features -> Train -> Eval). This minimizes overhead and fits the CPU-only CI constraints. The contract mapping ensures the Implementer Agent can validate each module's output.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | The project complexity is driven by the algorithmic requirements (DelTA generation) and strict CPU constraints. The modular structure is the simplest way to maintain separation of concerns (Oracle vs. Predictor) required by Principle VI. Using two distinct models (Phi-3-mini for Oracle, sentence-transformers for features) adds complexity but is necessary to avoid circularity. | A monolithic script would violate Principle VI (separation of concerns) and make debugging the DelTA vs. Feature extraction steps difficult. Reusing the same model for both Oracle and features would create circularity and invalidate the independence hypothesis test. |

## Compute Feasibility

**Hardware**: GitHub Actions Free Tier (limited CPU, ~ GB RAM, limited disk, no GPU).

**Deterministic Subset**: N=200 examples (reduced from 500 in original spec to ensure feasibility).

**Time Budget**:
- Download/Filter: < 10 min
- Oracle Generation (Phi-mini, a representative set of examples): Several hours
- Feature Extraction (sentence-transformers): < 30 min
- Training (2-layer MLP): < 10 min
- Evaluation (Spearman, permutation test, SHAP): < 10 min
- **Total**: ~3–4 hours (well within 6-hour limit)

**Memory Budget**:
- Phi-mini in full precision: ~ GB (peak)
- sentence-transformers/all-MiniLM-L-v: compact model size
- Feature matrices (a representative sample of examples × a moderate sequence length × a moderate number of features): a moderate data volume
- MLP training: moderate memory footprint

The research question remains: What is the optimal architecture for the given task?
The method remains: Multi-layer perceptron training with standard backpropagation.
References remain: [Citation placeholder]
- **Total peak**: Within acceptable limits for standard high-performance computing environments with careful memory management.

**No Fallback Strategy**: The pipeline is deterministic. If runtime or memory constraints are exceeded, the pipeline fails explicitly with an error message, ensuring reproducibility. No partial-data fallbacks or adaptive timeouts are used.
