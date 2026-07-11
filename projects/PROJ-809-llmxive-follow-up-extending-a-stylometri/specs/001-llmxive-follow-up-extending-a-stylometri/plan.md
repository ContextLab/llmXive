# Implementation Plan: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-04 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary

This project implements a stylometric analysis pipeline to extend the findings of "A Stylometric Application of Large Language Models." The primary requirement is to determine if character-level n-gram models (orders 4-6) can distinguish between scientific authors based solely on abstract text, outperforming a function-word baseline. The technical approach involves: (1) ingesting a filtered subset of the arXiv dataset (cs.CL, physics.gen-ph, q-bio.QM, with fallback to cs.AI/stat.ML) to build a balanced corpus of multiple authors via stratified random sampling; (2) training CPU-efficient n-gram models with Kneser-Ney smoothing and sparsity checks; (3) computing a cross-evaluation perplexity matrix using a pre-registered primary model (n=5) to avoid selection bias; and (4) validating results via classification accuracy, McNemar's test (on n=5 only), and robustness checks on synthetic hybrid texts with random-swap controls. All operations are constrained to CPU-only execution on GitHub Actions free-tier resources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `scikit-learn`, `scipy`, `numpy`, `pandas`, `pyyaml`  
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for models/metrics)  
**Testing**: `pytest` (contract tests against `contracts/*.schema.yaml`, unit tests for preprocessing/logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU and RAM resources

The research question, method, and references remain unchanged as per the planning document requirements.)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Total runtime ≤ 1.5 hours; Peak RAM ≤ 6 GB; Model training per author ≤ 30s (optimized vectorization).  
**Constraints**: No GPU/CUDA; No transformer fine-tuning; Strict adherence to character-level n-grams; Pre-registered n=5 for primary hypothesis testing; Bonferroni correction applied only if multiple orders are tested (now restricted to sensitivity analysis).  
**Scale/Scope**: A cohort of authors, a substantial collection of abstracts, Multiple n-gram orders (4,5,6) for sensitivity, function-word baseline.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All scripts will use pinned random seeds (`numpy`, `random`, `python`). Dataset versioning via `datasets` library. No manual data editing. |
| **II. Verified Accuracy** | ✅ PASS | Dataset source is `arXiv` via HuggingFace (verified URL). All citations in `research.md` will be validated against primary sources. |
| **III. Data Hygiene** | ✅ PASS | Raw data downloaded once, checksummed (SHA-256) and recorded in `state/...yaml` artifact_hashes map immediately upon download. Preprocessing creates new files. PII scan will be run. |
| **IV. Single Source of Truth** | ✅ PASS | Final metrics (accuracy, p-values) will be generated programmatically from `data/` artifacts and written to `results/` JSON/CSV, never hand-typed. |
| **V. Versioning Discipline** | ✅ PASS | All artifacts (models, datasets) will carry content hashes. A dedicated `update_state.py` script will update the project state file (`state/projects/...yaml`) with artifact hashes upon completion of Phase 3. |
| **VI. Lightweight Modeling Fidelity** | ✅ PASS | Plan strictly uses character-level n-grams (n=4-6) via `scikit-learn` or custom CPU maps. No transformers. |
| **VII. Domain-Constraint Sensitivity** | ✅ PASS | Phase 3 explicitly includes generating and evaluating "hybrid" abstracts with random-swap controls to test signal degradation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Source of Truth)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_ingestion.py          # FR-001, FR-002, FR-009
│   ├── model_training.py          # FR-003, FR-011
│   ├── evaluation.py              # FR-004, FR-005, FR-010
│   ├── baseline.py                # FR-006
│   ├── robustness.py              # FR-007
│   ├── utils.py                   # Tokenization, logging
│   ├── update_state.py            # Constitution V: State file updater
│   └── main.py                    # Orchestration
├── data/
│   ├── raw/                       # Downloaded arXiv subset
│   ├── processed/                 # Cleaned, tokenized, split
│   └── hybrid/                    # Synthetic abstracts
├── artifacts/
│   ├── models/                    # Pickled n-gram models
│   └── metrics/                   # Perplexity matrix, results JSON
├── contracts/                     # Copied from specs/ during setup
│   └── *.schema.yaml
└── tests/
    ├── unit/
    ├── contract/                  # Validates against contracts/*.schema.yaml
    └── integration/
```

**Structure Decision**: Single project structure (`code/`, `data/`, `artifacts/`) selected to align with the research pipeline nature of the work. This minimizes overhead and ensures data flows sequentially from ingestion to evaluation without complex API layers. The `contracts/` directory in `specs/` is the source of truth and is copied to `code/contracts/` during the build/setup phase.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Multiple N-gram Orders (4,5,6)** | Required by spec for sensitivity analysis, but **n=5** is pre-registered as the primary test to avoid selection bias (FR-010). | Testing a single order would fail the sensitivity requirement; testing all without pre-registration inflates Type I error. |
| **Hybrid Abstract Generation** | Required by FR-007 and Constitution Principle VII. | A simple accuracy metric on original text cannot distinguish between topical bias and true stylometric signal. |
| **Kneser-Ney Smoothing** | Required by FR-011 due to limited data per author (a small number of abstracts). | Standard Maximum Likelihood Estimation (MLE) would suffer severe data sparsity, leading to infinite perplexity for unseen n-grams. |
| **Stratified Random Sampling** | Required to avoid selection bias from "top 20" volume. | Selecting by volume confounds "style" with "productivity". |

## Phase Breakdown

### Phase 0: Data Ingestion & Hygiene
1.  Download `arXiv` dataset.
2.  **Checksum**: Compute SHA-256 of raw download; write to `state/...yaml` (Constitution III & V).
3.  Filter by categories (cs.CL, physics.gen-ph, q-bio.QM) and fallback (cs.AI, stat.ML).
4.  Extract `lead_author` as `authors[0]`.
5.  Stratified random sampling to select a representative cohort of authors (minimum threshold of abstracts per author).
6.  Preprocess and split the data into training and validation sets using a standard partitioning strategy.

### Phase 1: Model Training
1.  Train n-gram models (n=4, 5, 6) for each author.
2.  **Sparsity Check**: If n=6 sparsity > threshold, downgrade to n=5 for that author.
3.  Save models to `artifacts/models/`.

### Phase 2: Evaluation & Baseline
1.  Compute perplexity matrix (using n=5 as primary).
2.  Train function-word baseline.
3.  **McNemar's Test**: Compare n=5 model vs. baseline (no Bonferroni needed for single primary test, but reported for sensitivity).
4.  Calculate accuracy.

### Phase 3: Robustness & State Update
1.  Generate hybrid abstracts (author swap + random swap control).
2.  Evaluate degradation.
3.  **State Update**: Run `update_state.py` to hash all artifacts and update `state/...yaml`.
