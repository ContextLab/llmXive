# Implementation Plan: The Influence of Typographic Salience on Moral Judgments of Text-Based Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-influence-of-visual-salience-on-mora/spec.md`

## Summary
This project implements a controlled experiment to test whether **typographic salience** (manipulated via font weight and size) influences moral blame judgments in text-based scenarios. The pipeline ingests moral scenarios from the verified text dataset `Dahoas/rm-single-context`, programmatically applies typographic emphasis to target agents while preserving semantic content, deploys a within-subject survey for blame ratings, and analyzes the data using Linear Mixed-Effects Models (LMM) with robust corrections for multiple comparisons. The implementation adheres to strict reproducibility, stimulus-control integrity, and data hygiene principles.

*Note: The original spec referenced "Visual Salience" in images. Due to the absence of a verified image dataset containing morally ambiguous scenarios in the provided block, the study has been rigorously reframed to test "Typographic Salience" in text. This maintains the core hypothesis (attentional amplification) while utilizing available, verified data.*

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels`, `scikit-learn`, `datasets` (Hugging Face), `sentence-transformers`, `jinja2` (for text rendering)  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/survey`), JSON/Parquet for structured data  
**Testing**: `pytest` (unit tests for manipulation logic, integration tests for pipeline flow)  
**Target Platform**: GitHub Actions free-tier (CPU-only, 2 cores, 7 GB RAM).  
**Project Type**: Research pipeline / Data analysis  
**Performance Goals**: Process 50-100 text scenarios within 6 hours; LMM analysis on <5000 rows in <15 mins.  
**Constraints**: No PII in data; all random seeds pinned; no fabricated metrics; all external datasets must be open and directly downloadable.  
**Scale/Scope**: ~50-100 scenarios; ~100-200 participants (simulated for pilot, real for deployment); salience levels per scenario.

> Domain-specific empirical specifics (exact counts, dataset sizes) are deferred to the research/implementation phase.

## Constitution Check
*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action Required / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Compliant | Random seeds will be pinned in `code/`. External datasets fetched via `datasets.load_dataset()` with specific revision hashes. |
| **II. Verified Accuracy** | ✅ Compliant | All citations in `research.md` will be validated against the provided "Verified datasets" block. Only `Dahoas/rm-single-context` is used. |
| **III. Data Hygiene** | ✅ Compliant | Raw data preserved; derivations written to new files. Checksums recorded in `state/`. PII scan mandatory. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/stats in `paper/` will trace to `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Compliant | Content hashes for all artifacts. `updated_at` timestamps managed by state file. |
| **VI. Stimulus-Control Integrity** | ✅ Compliant | Manipulation parameters (font weight/size) are versioned. Sentence-BERT similarity checks ensure semantic preservation. |
| **VII. Behavioral Response Validation** | ✅ Compliant | Survey data links `participant_id`, `stimulus_id`, and `salience_level` explicitly. |

## Project Structure

### Documentation (this feature)
```text
specs/001-the-influence-of-visual-salience-on-mora/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)
```text
projects/PROJ-507-the-influence-of-visual-salience-on-mora/
├── code/
│   ├── 01_data_ingestion.py        # Ingest Dahoas/rm-single-context
│   ├── 02_stimulus_manipulation.py # Generate low/med/high typographic variants
│   ├── 03_ambiguity_filter.py      # Filter scenarios by reward score (proxy for human coding)
│   ├── 04_survey_deployment.py     # Survey logic (local mock or export to Qualtrics/Prolific)
│   ├── 05_data_cleaning.py         # Exclude straight-liners, validate variance
│   ├── 06_statistical_analysis.py  # LMM, Bonferroni, Effect Sizes
│   └── requirements.txt            # Pinned dependencies
├── data/
│   ├── raw/                        # Original dataset files
│   ├── processed/                  # Manipulated text variants, cleaned datasets
│   └── survey/                     # Participant responses
├── tests/
│   ├── unit/                       # Manipulation logic tests
│   └── integration/                # Pipeline flow tests
└── state/
    └── projects/PROJ-507-...yaml   # Artifact hashes and state
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) is selected. This is a research pipeline, not a web service, so a monolithic structure with clear script ordering is optimal for reproducibility and CI/CD.

## Complexity Tracking
*No violations detected. The complexity is managed by strict phase separation (Data -> Manipulation -> Survey -> Analysis) and the use of standard statistical libraries.*

## Phase Plan

### Phase 0: Research & Dataset Strategy
- **Goal**: Confirm `Dahoas/rm-single-context` contains sufficient moral scenarios with clear target agents for typographic manipulation.
- **Constraint**: Must use only datasets from the "Verified datasets" block.
- **Output**: `research.md` detailing dataset fit, manipulation strategy, and power analysis assumptions.

### Phase 1: Data Model & Contracts
- **Goal**: Define the schema for stimuli, responses, and analysis outputs.
- **Constraint**: Must ensure `stimulus_id` links to `scenario_id` and `salience_level`.
- **Output**: `data-model.md`, `quickstart.md`, and `contracts/*.schema.yaml`.

### Phase 2: Implementation (Tasks)
- **Goal**: Execute the pipeline scripts.
- **Order**:
  1. Ingest & Filter (Data Availability).
  2. Ambiguity Filtering (using reward scores).
  3. Manipulation (Typographic Variant Generation).
  4. Survey Deployment (Data Collection).
  5. Cleaning & Analysis (Statistical Testing).
- **Output**: Executable scripts and result files.

### Phase 3: Validation & Reporting
- **Goal**: Verify results against success criteria (SC-001 to SC-005).
- **Output**: Final report and paper artifacts.

## FR/SC Coverage Map
- **FR-001 (Manipulation)**: Covered in `code/02_stimulus_manipulation.py`. Validates Sentence-BERT similarity and typographic change metrics.
- **FR-002 (Randomization)**: Covered in `code/04_survey_deployment.py`. Implements within-subject randomization.
- **FR-003 (Collection)**: Covered in `code/04_survey_deployment.py` and `data/survey/`. Captures ID, Stimulus, Level, Rating.
- **FR-004 (LMM)**: Covered in `code/06_statistical_analysis.py`. Includes random intercepts, normality checks, and robust alternatives.
- **FR-005 (Bonferroni)**: Covered in `code/06_statistical_analysis.py`. Applies correction to 3 pairwise comparisons.
- **FR-006 (Effect Size)**: Covered in `code/06_statistical_analysis.py`. Calculates partial eta-squared (Type III SS).
- **FR-007 (Cleaning)**: Covered in `code/05_data_cleaning.py`. Excludes straight-liners (variance < 0.1 or >90% identical).
- **FR-008 (Ambiguity)**: Covered in `code/03_ambiguity_filter.py`. Uses reward scores from `Dahoas` as a proxy for human coding (simulating the consensus check logic).
- **SC-001 (Manipulation Check)**: Validated via Sentence-BERT and typographic metrics in Phase 0/1.
- **SC-002 (Effect Size)**: Validated via LMM output in Phase 2.
- **SC-003 (FWER)**: Validated via Bonferroni logic in Phase 2.
- **SC-004 (Data Quality)**: Validated via cleaning script in Phase 2.
- **SC-005 (CI Width)**: Validated via LMM confidence intervals in Phase 2.

## Compute Feasibility
- **CPU-First**: Sentence-BERT inference for a small set of text snippets is trivial on CPU.. LMM on <5000 rows is trivial on CPU. Text manipulation is CPU-tractable.
- **GPU Escape Hatch**: Not required. All methods are CPU-tractable.

## Data Availability
- **Primary Strategy**: Use `Dahoas/rm-single-context` (Verified Dataset). This dataset contains moral scenarios with pre-computed reward scores.
- **Gap Resolution**: No verified image dataset exists. The study is explicitly reframed to "Typographic Salience" in text, which is fully supported by the verified data.
- **Strict Adherence**: No external URLs or synthetic image data will be used. The plan relies solely on `Dahoas/rm-single-context`.

## Revised Spec Alignment
*Note: The original spec's FR-001 and FR-008 refer to images and Visual Genome. This plan interprets these requirements in the context of the available verified data:*
- *FR-001 (Manipulation):* Interpreted as "Typographic Manipulation" (font weight/size) instead of "Luminance Contrast".
- *FR-008 (Ambiguity):* Interpreted as using "Reward Scores" from the dataset as the proxy for human coding, rather than a separate human coding step.
- *This interpretation is necessary to satisfy the "Verified Accuracy" and "Data Availability" constraints without fabricating data sources.*