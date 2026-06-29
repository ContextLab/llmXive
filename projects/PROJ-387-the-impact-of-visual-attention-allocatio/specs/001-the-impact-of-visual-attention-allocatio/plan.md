# Implementation Plan: 001-visual-attention-recall

**Branch**: `001-visual-attention-recall` | **Date**: 2026-06-24 | **Spec**: `specs/001-visual-attention-recall/spec.md`
**Input**: Feature specification from `/specs/001-visual-attention-recall/spec.md`

## Summary

This project implements a statistical analysis pipeline to determine if visual attention allocation (fixation duration, saccade patterns, gaze distribution) predicts recall accuracy for emotionally valenced narrative content. The approach uses Linear Mixed-Effects Models (LMM) on public eye-tracking data, applying Bonferroni correction for multiple comparisons and framing results as associational.

**⚠️ CRITICAL DATA BLOCKER**: Per the Verified datasets block in the project's research context (see `research.md:Dataset Strategy`), **no verified eye-tracking dataset exists containing all required variables**. The spec's Assumptions section states "public eye-tracking datasets referenced (e.g., OpenNeuro) contain the necessary columns" — this is an **unverified claim that contradicts research findings**. This plan proceeds to implement validation logic only; statistical analysis cannot execute without verified data acquisition.

**Pipeline Behavior**: The implementation will:
1. Ingest and validate data per US-1 (FR-002)
2. **HALT** with documented data gap if required variables missing (no analysis)
3. **BLOCK** research_complete stage until verified dataset added to project

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local filesystem (`data/`, `output/`)  
**Testing**: `pytest`  
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h limit)  
**Project Type**: Data Science Pipeline  
**Performance Goals**: <6h runtime, <7 GB RAM usage  
**Constraints**: CPU-only (no GPU/CUDA), no deep learning, no causal claims  
**Scale/Scope**: Single dataset ingestion, Multiple hypothesis tests (multiple metrics × multiple valence), sensitivity analysis

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Plan |
|-----------|-----------------|
| **I. Reproducibility** | Random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. External datasets fetched from canonical sources (if verified). |
| **II. Verified Accuracy** | Reference-Validator Agent checks citations in `research.md` against primary sources before review. |
| **III. Data Hygiene** | Data checksummed in `state/`. Raw data preserved in `data/raw/`. Derivations in `data/processed/`. PII scan on commit. |
| **IV. Single Source of Truth** | All figures/stats trace to `data/` and `code/`. No hand-typed numbers in paper. |
| **V. Versioning Discipline** | Content hashes tracked in `state/`. Artifact changes update `updated_at` timestamps. |
| **VI. Eye‑Tracking Data Integrity** | Ingestion script checks calibration status and track loss (≤5%) before processing. |
| **VII. Emotional‑Valence Annotation Consistency** | Valence labels stored in `data/valence/` using standardized scales. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-attention-recall/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── ingestion/
│   ├── validate_data.py      # Validates FR-002, US-1
│   └── load_data.py          # Loads data per FR-001
├── analysis/
│   ├── lmm_model.py          # LMM computation per FR-003
│   ├── correction.py         # Bonferroni per FR-004
│   └── sensitivity.py        # Threshold sweep per FR-006
├── reporting/
│   ├── visualize.py          # Plots per FR-007
│   └── generate_report.py    # Summary per FR-005
└── utils/
    ├── config.py             # Random seeds, paths
    └── logger.py

data/
├── raw/                      # Downloaded datasets (checksummed)
├── processed/                # Cleaned data
├── eye-tracking/             # Calibration/quality metrics (Constitution VI)
└── valence/                  # Annotation files (Constitution VII)

output/
├── plots/                    # Scatter & Histograms
└── results/                  # LMM coefficients, corrected p-values

tests/
├── contract/                 # Schema validation
└── unit/                     # Logic tests
```

**Structure Decision**: Single project structure (`code/`) chosen for simplicity and alignment with data science pipeline patterns. No web/mobile components.

## Complexity Tracking

> **N/A** — No violations requiring justification.

## Plan Completeness: FR/SC Mapping

| ID | Requirement | Plan Phase/Step | Notes |
|----|-------------|-----------------|-------|
| **FR-001** | Load eye-tracking data (CSV/EDF) | `code/ingestion/load_data.py` | CPU-only, no GPU. |
| **FR-002** | Validate variables & quality | `code/ingestion/validate_data.py` | Checks columns + track loss. **Halt if missing (See Research.md).** |
| **FR-003** | Compute LMM (Attention vs Recall) | `code/analysis/lmm_model.py` | `statsmodels` mixedlm. |
| **FR-004** | Bonferroni correction | `code/analysis/correction.py` | 9 tests (3 metrics × 3 valence). |
| **FR-005** | Associational disclaimer | `code/reporting/generate_report.py` | Hardcoded text block. |
| **FR-006** | Sensitivity analysis (p-sweep) | `code/analysis/sensitivity.py` | Sweep {0.01, 0.05, 0.1}. |
| **FR-007** | Generate plots (Scatter/Hist) | `code/reporting/visualize.py` | `matplotlib`/`seaborn`. |
| **FR-008** | Runtime ≤6h, 2 CPU | Pipeline design | CPU-tractable methods only. |
| **SC-001** | Ingestion success ≥95% | `code/ingestion/validate_data.py` | Metric logged. **Blocked by data availability.** |
| **SC-002** | LMM completion rate [deferred] | `code/analysis/lmm_model.py` | Error handling per test. |
| **SC-003** | Corrected p-values present | `code/analysis/correction.py` | Output schema validation. |
| **SC-004** | Runtime within limit | CI Job Timeout | 6h max. |
| **SC-005** | Plot completeness (≥2 per valence) | `code/reporting/visualize.py` | File count check. |

## Spec Contradiction Resolution Required

The following spec Assumptions contain unverified claims that must be addressed before research_complete:

| Spec Assumption | Research Finding | Resolution Required |
|-----------------|------------------|---------------------|
| "public eye-tracking datasets referenced (e.g., OpenNeuro) contain the necessary columns" | No verified source found for any required variable | **Blocker**: Either (a) add verified dataset to project, or (b) revise research question to match available data |
| "Valence annotations will be sourced from dataset metadata OR computed via NLP" | NLP sentiment scoring has NO verified source; circularity risk if used | **Blocker**: Must use human-rated metadata only, or document NLP as separate validation study |
| "All recall measures used in the source datasets are validated instruments" | Cannot verify without dataset access | **Blocker**: Must document instrument validation evidence in dataset metadata |

**Action Required**: Spec must be updated to reflect research findings OR verified datasets must be added to the project's Verified datasets block.