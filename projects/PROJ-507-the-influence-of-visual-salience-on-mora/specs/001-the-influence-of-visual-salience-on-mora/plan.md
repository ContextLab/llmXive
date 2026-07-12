# Implementation Plan: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Branch**: `001-visual-salience-moral-judgments` | **Date**: 2026-07-06 | **Spec**: `specs/001-visual-salience-moral-judgments/spec.md`
**Input**: Feature specification from `/specs/001-visual-salience-moral-judgments/spec.md`

## Summary

This project implements a computational psychology pipeline to investigate the causal effect of visual salience (manipulated via luminance contrast/brightness) on moral blame judgments. The system ingests real images from the verified Visual Genome dataset, programmatically generates stimulus variants with controlled salience levels, deploys a within-subject survey with a real pilot cohort, and performs repeated-measures ANOVA with rigorous multiple-comparison corrections. The implementation is strictly constrained to CPU-only execution on GitHub Actions free-tier runners (limited CPU, ~ GB RAM).

**Critical Methodological Note**: The pilot phase is a real empirical study, NOT a simulation. It uses real images from the Visual Genome dataset, real human coding to establish moral ambiguity (FR-008), and real behavioral data from a small recruited cohort. No placeholder images, synthetic labels, or deterministic rules are used to define the dependent variable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `Pillow`, `requests`, `pyyaml`, `seaborn`  
**Storage**: Local CSV/Parquet files (`data/`), JSON logs  
**Testing**: `pytest` (unit tests for data cleaning, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Entire pipeline (data prep + analysis) completes in < 6 hours on 2 vCPU.  
**Constraints**: No GPU; no deep learning models for inference (only lightweight PIL operations); dataset size limited to ensure < 7 GB RAM usage; statistical methods must be CPU-tractable.  
**Scale/Scope**: A set of real images (human-coded), A small cohort of pilot participants, < 1,000 total response records.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value. All statistical results (F-statistics, p-values, effect sizes) will be computed from the actual pilot data during the implementation phase; no fabricated or placeholder values are used in this plan.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Note |
|-----------|--------|------------------------|
| **I. Reproducibility** | **PASS** | Random seeds will be pinned in `code/`. External datasets will be fetched from canonical sources (Visual Genome) on every run. `requirements.txt` will pin all dependencies. |
| **II. Verified Accuracy** | **PASS** | All primary citations in `research.md` reference ONLY the verified visual dataset URLs provided in the spec. Secondary references (ANOVA/Text) are clearly distinguished and not used for core analysis. |
| **III. Data Hygiene** | **PASS** | Raw data will be checksummed. No in-place modifications; derivations will create new files with documented hashes. PII scan will be enforced. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated directly from `data/` via `code/` scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. The `state` YAML will be updated on artifact changes. |
| **VI. Stimulus-Control Integrity** | **PASS** | Visual manipulations will be performed programmatically with explicit, versioned parameters for contrast/brightness. Object detection (if used for validation) will be lightweight and CPU-optimized. |
| **VII. Behavioral Response Validation** | **PASS** | Metadata linking responses to specific stimulus versions will be enforced in the data schema. |

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
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_data_ingestion.py       # Ingests Visual Genome subset, filters metadata
│   ├── 02_human_coding.py         # Manages human coding protocol for ambiguity (FR-008)
│   ├── 03_stimulus_generation.py  # PIL-based luminance manipulation
│   ├── 04_survey_data_loader.py   # Loads survey CSV/JSON, validates structure
│   ├── 05_data_cleaning.py        # Filters straight-liners, handles missing data
│   ├── 06_statistical_analysis.py # Repeated-measures ANOVA, post-hoc tests
│   └── 07_report_generation.py    # Generates summary stats and plots
├── data/
│   ├── raw/                       # Downloaded source datasets (checksummed)
│   ├── processed/                 # Stimulus variants, cleaned response data
│   └── results/                   # ANOVA tables, plots
├── specs/001-visual-salience-moral-judgments/
└── tests/
    ├── unit/
    │   ├── test_stimulus_generation.py
    │   └── test_data_cleaning.py
    └── integration/
        └── test_pipeline_flow.py
```

**Structure Decision**: Single-project structure (`code/` scripts) chosen for simplicity and reproducibility in a research context. No separate frontend/backend; survey data is assumed to be exported as a structured file for analysis.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed without violations. | N/A |

## Implementation Phases & Requirement Mapping

### Phase 1: Data Ingestion, Human Coding & Stimulus Generation (FR-001, FR-008, SC-001)
- **Action**: Ingest images from the verified Visual Genome dataset (`https://homes.cs.washington.edu/~ranjay/visualgenome/data/dataset.json`). Filter by metadata (social/conflict tags) to narrow candidates.
- **Action**: **Execute mandatory human coding step** (FR-008). Recruit ≥2 independent annotators to label a pilot subset of images as 'morally ambiguous'. Exclude scenarios failing ≥80% inter-rater reliability (Cohen's κ ≥ 0.8). **The pilot IS this coding run.**
- **Action**: Generate low/medium/high salience variants using `Pillow` luminance adjustments (FR-001) ONLY on validated ambiguous scenarios.
- **Action**: Validate pixel-level changes (SC-001) and log failures (Edge Case: detection failure).
- **Output**: `data/processed/stimuli/` containing validated image variants.

### Phase 2: Survey Data Collection & Cleaning (FR-002, FR-003, FR-007, SC-004)
- **Action**: Deploy survey to a real pilot cohort (N=20-30) using the validated stimuli.
- **Action**: Collect blame ratings ensuring within-subject design (FR-002).
- **Action**: Implement data cleaning routine to flag/exclude straight-liners (FR-007).
- **Action**: Validate data structure (Participant ID, Image ID, Salience, Rating) (FR-003).
- **Output**: `data/processed/cleaned_responses.csv` with valid participant subset.

### Phase 3: Statistical Analysis (FR-004, FR-005, FR-006, SC-002, SC-003, SC-005)
- **Action**: Perform repeated-measures ANOVA (FR-004) on the real pilot data. Check Mauchly's test for sphericity.
- **Action**: Apply Greenhouse-Geisser/Huynh-Feldt corrections if needed.
- **Action**: Perform Bonferroni-corrected post-hoc pairwise comparisons (FR-005).
- **Action**: Calculate partial eta-squared and 95% CIs (FR-006, SC-002, SC-005).
- **Action**: Verify family-wise error rate control (SC-003).
- **Output**: `data/results/analysis_report.json` and plots. **All statistical values (F, p, η²) are computed from the real data; no placeholders are used.**

### Phase 4: Reporting & Validation (SC-001, SC-004)
- **Action**: Generate final report linking results back to `data/` and `code/`.
- **Action**: Verify reproducibility by re-running pipeline on fresh runner.

## Compute Feasibility Statement
The plan adheres strictly to CPU-only constraints.
- **Image Processing**: Uses `Pillow` (CPU-bound, low memory) for luminance adjustments. No deep learning inference for image generation.
- **Statistics**: Uses `statsmodels` and `scipy` (pure Python/C extensions) which are efficient on 2 vCPU.
- **Data Volume**: Dataset limited to < 1,000 rows and < 30 images to ensure < 7 GB RAM usage.
- **Runtime**: Estimated total runtime < 2 hours for typical pilot sizes, well within the 6-hour limit.

## Risks & Mitigations
- **Risk**: Visual Genome metadata may not perfectly align with "morally ambiguous" criteria.
  - **Mitigation**: The mandatory human coding step (FR-008) is the primary filter. The pilot size depends on the success rate of this step.
- **Risk**: Sample size may be insufficient for power.
  - **Mitigation**: Explicitly report power limitations and wider CIs as per FR-007 and Edge Cases.
- **Risk**: Sphericity violation in ANOVA.
  - **Mitigation**: Plan explicitly includes Mauchly's test and correction methods (FR-004).