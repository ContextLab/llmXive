# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-visual-salience-moral-judgments/spec.md`

## Summary

This project implements a controlled experimental pipeline to test whether increasing the visual salience (luminance contrast/brightness) of target regions in morally ambiguous scenarios alters blame ratings. The approach involves: (1) ingesting the verified open **MoralD** dataset (or a validated synthetic generation pipeline if specific image subsets are unavailable), (2) programmatically manipulating images to create low/medium/high salience variants while verifying semantic integrity with a quantitative 'Moral Intent Preservation' metric, (3) deploying a within-subject survey with a Latin Square balanced design to collect blame ratings, and (4) analyzing the data using Cumulative Link Mixed Models (CLMM) with robust corrections for multiple comparisons. The implementation prioritizes CPU feasibility on GitHub Actions, using streaming for data and scaled-down subsets where necessary, while ensuring all steps are reproducible and adhere to the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `Pillow`, `scikit-learn`, `statsmodels`, `transformers` (CPU-only inference), `datasets` (Hugging Face), `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `bert-moral-intent` (custom CPU-tractable model)  
**Storage**: Local file system (`data/`), JSON/Parquet for structured data, SQLite for survey responses (optional, or CSV)  
**Testing**: `pytest` (unit/integration), `pytest-cov` for coverage  
**Target Platform**: Linux (GitHub Actions runner), CPU-first with optional Kaggle GPU offload for CLIP/BERT embedding extraction if needed  
**Project Type**: research-pipeline (data processing, survey simulation, statistical analysis)  
**Performance Goals**: Process ≤100 images for pilot; full pipeline ≤20 scenarios with 3 variants each; analysis complete within 6 hours on CPU  
**Constraints**: ≤7 GB RAM, ≤14 GB disk, no local GPU (unless offloaded to Kaggle), no access to gated datasets  
**Scale/Scope**: Initial pilot with ambiguous scenarios; full study design supports up to 50 scenarios with 100+ participants

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds pinned in `code/`; external datasets (MoralD) fetched from canonical Hugging Face sources; `requirements.txt` ensures dependency consistency.
- **II. Verified Accuracy**: Citations in `research.md` limited to verified URLs from the provided block; title-overlap threshold enforced by Reference-Validator.
- **III. Data Hygiene**: Raw data checksummed; transformations produce new files with derivation logs; PII scan enforced.
- **IV. Single Source of Truth**: All figures/statistics trace to `data/` rows and `code/` blocks; no hand-typed values.
- **V. Versioning Discipline**: Content hashes for artifacts; `state/` updated on changes.
- **VI. Stimulus-Control Integrity**: Visual manipulations generated programmatically with versioned parameters defined in `config/manipulation.yaml` and enforced by `contracts/stimulus.schema.yaml` (which requires a `version` field); CLIP similarity ≥0.95 and 'Moral Intent Preservation' score ≥0.90 enforce isolation of salience.
- **VII. Behavioral Response Validation**: Survey responses link participant ID, `variant_id` (in `contracts/response.schema.yaml`) or `stimulus_id` (in `contracts/survey_responses.schema.yaml`), and blame rating. The `variant_id` in `response.schema.yaml` acts as a foreign key to the `stimulus_manifest.schema.yaml`, ensuring the linkage between the specific stimulus version and the behavioral response required for circularity checks.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-salience-moral-judgments/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── data/
│   ├── raw/                 # Downloaded datasets (streamed or sampled)
│   ├── processed/           # Manipulated stimuli, cleaned survey data
│   └── checksums.txt        # Artifact hashes
├── code/
│   ├── 01_ingest_and_filter.py
│   ├── 02_human_coding.py   # Simulated or integrated with external tool
│   ├── 03_manipulate_stimuli.py
│   ├── 04_survey_deployment.py
│   ├── 05_data_cleaning.py
│   ├── 06_analysis_clmm.py
│   └── requirements.txt
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── docs/
    └── constitution.md
```

**Structure Decision**: Single project structure chosen for research pipeline simplicity; all scripts in `code/` with modular design for ingest, manipulation, survey, cleaning, and analysis. `data/` organized by raw/processed with checksums for hygiene.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed; no violations requiring justification. | N/A |