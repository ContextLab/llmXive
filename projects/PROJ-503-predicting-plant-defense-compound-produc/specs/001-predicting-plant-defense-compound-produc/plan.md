# Implementation Plan: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

**Branch**: `001-predict-plant-defense` | **Date**: 2026-06-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-predict-plant-defense/spec.md`

## Summary

This feature implements a computational pipeline to predict plant defense compound production from publicly available genomic and transcriptomic data. The approach involves: (1) **Phase 0 Data Discovery** to verify dataset availability and power requirements, (2) downloading paired gene-expression and metabolite data from GEO and Metabolomics Workbench, (3) preprocessing and feature selection based on KEGG defense pathways plus regulatory genes, (4) training **species-specific** Ridge Regression models with cross-validation and permutation testing, and (5) evaluating model performance against defined success criteria.

**⚠️ CRITICAL**: This plan is contingent on Phase 0 Data Discovery confirming verified plant omics datasets. Without verified sources, the project halts with error code E-DATASET.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, scipy, requests, pyyaml, biopython, statsmodels  
**Storage**: Local file system (data/, logs/, outputs/)  
**Testing**: pytest  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: computational pipeline / data science  
**Performance Goals**: Complete E2E pipeline within 4 hours on 2 CPU cores, ~7 GB RAM  
**Constraints**: No GPU, no CUDA, no large-LLM inference; data subset to fit memory budget  
**Scale/Scope**: Multi-omics integration for Arabidopsis and Solanum species (species-specific models)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass Phase 0 Data Discovery before Phase 1 research. Dataset availability status below.*

| Principle | Status | Mapping |
|-----------|--------|---------|
| I. Reproducibility (NON-NEGOTIABLE) | ⚠️ PENDING VERIFICATION | Random seeds pinned in code/; external datasets fetched from canonical sources; pipeline re-runnable on fresh GitHub Actions runner |
| II. Verified Accuracy | ⚠️ PENDING VERIFICATION | All citations in research.md validated against primary sources; Reference-Validator Agent checks title-token-overlap ≥0.7 |
| III. Data Hygiene | ✅ PASS | All data under data/ checksummed (SHA-256); transformations produce new files with documented derivation; PII scan enforced |
| IV. Single Source of Truth | ✅ PASS | All figures/statistics trace to data/ rows and code/ blocks; derived numbers not hand-typed into paper |
| V. Versioning Discipline | ✅ PASS | Artifacts carry content hashes; state YAML updated_at timestamp on changes |
| VI. Dataset Version Traceability | ⚠️ PENDING VERIFICATION | External omics datasets referenced by accession IDs + version/release date; data/sources.yaml documents accession, download date, preprocessing script version |
| VII. Statistical Validation Discipline | ✅ PASS | Performance metrics accompanied by 5-fold CV (mean+SD) and permutation-test p-value (≥1000 shuffles); claims of correlation supported by significant permutation test |

**⚠️ Dataset Availability**: All plant omics dataset sources currently show "NO VERIFIED SOURCE" in verified datasets block. Phase 0 must confirm dataset availability before proceeding. **If E-DATASET error occurs, the project cannot proceed.**

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-plant-defense/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-503-predicting-plant-defense-compound-produc/
├── code/
│   ├── requirements.txt
│   ├── data_download.py
│   ├── preprocessing.py
│   ├── feature_selection.py
│   ├── modeling.py
│   ├── evaluation.py
│   └── main.py
├── data/
│   ├── sources.yaml
│   ├── raw/
│   ├── processed/
│   └── paired/
├── logs/
│   ├── data_pairing.json
│   └── feature_filtering.csv
├── outputs/
│   └── models/
├── docs/
│   └── edge_cases.md
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: Single project structure (Option 1) chosen for computational pipeline simplicity; all code under code/, data under data/, outputs under outputs/, logs under logs/.

## Phase Definitions

### Phase 0: Data Discovery (MANDATORY BLOCKER)

1. Search GEO and Metabolomics Workbench for plant herbivore-stress datasets
2. Verify sample-level pairing feasibility (≥95% match rate per FR-009)
3. **Conduct power analysis**: n≥28-30 samples required for detecting r≥0.5 with 80% power at α=0.05
4. **ABORT** if: No verified plant datasets OR pairing <95% OR n<28
5. **ABORT** with E-DATASET if no verified plant omics datasets exist in verified datasets block

### Phase 1: Data Acquisition

1. Download verified GEO expression matrices (FR-001)
2. Retrieve verified Metabolomics Workbench metabolite data (FR-002)
3. Validate checksums (FR-009, SC-004)

### Phase 2: Preprocessing & Feature Selection

1. Normalize expression to TPM/FPKM; log-transform metabolites (FR-003)
2. Filter zero-variance genes (FR-003)
3. Select defense pathway genes + regulatory genes (FR-004, FR-004 Extended)
4. Species-specific z-score normalization (FR-010)

### Phase 3: Modeling & Evaluation

1. Train **species-specific** Ridge Regression models (FR-005)
2. 5-fold cross-validation; report RMSE, Pearson r (FR-005)
3. Permutation test with 1,000 iterations (FR-006)
4. Bonferroni correction across metabolites (FR-007)
5. Cross-species model is **exploratory only** if sample size permits

## Complexity Tracking

**Current Status**: Phase 0 Data Discovery BLOCKER active. Dataset availability pending verification from verified datasets block.

**Constitution Check**: Principles III, IV, V, VII pass. Principles I, II, VI remain PENDING until Phase 0 completes and datasets are verified.

**⚠️ ABORT CRITERIA**: If Phase 0 does not confirm verified plant omics datasets with ≥95% pairing and n≥28, the project halts with error code E-DATASET or E-PAIRING or E-POWER.

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md FR-010 still references cross-species model as primary, but this plan correctly defines species-specific models as PRIMARY with cross-species as exploratory-only. This requires spec.md revision (flagged for kickback).

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md Assumptions defers power analysis to implementation, but this plan requires explicit power analysis in Phase 0 (n≥28-30). This requires spec.md revision (flagged for kickback).