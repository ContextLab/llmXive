# Implementation Plan: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

**Branch**: `001-logical-dependency-icl` | **Date**: 2026-07-11 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-logical-dependency-icl/spec.md`

## Summary

This project implements a comparative study on In-Context Learning (ICL) strategies. It extends the "Many-Shot CoT-ICL" baseline by introducing a "Logical Ascending" ordering strategy. This strategy orders demonstration examples based on a "Logical Difficulty Score," derived from parsing Chain-of-Thought (CoT) traces into Directed Acyclic Graphs (DAGs) and calculating maximum path depth. The plan covers: (1) a rule-based DAG parser validated against a **human-annotated gold standard**, (2) generation of three prompt ordering strategies (Logical Ascending, Logical Random, **SBERT-based Semantic Curvature**), (3) CPU-only inference using `llama.cpp` on reasoning and non-reasoning models, and (4) a **Linear Mixed-Effects Model (LMM)** to test for interaction effects between model type and ordering strategy. All steps are constrained to run on a free-tier GitHub Actions runner (CPU, ~7GB RAM, 6h limit).

**Critical Deviation Note**: The original spec (FR-001) required correlation with "external GeoQA ratings." As the GeoQA dataset is unavailable in the verified sources, this plan implements a **Generalized Validation** protocol: validating the DAG depth metric against human-rated logical complexity on the *actual* dataset used (SFT). This preserves scientific rigor while acknowledging the domain shift.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (DAG logic), `llama-cpp-python` (inference), `pandas`, `statsmodels` (LMM), `sentence-transformers` (SBERT), `pyyaml`, `huggingface_hub`.  
**Storage**: Local filesystem (`data/` for raw/processed data, `artifacts/` for results). No external database.  
**Testing**: `pytest` (unit tests for parser, integration tests for pipeline).  
**Target Platform**: Linux (x86_64) GitHub Actions Runner.  
**Project Type**: Computational Research Pipeline.  
**Performance Goals**: Complete full inference and analysis within 6 hours; DAG parsing < 15 mins for 1000 traces.  
**Constraints**: No GPU/CUDA; RAM < 7GB per process; disk < 14GB; no heavy model training (inference only).  
**Scale/Scope**: A substantial set of CoT traces for DAG construction; -shot prompts; 10 seeds; 2 models; strategies.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins all deps; seeds pinned in code; `data/` checksummed. |
| **II. Verified Accuracy** | **PASS** | **Reference-Validator Agent** has confirmed `aaabiao/DAG_sft` URL is reachable and format-verified before proceeding. |
| **III. Data Hygiene** | **PASS** | Raw data preserved; derivations to new files; PII scan included in CI. |
| **IV. Single Source of Truth** | **PASS** | All stats trace to `data/results.csv`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | **Versioning & State Update Procedure** (see below) ensures `state/projects/...yaml` is updated with artifact hashes. |
| **VI. Structural Dependency Parsing Integrity** | **PASS** | "Logical Ascending" strictly uses `networkx` DAG max-path-depth; no embedding proxies. |
| **VII. Model-Architecture Alignment** | **PASS** | Explicit stratification of Reasoning vs. Non-Reasoning models; LMM interaction term required. |

### Versioning & State Update Procedure
To satisfy Constitution Principle V:
1. After each phase (Parser, Prompt Gen, Inference, Analysis), a script `code/src/update_state.py` will:
   - Compute SHA-256 hashes of all new artifacts in `data/` and `artifacts/`.
   - Update the `artifact_hashes` map in `state/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co.yaml`.
   - Update the `updated_at` timestamp.
2. This script is triggered automatically by the CI pipeline after each stage.

## Project Structure

### Documentation (this feature)

```text
specs/001-logical-dependency-icl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/
├── data/
│   ├── raw/             # Downloaded datasets
│   ├── processed/       # Parsed DAGs, prompt files, gold standard
│   │   └── gold_standard_annotations.json  # Human-annotated subset
│   └── results/         # Inference logs, CSVs
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── parser.py    # CoT to DAG logic (FR-001, FR-007)
│   │   ├── prompt_gen.py# Ordering strategies (FR-002)
│   │   ├── inference.py # llama.cpp runner (FR-003)
│   │   ├── analysis.py  # LMM, stats (FR-004, FR-005)
│   │   └── update_state.py # Versioning script
│   └── tests/
│       ├── test_parser.py
│       └── test_integration.py
└── artifacts/           # Checksums, logs
```

**Structure Decision**: Single project structure selected. Separation of `data/`, `code/`, and `artifacts/` ensures strict adherence to Constitution Principle III (Data Hygiene) and IV (Single Source of Truth). The `src/` subdirectory keeps the environment isolated.

## Complexity Tracking

No violations found. The complexity (DAG parsing + LMM) is necessary to address the core research question (Logical vs. Semantic ordering) and is feasible within the 6h CPU limit by using sampled data and efficient `networkx` algorithms.

## FR-001 & FR-007 Validation Strategy (Generalized)

Due to the unavailability of the specific "GeoQA" dataset with expert ratings:
1.  **Gold Standard Creation**: A subset of 50 traces will be manually annotated by **2 independent domain experts** for "Logical Complexity" (scale 1-5).
2.  **Validation Metric**: Pearson correlation (`r`) between `DAG Max Depth` and `Human Rated Complexity`.
3.  **Acceptance**: `r ≥ 0.6`. If not met, the "Logical Difficulty Score" is deemed invalid for this dataset, and the study will be limited to descriptive analysis only.
4.  **Storage**: Annotations stored in `data/processed/gold_standard_annotations.json`.

## FR-004 Statistical Method (LMM)

Due to the low power of ANOVA on n=10 seeds:
1.  **Method**: Linear Mixed-Effects Model (LMM) using `statsmodels` or `pymer4`.
2.  **Fixed Effects**: `Strategy`, `ModelType`, `Strategy:ModelType` interaction.
3.  **Random Effects**: `(1 | Seed)`, `(1 | PromptID)` to account for trial-level variance.
4.  **Justification**: This allows using all individual trial data (n=360+) rather than aggregating to n=10, significantly increasing statistical power.
5.  **Deviation**: This is a necessary deviation from the original spec (FR-004) to ensure scientific validity.
