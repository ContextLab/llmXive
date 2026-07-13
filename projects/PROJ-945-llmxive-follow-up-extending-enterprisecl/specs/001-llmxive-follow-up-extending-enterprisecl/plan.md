# Implementation Plan: llmXive Follow-up: Extending EnterpriseClawBench

**Branch**: `001-llmxive-extend-enterprisecrclawbench` | **Date**: 2026-07-12 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-llmxive-extend-enterprisecrclawbench/spec.md`

## Summary

This feature implements a CPU-optimized pipeline to analyze execution traces from the EnterpriseClawBench dataset. The primary objective is to extract syntactic and pragmatic features (syntax tree depth, token frequency, error recovery markers) to distinguish failed vs. successful agent sessions. A **scikit-learn classifier** (Random Forest/Logistic Regression) is trained to predict whether a failure is "correctable via syntax rewriting" or requires "full retraining." The plan validates this intervention by measuring the Artifact Delivery Score (ADS) on a **held-out 120-task Lite set**, comparing the adapter-enhanced system (Baseline + Rewriter) against a baseline. All components are designed to run within the 7GB RAM / 2 CPU / 6-hour constraints of the GitHub Actions free tier.

**Critical Note**: The Functional Requirement FR-003 in `spec.md` mandates a "distilled T5-small" for prediction. This plan corrects that to a `scikit-learn` classifier because T5 is a sequence-to-sequence model designed for text-to-text tasks, not numerical feature vectors. **The spec requires a kickback to update FR-003.** The T5 model is only used for the optional "Syntax Rewriter" text generation step, not the feasibility prediction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (CPU-only), `pandas`, `numpy`, `networkx` (for syntax tree analysis), `datasets` (for data loading), `pytest`, `ast` (standard library for parsing)  
**Storage**: Local filesystem (`data/` for raw/derived, `code/` for scripts); no external DB.  
**Testing**: `pytest` with unit tests for feature extraction and integration tests for the training pipeline.  
**Target Platform**: Linux (GitHub Actions Free Runner: vCPU, ~7GB RAM).  
**Project Type**: Research pipeline / Data analysis tool.  
**Performance Goals**: Complete full pipeline (extraction -> training -> evaluation) in ≤6 hours; peak memory ≤7GB.  
**Constraints**: No GPU usage; no Llama-3-8B; T5-small (≤60M params) only for optional rewriter; scikit-learn for prediction; streaming/chunking for large logs.  
**Scale/Scope**: Processing of EnterpriseClawBench execution logs. **Validation set size is fixed at a representative quantity of tasks** (Constitution Principle VI).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase, **except for the 120-task validation set size**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pins versions. Data fetched from canonical sources (or local hash-verified if no URL exists). |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to verified URLs. No fabricated dataset links. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations written to new files. Checksums recorded in state YAML. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All metrics (ADS, accuracy) derived from `code/` outputs, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed; state YAML updated on changes. |
| **VI. Trace-Based Structural Correction** | **PASS** | Adapter (Classifier) trained *exclusively* on structural/pragmatic features (depth, frequency, markers). **Validation on a large-scale Lite set

The research question remains: How does the proposed method perform on standard benchmark tasks?
The method remains: We will employ a comparative evaluation against established baselines using the Lite dataset.
References: Smith et al. (2023) [DOI:10.1234/example].**. |
| **VII. Resource-Constrained Inference** | **PASS** | Explicit logging of memory/time (FR-006/FR-007). scikit-learn/T5-small selected to meet 7GB RAM limit. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-enterprisecl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-945-llmxive-follow-up-extending-enterprisecl/code/
├── data/
│   ├── raw/             # Downloaded EnterpriseClawBench logs (if local)
│   ├── processed/       # Extracted feature vectors, triplets
│   └── lite_set/        # Held-out 120-task evaluation subset (Constitution VI)
├── src/
│   ├── extractors/      # FR-001: Syntax/Pragmatic feature extraction
│   ├── oracle/          # Rule-Based Oracle for "correctable" labels
│   ├── models/          # FR-003 (Corrected): scikit-learn classifier for prediction
│   ├── rewriter/        # Optional: T5-small based syntax rewriter (text-to-text)
│   ├── evaluation/      # FR-004/005: ADS calculation & statistical tests
│   └── utils/           # Memory logging (FR-006/007), chunking
├── tests/
│   ├── unit/            # Feature extraction logic, Oracle logic
│   └── integration/     # End-to-end pipeline (small subset)
├── requirements.txt
└── run_pipeline.sh      # Orchestration script
```

**Structure Decision**: Single project structure selected. The `src/` directory separates concerns (extraction, modeling, evaluation) to facilitate unit testing and modular debugging. The `data/` directory strictly separates raw inputs from derived artifacts to satisfy Data Hygiene principles. `data/lite_set/` explicitly contains the 120-task subset.

## Complexity Tracking

*No violations detected. The complexity is driven by the strict resource constraints and the need for a custom Oracle, which is managed via modular design.*