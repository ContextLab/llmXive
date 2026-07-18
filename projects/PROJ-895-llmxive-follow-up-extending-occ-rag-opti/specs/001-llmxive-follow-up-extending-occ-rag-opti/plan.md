# Implementation Plan: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

**Branch**: `001-llmxive-occrag-sparse-core` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-occrag-sparse-core/spec.md`
**Input**: Feature specification from `specs/001-llmxive-occrag-sparse-core/spec.md`

## Summary

This feature implements a gradient-free sensitivity analysis to test the hypothesis that faithful, context-grounded multi-hop reasoning in the OCC-RAG model relies on a sparse, localized sub-network. The plan covers: () independent single-unit masking to rank sensitivity, (2) construction of a pruned model retaining only critical parameters, (3) lightweight CPU-only fine-tuning to recover performance (with a control), and (4) statistical validation via paired t-test comparing sensitivity-ranked vs. random pruning. All operations are constrained to CPU-only execution within GitHub Actions free-tier limits (limited RAM, 6h runtime) using layer-wise loading.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only wheel), `transformers`, `scikit-learn`, `pandas`, `numpy`, `datasets`  
**Storage**: Local filesystem (temporary), `data/` for artifacts, `code/` for scripts  
**Testing**: `pytest` (unit tests for masking logic, schema validation), integration tests via script execution  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational research / data science  
**Performance Goals**: Memory < 7 GB RAM (via layer-wise loading); Runtime < 6 hours for full pipeline on sampled data  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; no deep-net training from scratch; dataset sampling required if A full dataset exceeds RAM capacity.; **k** fine-tuning subset explicitly defined  
**Scale/Scope**: Large-scale model (frozen for inference, pruned for fine-tuning); **k** synthetic examples for fine-tuning; A large synthetic corpus for sensitivity analysis (sampled)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
|-----------|-------------------|---------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; datasets fetched from canonical sources (or manual fetch); scripts runnable end-to-end. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` and `paper/` will be validated against primary sources; no title-token-overlap below. |
| **III. Data Hygiene** | PASS | Raw data checksummed in `state/`; transformations produce new files; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `state/` updated on changes. |
| **VI. Sparse Sub-network Identification Protocol** | PASS | Sensitivity analysis explicitly ranks parameters by masking-induced performance drop; **top [deferred]** selected for "Critical Sub-network". |
| **VII. Statistical Validation of Faithfulness Preservation** | PASS | Paired t-test on per-sample faithfulness scores (**p < 0.05**) required for all pruning comparisons (Sensitivity vs. Random). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-occrag-sparse-core/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 artifact (NOT created by /speckit-plan; generated in next phase)
```

### Source Code (repository root)

```text
projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/
├── code/
│   ├── requirements.txt
│   ├── 01_sensitivity_analysis.py
│   ├── 02_prune_model.py
│   ├── 03_finetune_pruned.py
│   ├── 04_statistical_validation.py
│   └── utils/
│       ├── faithfulness_score.py
│       ├── masking.py
│       └── dataset_loader.py
├── data/
│   ├── raw/
│   │   └── occ_rag_corpus.jsonl (checksummed)
│   ├── processed/
│   │   ├── sensitivity_results.csv
│   │   ├── pruned_model_weights.pt
│   │   └── faithfulness_scores.csv
│   └── checksums.json
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── paper/
    └── draft.md
```

**Structure Decision**: Single project structure (Option 1) selected to align with research workflow; scripts ordered by data dependency (download → analyze → prune → fine-tune → validate).

## Complexity Tracking

No violations identified. All complexity justified by spec requirements (gradient-free analysis, CPU constraints, statistical rigor).