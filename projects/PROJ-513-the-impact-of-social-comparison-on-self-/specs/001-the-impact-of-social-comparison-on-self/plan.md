# Implementation Plan: The Impact of Social Comparison on Self-Perception in AI-Generated Image Platforms

**Branch**: `001-synthetic-body-comparison` | **Date**: 2026-07-13 | **Spec**: `specs/001-synthetic-body-comparison/spec.md`
**Input**: Feature specification from `specs/001-synthetic-body-comparison/spec.md`

## Summary

This feature implements a controlled psychological experiment to test whether AI-generated idealized body images induce stronger negative body image self-perception (measured by BISS) than human-generated images. The approach involves a web-based data collection interface for randomized stimulus presentation, baseline covariate collection (INCOM, usage frequency), and a CPU-tractable Linear Mixed Effects (LME) statistical analysis pipeline. The system ensures strict adherence to the "Synthetic Body Comparison" within-subjects design, validates data completeness, and applies multiple-comparison corrections.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `statsmodels` (for LME), `numpy`, `scipy`, `pytest`  
**Storage**: Local CSV/JSON artifacts in `data/` (static assets and response logs)  
**Testing**: `pytest` (unit tests for data validation, integration tests for LME pipeline)  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, ~7GB RAM)  
**Project Type**: Research Data Collection & Analysis Pipeline  
**Performance Goals**: Analysis pipeline ≤ 3600 seconds; Memory ≤ 7GB; Data validation ≥ 95% completeness.  
**Constraints**: No GPU; No on-the-fly image generation; Pre-validated static stimuli only.  
**Scale/Scope**: Target N=150 participants; A set of stimuli per participant.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/analysis.py`; External datasets (stimuli) stored with immutable hashes in `data/stimuli/`. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to the primary literature (DOI) for BISS and INCOM instruments. No fabricated dataset URLs. |
| **III. Data Hygiene** | PASS | Raw data preserved; derivations (cleaned datasets) written to new files; PII stripped before commit. |
| **IV. Single Source of Truth** | PASS | `code/traceability.py` automatically extracts statistics from `data/analysis_results.json` and injects them into the paper template, preventing hand-typing. |
| **V. Versioning Discipline** | PASS | Content hashes tracked for all artifacts; `state/` updated on changes. |
| **VI. Experimental Stimulus Integrity** | PASS | Stimuli stored in `data/stimuli/` with hashes; Generation prompts recorded in `code/stimulus_generation.py` and `data/stimuli/metadata.json`. |
| **VII. Participant Anonymity** | PASS | No PII in `data/`; Participant IDs are anonymized tokens; raw survey responses stripped before analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-synthetic-body-comparison/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-513-the-impact-of-social-comparison-on-self-/
├── code/
│   ├── __init__.py
│   ├── analysis.py              # LME model fitting, correction, outlier handling
│   ├── data_validation.py       # FR-007, FR-008, FR-009 checks, CI gating
│   ├── stimulus_loader.py       # Loads pre-generated assets
│   ├── stimulus_generation.py   # Records generation prompts (Principle VI)
│   ├── traceability.py          # SSoT extraction for paper (Principle IV)
│   └── simulate_participant.py  # Mock data generation for testing
├── data/
│   ├── stimuli/                 # AI and Human images (static assets)
│   │   ├── ai/                  # a subset of images
│   │   ├── human/               # a set of images
│   │   └── metadata.json        # Match groups, pose, lighting info, generation prompts
│   ├── pretest/                 # Blind pre-test results (FR-009)
│   │   └── results.json         # Indistinguishability p-value
│   ├── raw/                     # Raw participant responses (anonymized)
│   ├── processed/               # Cleaned datasets for analysis
│   └── checksums.yaml           # Integrity hashes
├── tests/
│   ├── unit/
│   │   └── test_analysis.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to keep the analysis pipeline and data validation logic tightly coupled. The `data/` directory is split into `raw` (immutable) and `processed` (derived) to satisfy Data Hygiene. `code/` contains only analysis and validation scripts, as the data collection interface is assumed to be a separate frontend tool (or simulated for this research prototype) that outputs to the expected schema.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LME vs. ANOVA** | The design is within-subjects with nested covariates (Participant ID random intercept). ANOVA cannot handle missing data or unbalanced designs robustly. | ANOVA would require complete-case analysis, reducing power and violating FR-007 (missing data exclusion) by potentially discarding too much data. |
| **Random Slopes** | Participant-specific responses to AI vs. Human images may vary. | A random intercept-only model assumes a fixed effect across all participants, which may inflate Type I error if slopes vary. We include random slopes for Image Type. |
| **Pre-generated Assets** | FR-006 mandates no on-the-fly generation. | Real-time generation would exceed the computational time limit and require GPU, violating compute constraints. |

## Phases

### Phase 0: Pre-Test Validation (FR-009)
1.  **Action**: Run a blind pre-test with a small sample (N=30) to verify that AI and Human images are visually indistinguishable in quality (p > 0.05).
2.  **Output**: `data/pretest/results.json` containing the p-value.
3.  **Gate**: If p < 0.05, the study launch is blocked (FR-009).

### Phase 1: Data Collection & Simulation
1.  **Action**: Collect real participant data or run `simulate_participant.py` for testing.
2.  **Constraint**: Simulated data uses standard psychometric distributions for INCOM. and Usage Frequency, based on literature means, not external dataset URLs.

### Phase 2: Analysis & Validation
1.  **Action**: Run `data_validation.py` to check completeness (≥95%) and stimulus match (FR-008).
2.  **Gate**: If validation fails, the script exits with non-zero code, blocking CI.
3.  **Action**: Run `analysis.py` to fit LME with random slopes, center covariates, detect outliers, and apply Bonferroni correction.

### Phase 3: Traceability & Reporting
1.  **Action**: Run `traceability.py` to extract results into the paper template.
2.  **Output**: Final paper with statistics linked to `data/analysis_results.json`.

## FR/SC Coverage Map

| ID | Type | Plan Element |
| :--- | :--- | :--- |
| FR-001 | Req | Phase 1: Randomized sequence presentation (simulated). |
| FR-002 | Req | Phase 1: BISS collection per trial. |
| FR-003 | Req | Phase 1: INCOM/Usage collection. |
| FR-004 | Req | Phase 2: LME model in `analysis.py`. |
| FR-005 | Req | Phase 2: Bonferroni correction in `analysis.py`. |
| FR-006 | Req | Phase 2: CPU-only execution; static assets. |
| FR-007 | Req | Phase 2: Validation (≥95% completeness); partial data retained via LME. |
| FR-008 | Req | Phase 2: Metadata validation; CI gate blocks launch on failure. |
| FR-009 | Req | Phase 0: Blind pre-test execution; results stored in `data/pretest/`. |
| SC-001 | Metric | Phase 2: Hypothesis test (p < 0.05). |
| SC-002 | Metric | Phase 2: Effect size (eta-squared). |
| SC-003 | Metric | Phase 2: FWER control via Bonferroni. |
| SC-004 | Metric | Phase 2: Completion rate calculation (partial data included). |
| SC-005 | Metric | Phase 2: Runtime measurement (CI logs). |
| Edge: Outliers | Edge | Phase 2: Outlier detection and sensitivity analysis. |