# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2024-05-21 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary

This feature implements a computational pipeline to investigate associations between gut microbiome composition (16S rRNA data) and cognitive decline in aging populations. The technical approach involves ingesting American Gut Project (AGP) taxonomic data from the official Qiita/EBI repository and Health and Retirement Study (HRS) cognitive metadata from the official HRS portal, merging them by participant ID (if available), and filtering for age ≥ 60. The analysis uses **Cumulative Sum Scaling (CSS)** for normalization, **SparCC** and **SPIEC-EASI** for compositional correlation analysis, and **Random Forest** predictive modeling with nested cross-validation and **SHAP** interpretability. All steps are constrained to run on CPU-only GitHub Actions free-tier runners (≤7 GB RAM, ≤6 hours).

**Critical Feasibility Note**: The plan explicitly treats the linkage of AGP and HRS via a shared participant ID as a "Fatal Coverage Gap" condition. If the official datasets do not share a common identifier, the project is terminated immediately; no synthetic data or simulation studies are used to approximate the research question.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `statsmodels`, `scikit-bio`, `sparcc`, `shap`, `numpy`, `seaborn`, `pymice`  
**Storage**: Local file system (CSV/TSV/Parquet) within `data/` and `code/` directories; no external database.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data science / Computational biology pipeline.  
**Performance Goals**: Execution ≤ 6 hours, RAM ≤ 7 GB, Disk ≤ 14 GB.  
**Constraints**: No GPU, no CUDA, no 8-bit quantization. Data must be subset/sampled to fit memory.  
**Scale/Scope**: Analysis of merged samples (AGP+HRS overlap) and microbial genera.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Note |
|-----------|--------|---------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, random seeds, and deterministic data fetching from official Qiita/EBI and HRS sources. |
| **II. Verified Accuracy** | PASS | Plan restricts dataset citations to official sources (Qiita/EBI, HRS). No user-uploaded HuggingFace mirrors. |
| **III. Data Hygiene** | PASS | Plan requires checksumming of raw data, immutable derivations (new filenames), and PII scanning. |
| **IV. Single Source of Truth** | PASS | Plan ensures all figures/stats trace to `data/` rows and `code/` blocks. |
| **V. Versioning Discipline** | PASS | Plan includes content hashing strategy for artifacts. |
| **VI. Microbiome Data Provenance** | PASS | Plan explicitly sources AGP from official Qiita/EBI repository (Study ID) and HRS from official HRS portal, retaining sample IDs. |
| **VII. Predictive Modeling Transparency** | PASS | Plan mandates logging of seeds, hyperparameters, and use of **SHAP values** for feature importance, archived alongside model artifacts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-189-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/               # Downloaded AGP/HRS raw files (checksummed)
│   ├── processed/         # Merged, CSS-normalized datasets
│   └── models/            # Saved model artifacts (pickle/joblib)
├── code/
│   ├── requirements.txt   # Pinned dependencies
│   ├── 01_data_ingestion.py
│   ├── 02_preprocessing.py
│   ├── 03_correlation_analysis.py
│   ├── 04_predictive_modeling.py
│   ├── 05_sensitivity_analysis.py
│   └── utils/
│       ├── metrics.py
│       └── plot_helpers.py
├── tests/
│   ├── contract/          # Tests validating against contracts/*.schema.yaml
│   ├── integration/       # End-to-end pipeline tests
│   └── unit/              # Unit tests for helper functions
└── docs/
    └── paper_draft.md     # Draft manuscript
```

**Structure Decision**: Single project structure selected. The pipeline is linear (ingest → process → analyze → model) and does not require separate backend/frontend services. All logic resides in Python scripts under `code/` to ensure reproducibility and ease of CI execution. QIIME2 artifacts are not used; data is handled via CSV/Parquet.

## Complexity Tracking

No complexity violations detected. The plan adheres strictly to the spec's constraints (CPU-only, limited RAM) by explicitly defining data sampling and method choices (e.g., Random Forest over deep learning, CSS over rarefaction) that fit the hardware.