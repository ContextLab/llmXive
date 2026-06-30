# Implementation Plan: 001-predict-plant-disease-resistance

**Branch**: `001-predict-plant-disease-resistance` | **Date**: 2026-06-25 | **Spec**: `specs/001-predict-plant-disease-resistance/spec.md`
**Input**: Feature specification from `/specs/001-predict-plant-disease-resistance/spec.md`

## Summary

This project implements a reproducible, CPU-tractable pipeline to predict plant disease resistance using paired genomic (SNP) and metabolomic data. The system retrieves public data, preprocesses raw reads (fastp/bcftools) and metabolomics (MetaboAnalyst-compatible normalization), performs feature selection (LASSO/RF) with Benjamini-Hochberg correction, and trains Elastic-Net or Gradient-Boosting models. It validates performance via 5-fold cross-validation, permutation testing, and external validation, adhering to strict resource constraints (≤7 GB RAM, ≤6h runtime) on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `scipy`, `fastp` (via Docker/Conda), `bcftools` (via Docker/Conda), `pyyaml`, `requests`  
**Storage**: Local temporary directories within runner (no persistent DB); data cached in `data/` with checksums.  
**Testing**: `pytest` for unit/integration; contract tests against `contracts/*.schema.yaml`.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: CLI/Data Pipeline  
**Performance Goals**: Runtime ≤ 6 hours, Peak RAM ≤ 7 GB.  
**Constraints**: No GPU; no deep learning training; strict sample size validation (n ≥ 100); BH correction mandatory.  
**Scale/Scope**: Processing of 1-2 public multi-omics datasets; outputting ranked biomarkers and performance metrics.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | All code in `code/` uses pinned `requirements.txt`. Random seeds set globally. Docker container ensures environment parity. |
| **II. Verified Accuracy** | ✅ Pass | External citations in `research.md` strictly limited to URLs in the `# Verified datasets` block. No invented URLs. |
| **III. Data Hygiene** | ✅ Pass | Raw data preserved in `data/raw/`. Derived files in `data/processed/` with checksums recorded in `data_manifest.yaml`. No in-place modification. |
| **IV. Single Source of Truth** | ✅ Pass | All metrics in `paper/` generated directly from `code/` output logs; no manual transcription. |
| **V. Versioning Discipline** | ✅ Pass | Artifacts hashed in `state/` upon generation. `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Multi‑omics Provenance** | ✅ Pass | Data manifest (`data_manifest.yaml`) records NCBI SRA/MetaboLights accession numbers, query strings, and retrieval dates. |
| **VII. Statistical Rigor** | ✅ Pass | Pipeline enforces BH correction (p < 0.05), 5-fold CV, permutation testing (n=1000), and VIF diagnostics. Claims framed associationally. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-disease-resistance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-259-predicting-plant-disease-resistance-from/
├── data/
│   ├── raw/                 # Downloaded raw files (SRA, MetaboLights)
│   ├── processed/           # Aligned SNP/Metabolite matrices
│   └── data_manifest.yaml   # Provenance and checksums
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── download.py          # Data retrieval (SRA/MetaboLights)
│   ├── preprocess.py        # fastp, bcftools, metabolite normalization
│   ├── feature_selection.py # LASSO/RF, BH correction, sensitivity sweep
│   ├── train.py             # Elastic-Net / Gradient-Boosting, CV
│   ├── validate.py          # Permutation testing, VIF, external validation
│   ├── utils.py             # Logging, seed setting, error handling
│   └── requirements.txt     # Pinned dependencies
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── unit/
│       ├── test_feature_selection.py
│       └── test_preprocess.py
├── Dockerfile               # Reproducible environment (CPU only)
└── README.md
```

**Structure Decision**: Single project structure (`code/` + `data/` + `tests/`) selected to minimize overhead and ensure tight coupling between data provenance and processing logic, suitable for a CLI pipeline.

## Complexity Tracking

> **No violations detected.** The single-project structure and CPU-only constraints align with the project's scope and resource limits.
