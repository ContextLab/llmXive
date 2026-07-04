# Implementation Plan: The Impact of Emotional Expression in AI Avatars on User Trust

**Branch**: `001-emotional-synchrony-trust` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-emotional-synchrony-trust/spec.md`

## Summary

This project implements a computational pipeline to analyze the association between intra-modal emotional consistency (synchrony between facial expression and vocal prosody in AI avatars) and user trust scores. The approach involves extracting time-series features from video/audio using CPU-compatible tools (OpenFace, librosa) for real data, or generating synthetic landmark/prosody time-series directly for pipeline validation. The pipeline computes a cross-correlation consistency metric and performs Spearman correlation and ordinal regression analysis. The pipeline is designed to run entirely on free-tier GitHub Actions (CPU-only, ~7GB RAM) and handles missing/corrupted data gracefully.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `openface` (CPU binary), `librosa`, `scikit-learn`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `synthpop` (for synthetic landmark generation).  
**Storage**: Local file system (CSV/JSON/PNG artifacts in `data/` and `outputs/`)  
**Testing**: `pytest` (contract tests against YAML schemas `contracts/dataset_schema.yaml` and `contracts/feature_extraction_schema.yaml`, unit tests for feature extraction logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / Research tool  
**Performance Goals**: Complete analysis of N=500 interactions within 6 hours on 2 CPU cores, <7GB RAM peak.  
**Constraints**: No GPU; no deep learning training; must handle corrupted media files gracefully; must frame results as associational only.  
**Scale/Scope**: Analysis of video/audio interactions (or synthetic time-series); generation of statistical reports and visualizations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `requirements.txt` pins exact versions. External data sources (or fallback generation) are deterministic. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the "Verified datasets" block (currently empty, fallback to simulation). No unverified URLs will be used. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed on ingestion. Derived feature files (CSVs) checksummed and stored in `data/`. No in-place modification of raw files. |
| **IV. Single Source of Truth** | **PASS** | All statistics in reports generated directly from `code/` outputs. No manual transcription of numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts tracked in `state/`. Any change to extraction logic triggers a re-run and hash update. |
| **VI. Multimodal Feature Extraction Integrity** | **PASS** | Pipeline strictly uses OpenFace and librosa for real data. For simulation, uses `synthpop` to generate synthetic landmarks. Versions and config parameters logged in `code/`. Feature outputs checksummed. |
| **VII. Human-Subject Privacy** | **N/A (Simulation Phase)** | Current implementation uses synthetic data. Principle VII is **N/A** for the simulation phase. **Future Requirement**: Before ingesting real human data, a Data Collection Protocol must be executed to obtain informed consent and IRB documentation as specified in the Constitution. |

## Project Structure

### Documentation (this feature)

```text
specs/001-emotional-synchrony-trust/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Static schema definitions)
└── tasks.md             # Phase 2 output
```

**Note on `contracts/`**: This directory contains static YAML schema definitions (e.g., `dataset_schema.yaml`) used by the validation logic in `code/`. It is not executable code itself, but serves as the source of truth for data validation.

### Source Code (repository root)

```text
projects/PROJ-344-the-impact-of-emotional-expression-in-ai/
├── data/
│   ├── raw/                  # Raw video/audio (or simulated)
│   ├── processed/            # Extracted time-series (CSV)
│   └── features/             # Computed consistency scores
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, hyperparameters
│   ├── extract_features.py   # OpenFace & librosa extraction (real) OR synthpop generation (sim)
│   ├── compute_metrics.py    # Cross-correlation logic
│   ├── analyze.py            # Spearman & Ordinal Regression
│   ├── visualize.py          # Plotting logic
│   └── requirements.txt      # Pinned dependencies
├── tests/
│   ├── contract/             # Schema validation tests (validates against contracts/*.yaml)
│   ├── unit/                 # Logic tests (mocked data)
│   └── integration/          # End-to-end pipeline test
├── outputs/                  # Generated plots and reports
└── state/                    # Project state tracking
```

**Structure Decision**: Single project structure chosen for a research pipeline. All code resides in `code/` for reproducibility, with strict separation between raw data, processed features, and outputs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The pipeline is linear and modular. | A monolithic script would violate reproducibility and testability requirements (Constitution I & IV). |