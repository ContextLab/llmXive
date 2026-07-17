# Implementation Plan: Visual Detail and False Memory Susceptibility

**Branch**: `001-visual-detail-false-memory` | **Date**: 2026-06-30 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-visual-detail-false-memory/spec.md`

## Summary

This project implements a computational psychology pipeline to investigate how visual scene complexity influences false memory susceptibility. The system downloads scene images from the COCO dataset. (as a verified open substitute for Visual Genome), generates two manipulated variants per image (enhanced vs. reduced detail), and administers a recognition-based false memory test to participants. Statistical analysis (repeated-measures ANOVA) will determine if detail manipulation significantly alters false alarm rates for lure items, adhering to strict reproducibility and ethics guidelines.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (Hugging Face), `Pillow` (image manipulation), `scipy` (statistics), `pandas`, `matplotlib`, `streamlit` (participant interface), `pytest`, `wordnet` (semantic plausibility)  
**Storage**: Local filesystem (`data/stimuli/`, `data/responses/`, `data/logs/`)  
**Testing**: `pytest` (unit/integration), manual verification of image outputs  
**Target Platform**: Linux (GitHub Actions free-tier runner), Web browser (participant interface)  
**Project Type**: Research pipeline / Web application  
**Performance Goals**: Image manipulation < 30s/image; Analysis < 30min on CPU; Interface latency < 1s  
**Constraints**: ≤ 7 GB RAM, ≤ 14 GB disk, no local GPU, IRB compliance mandatory  
**Scale/Scope**: 30+ baseline images (validated for annotation density), 50+ participant sessions, 1000+ total responses  

> Empirical specifics (exact counts, dataset sizes) are deferred to the research phase but constrained by compute feasibility. The "30 baseline images" target is contingent on the successful implementation of the "skip and log" logic (T018) and the "Annotation Density Check".

## Constitution Check

**Status**: PASSED (with explicit mitigation for dataset substitution and scope boundaries)

1.  **I. Reproducibility**: All random seeds pinned in `code/utils/seeds.py`. External datasets fetched via `datasets.load_dataset` with pinned version. Power analysis simulation uses the same seeds for reproducibility.
2.  **II. Verified Accuracy**: Citations in `research.md` limited to verified HuggingFace sources (COCO dataset). Dataset substitution (COCO for Visual Genome) is explicitly documented as a deviation due to lack of verified open URL for Visual Genome.
3.  **III. Data Hygiene**: All stimulus metadata checksummed. Raw responses stored before any processing. PII stripped at ingestion.
4.  **IV. Single Source of Truth**: All statistics derived programmatically from `data/responses/` via `code/analysis/stats.py`. No manual entry.
5.  **V. Versioning**: Content hashes recorded in `state/` for all artifacts.
6.  **VI. Human Subjects Ethics**: **CRITICAL**: The plan explicitly excludes biological mechanism mapping (T040-T042). The project scope is strictly behavioral. IRB templates and consent flows are implemented in `code/interface/consent.py`. A fixed reading time is enforced via a UI timer.
7.  **VII. Stimulus Standardization**: Metadata files (`data/stimuli/{id}.yaml`) generated for every manipulated image, recording object lists and parameters, adhering to `contracts/stimulus_metadata.schema.yaml`.

**Scope Boundary**:
-   **REMOVED**: Tasks T040-T042 (Biological Mechanism Mapping). These tasks are explicitly excluded from the implementation scope as they represent scope creep and are not supported by the spec or data model.
-   **REMOVED**: Task T044 (Code cleanup) is atomized into specific refactoring actions in the implementation phase.

**Dataset Deviation**:
-   **Visual Genome** is replaced by **COCO 2017** because the input block contained no verified open URL for Visual Genome. The "Complexity Score" metric is recalibrated for COCO's annotation density.

## Project Phases

### Phase 0: Power Analysis (Blocking Gate)
-   **Goal**: Calculate required sample size (N ≥ 50) before any data collection.
-   **Action**: Run `code/analysis/stats.py --power-analysis`.
-   **Gate**: Pipeline halts if `data/analysis/power_report.json` is missing or N < 50.

### Phase 1: Stimuli Generation
-   **Goal**: Download images, filter for complexity, and generate variants.
-   **Action**:
    1.  `downloader.py`: Fetch COCO 2017.
    2.  `filter.py`: Calculate object density, select images spanning Q1-Q3 (range ≥ 0.3).
    3.  `manipulator.py`: Create Enhanced/Reduced versions. **Error Handling**: If manipulation fails, skip image, log to `data/logs/manipulation_errors.log`, and continue.
    4.  `metadata.py`: Generate `stimuli/{id}.yaml` adhering to schema.

### Phase 2: Participant Interface
-   **Goal**: Collect responses.
-   **Action**: `streamlit run code/interface/app.py`.
-   **Constraint**: Consent form must be displayed for ≥ 5 minutes (enforced by UI timer).

### Phase 3: Analysis
-   **Goal**: Run ANOVA and generate results.
-   **Action**: `code/analysis/stats.py --analyze`.

## Project Structure

### Documentation

```text
specs/001-visual-detail-false-memory/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code

```text
projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── seeds.py           # Global random seeds (linked to power analysis)
│   │   └── logging.py         # Structured logging for errors
│   ├── stimuli/
│   │   ├── downloader.py      # COCO fetcher
│   │   ├── filter.py          # Complexity stratification
│   │   ├── manipulator.py     # Image compositing (Enhanced/Reduced) with skip/log
│   │   └── metadata.py        # Stimulus metadata generation (adheres to schema)
│   ├── interface/
│   │   ├── app.py             # Streamlit participant interface
│   │   └── consent.py         # IRB consent flow (5-min timer)
│   ├── analysis/
│   │   ├── stats.py           # ANOVA, power analysis, corrections
│   │   └── viz.py             # Plotting
│   └── tests/
│       ├── unit/
│       │   ├── test_manipulator.py
│       │   └── test_stats.py
│       └── integration/
│           └── test_full_pipeline.py
├── data/
│   ├── stimuli/               # Generated images + metadata
│   ├── responses/             # Participant data (anonymized)
│   ├── logs/                  # Error logs (e.g., manipulation_errors.log)
│   ├── ethics/                # Consent templates (consent_template.md)
│   └── analysis/              # Power reports and results
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: A modular monolithic structure is selected. The separation of `stimuli`, `interface`, and `analysis` ensures independent testing of the pipeline components as required by the spec's "Independent Test" criteria. The `data/` directory is strictly append-only for raw responses to satisfy Data Hygiene.

## Complexity Tracking

No additional complexity layers are introduced. The previous iteration's biological mechanism mapping (Phase 6) is removed entirely to align with the spec's "associational" scope and Constitution VI. The complexity is limited to:
1.  Robust image manipulation with error handling (skip/log).
2.  Secure participant data handling (anonymization).
3.  Statistical rigor (power analysis, multiple comparison correction).
4.  Semantic coherence control for lure generation.