# Implementation Plan: Memory Load‑Adaptive Text Presentation for Abstract Concept Retention

**Branch**: `001-memory-load-adaptive-text` | **Date**: 2026-06-24 | **Spec**: `specs/001-memory-load-adaptive-text/spec.md`
**Input**: Feature specification from `/specs/001-memory-load-adaptive-text/spec.md`

## Summary

This feature implements a computational pipeline to simulate a "Memory Load-Adaptive" environment using the **Pupil Labs Reading** dataset. The system computes a Cognitive Load Index (CLI) from pupil dilation time series and derives a "High Load Exposure" metric (the proportion of time windows where CLI > 0.5 SD). The analysis tests the **associational** relationship between this high-load exposure and delayed recall of abstract concepts, explicitly acknowledging that the dataset lacks the "simplified text" required for true adaptive intervention. Consequently, the study frames results as an association between physiological load states and retention, rather than a causal claim of pedagogical improvement.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels` (for LME), `pyarrow` (for parquet), `openneuro-py` (for dataset access).  
**Storage**: Local file system (`data/derived/`), no external database.  
**Testing**: `pytest` (unit tests for CLI calculation, integration tests for aggregation logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPU cores, ~7 GB RAM).  
**Project Type**: Computational research pipeline / data analysis script.  
**Performance Goals**: Total pipeline runtime ≤ 30 minutes on CPU-only hardware.  
**Constraints**: No GPU usage; memory footprint < 7 GB; strict adherence to low-pass filtering and -second windowing for CLI.  
**Scale/Scope**: Processing of the **Pupil Labs Reading (ds004041)** dataset; analysis of participant-level random effects.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Rationale |
|-----------|-------------------|--------------------|
| **I. Reproducibility** | **Compliant** | All random seeds will be pinned in `code/`. External datasets fetched programmatically from the verified HuggingFace URL for ds004041. `requirements.txt` will pin exact versions. |
| **II. Verified Accuracy** | **Compliant** | Citations for the dataset and methodology will be validated against the "Verified datasets" block using the `Reference-Validator Agent` and `CITATION_TITLE_OVERLAP_THRESHOLD` logic. |
| **III. Data Hygiene** | **Compliant** | Raw data (parquet) will be checksummed. Derived data (CLI, exposure metrics) stored in `data/derived/` with provenance. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All statistics in the final report will be generated directly from `results/` CSVs produced by the code. |
| **V. Versioning Discipline** | **Compliant** | Artifacts will carry content hashes. The `state/projects/PROJ-557...yaml` file will be updated with the `updated_at` timestamp upon artifact changes, as required by the Constitution. |
| **VI. Statistical Rigor** | **Compliant** | LME model formula `Recall ~ ProportionHighLoad*PassageType + (1|Participant)` and a large-scale permutation test will be implemented exactly. Sensitivity analysis (across a range of standard deviation values) included. |
| **VII. Human Data Privacy** | **Compliant** | No PII will be added. Derived data will be screened. Participant IDs will remain as opaque tokens from the source dataset. |

## Project Structure

### Documentation (this feature)

```text
specs/001-memory-load-adaptive-text/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later, not present now)
```

### Source Code (repository root)

```text
projects/PROJ-557-memory-palace-pedagogy-vr-enhanced-spati/
├── data/
│   ├── raw/             # Downloaded parquet files (checksummed)
│   ├── derived/         # CLI time series, exposure metrics
│   └── metadata.yaml    # Dataset version, checksums
├── code/
│   ├── __init__.py
│   ├── preprocessing.py # Blinks removal, filtering, baseline correction
│   ├── cli_engine.py    # Z-score calculation, thresholding
│   ├── simulation.py    # Exposure metric generation (Aggregation)
│   ├── analysis.py      # LME fitting, permutation test, sensitivity analysis
│   └── main.py          # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_cli_engine.py
│   │   └── test_simulation.py
│   └── integration/
│       └── test_pipeline.py
├── results/
│   ├── model_summary.csv
│   └── permutation_pvalue.csv
└── requirements.txt
```

**Structure Decision**: Single-project structure selected. The pipeline is a linear research workflow (Download -> Preprocess -> Aggregate -> Analyze) rather than a multi-service web app. This minimizes overhead and ensures all steps run within the 7 GB RAM constraint of the CI runner.

## Complexity Tracking

No violations detected. The complexity is driven by the statistical rigor requirements (LME + Permutation) and the physiological signal processing (filtering/z-score), which are necessary to satisfy FR-001, FR-004, and FR-005. Simpler alternatives (e.g., t-tests without random effects) were rejected because they would violate the Constitution Principle VI (Statistical Rigor) and the specific requirements of the user story (US-3).