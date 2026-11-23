# Implementation Plan: llmXive follow-up: extending "GENEB: Why Genomic Models Are Hard to Compare"

**Branch**: `001-gene-regulation` | **Date**: 2026-08-22 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-geneb-why-ge/spec.md`

## Summary

This feature implements a zero-cost heuristic for predicting genomic foundation model performance on GENEB benchmark tasks using only alignment-free sequence statistics. The pipeline downloads raw sequence data (from primary FASTA/sequence splits), computes a reduced set of low-dimensional features (e.g., k-mer entropy, GC-content variance), trains sparse regression models (Lasso/Elastic Net) and shallow ensembles to predict macro-MCC scores, and performs rigorous statistical validation (5-fold CV, permutation tests, sensitivity analysis).

**Critical Methodological Note**: This is an **observational study**. All findings regarding "architectural niches" are framed strictly as **associational correlations**. No causal claims (e.g., sequence properties *create* niches) are made, as no randomization or confounding control (matching, IVs) is possible with the available data.

The entire pipeline is constrained to run within 6 hours on a 2-core CPU with 7GB RAM, adhering to the project's computational efficiency principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `datasets` (Hugging Face), `pyyaml`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `outputs/`)  
**Testing**: `pytest` with contract validation against `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/output.schema.yaml`  
**Target Platform**: Linux server (GitHub Actions free-tier: 2 CPU, ~7GB RAM)  
**Project Type**: Computational research pipeline / CLI tool  
**Performance Goals**: Total pipeline execution ≤ 6 hours; feature extraction ≤ 2 hours; model training ≤ 2 hours  
**Constraints**: No GPU acceleration; no external annotations or embeddings; strict memory bounds (≤7GB); reproducible random seeds  
**Scale/Scope**: Processing a sufficient number of GENEB benchmark tasks to ensure statistical power in small-sample regression; reduced feature set (target < 10) after pre-modeling selection.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned in `code/`; external datasets fetched from canonical Hugging Face URLs; `requirements.txt` pins all dependencies. |
| **II. Verified Accuracy** | ✅ Compliant | All citations (GENEB paper, dataset URLs) verified against primary sources; no fabricated URLs. |
| **III. Data Hygiene** | ✅ Compliant | Raw data preserved unchanged in `data/raw/`; derivations written to `data/processed/` with checksums recorded in state file. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/statistics trace to `data/processed/` rows and `code/` blocks; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ Compliant | Artifacts carry content hashes; state file updated on artifact changes. |
| **VI. Computational Efficiency** | ✅ Compliant | Pipeline designed for -core CPU/7GB RAM; uses sparse regression and shallow ensembles; no GPU required. |
| **VII. Alignment-Free Feature Grounding** | ✅ Compliant | All features derived strictly from raw sequence statistics. **Traceability**: Features map 1:1 to `SequenceFeatureSet` in `data-model.md` (e.g., `nucleotide_entropy` → `nucleotide_entropy`, `gc_content` → `gc_content`). AT-Content excluded due to perfect collinearity with GC-Content. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── (tasks.md is a downstream artifact generated in the 'tasks' stage, not created here)
```

### Source Code (repository root)

```text
projects/PROJ-944-llmxive-follow-up-extending-geneb-why-ge/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Downloads GENEB metadata AND raw sequences (FASTA/split)
│   │   ├── extract_features.py  # Computes reduced set of sequence features
│   │   └── preprocess.py        # Handles NaNs, outliers, feature selection
│   ├── models/
│   │   ├── train.py             # Trains Lasso/Elastic Net/RF
│   │   ├── validate.py          # 5-fold CV + metrics
│   │   └── predict.py           # Generates predictions
│   ├── analysis/
│   │   ├── feature_importance.py
│   │   ├── sensitivity.py       # Threshold sweep
│   │   └── permutation.py       # Permutation test
│   └── main.py                  # Orchestrates full pipeline
├── data/
│   ├── raw/                     # Downloaded GENEB files (checksummed)
│   └── processed/               # Feature matrices, predictions
├── outputs/
│   ├── reports/                 # PDF/HTML reports
│   └── figures/                 # Plots
└── tests/
    ├── contract/                # Schema validation tests (against dataset.schema.yaml, output.schema.yaml)
    ├── integration/             # End-to-end pipeline tests
    └── unit/                    # Feature extraction, model tests
```

**Structure Decision**: Single-project structure (Option 1) selected. The pipeline is linear (download → extract → train → analyze → report), making a monolithic `code/` directory with modular subpackages appropriate. This minimizes overhead and aligns with the 6-hour CPU constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All requirements are met with a straightforward linear pipeline. No additional layers (e.g., microservices, complex caching) are needed given the small dataset size and CPU constraints. | N/A |

## Addressing Spec Root Cause (Typo)

The source spec (`spec.md`) contains a typo in User Story 1: "result must be a single float value between and 2.0". The lower bound is missing. This plan explicitly interprets the lower bound as **0.0** based on information theory (entropy ≥ 0). This requires a kickback to the spec author to correct the source text.