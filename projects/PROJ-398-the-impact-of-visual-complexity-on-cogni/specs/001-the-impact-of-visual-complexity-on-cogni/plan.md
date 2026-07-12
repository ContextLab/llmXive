# Implementation Plan: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Branch**: `001-visual-complexity-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-visual-complexity-cognitive-load/spec.md`
**Input**: Feature specification from `specs/001-visual-complexity-cognitive-load/spec.md`

## Summary

This plan implements a computational psychology study to quantify the relationship between visual background complexity in video meetings and cognitive load. The approach involves: (1) validating automated visual metrics (entropy, variance, object count) against human pilot ratings; (2) processing a dataset of meeting backgrounds to extract these metrics; (3) administering a web-based study where participants view clips and complete NASA-TLX and reaction-time tasks; and (4) performing linear mixed-effects modeling with rigorous statistical controls (VIF, multiple-comparison correction, sensitivity analysis). The implementation strictly adheres to CPU-only constraints for CI compatibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `opencv-python-headless`, `ultralytics` (YOLOv8n CPU-compatible), `streamlit` (for study interface), `pytest`  
**Storage**: Local files (`data/stimuli/`, `data/measurements/`), JSON/Parquet intermediate formats  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM, No GPU)  
**Project Type**: Computational Research Pipeline / Web Experiment  
**Performance Goals**: Process 10 images (1080p) in <30s; Total runtime <6h  
**Constraints**: No GPU usage; No large-LLM inference; Data must fit in ~GB RAM; No hardcoded/fabricated results.  
**Scale/Scope**: N=100 participants (main study), 50 stimuli images, 10 trials/participant.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail (Evidence) |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Seeds pinned in `code/config.py`; `requirements.txt` pinned; external data fetched via canonical loaders in `code/utils/data_hygiene.py`. |
| **II. Verified Accuracy** | ✅ Pass | All citations in `research.md` restricted to the "Verified datasets" block; no fabricated URLs. |
| **III. Data Hygiene** | ✅ Pass | Raw data in `data/raw/` with checksums recorded in `state/PROJ-398...yaml` `artifact_hashes`; derived data in `data/processed/` with provenance logs in `code/utils/data_hygiene.py`. |
| **IV. Single Source of Truth** | ✅ Pass | All stats in `paper/` generated via scripts reading `data/processed/`; no manual entry. |
| **V. Versioning Discipline** | ✅ Pass | Artifact hashes tracked in `state/`; version bump on `constitution.md` change. |
| **VI. Stimulus Standardization** | ✅ Pass | All stimuli in `data/stimuli/` with metadata JSON containing entropy/variance/object count, validated against `contracts/stimuli_metadata.schema.yaml`. |
| **VII. Psychometric Data Integrity** | ✅ Pass | NASA-TLX and RT data stored raw in `data/measurements/`; preprocessing scripted in `code/analysis/models.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-complexity-cognitive-load/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── analysis_result.schema.yaml
    ├── analysis_results.schema.yaml
    ├── background_frame.schema.yaml
    ├── human_rating.schema.yaml
    ├── metrics.schema.yaml
    ├── participant_data.schema.yaml
    ├── participant_measurements.schema.yaml
    ├── participant_session.schema.yaml
    ├── participant_sessions.schema.yaml
    ├── stimuli_metadata.schema.yaml
    ├── stimuli_metrics.schema.yaml
    └── stimulus.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-398-the-impact-of-visual-complexity-on-cogni/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py           # Paths, seeds, hyperparameters
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── extract_visual.py  # FR-001: Entropy, Variance, YOLOv8n
│   │   └── validate_pilot.py  # FR-006: Human vs Auto correlation
│   ├── study/
│   │   ├── __init__.py
│   │   ├── app.py            # Streamlit interface for US-2
│   │   └── stimuli_loader.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── models.py         # FR-003: LMM, VIF, LME
│   │   ├── corrections.py    # FR-004: Benjamini-Hochberg
│   │   └── sensitivity.py    # FR-005: Alpha sweep
│   └── utils/
│       ├── data_hygiene.py   # Checksums, PII scan
│       └── synthetic_data.py # FR-007: Null simulation (Pipeline Validation Only)
├── data/
│   ├── raw/                  # Downloaded stimuli, raw participant logs
│   ├── processed/            # Feature extracted, aggregated stats
│   └── stimuli/              # Background images + metadata
├── tests/
│   ├── contract/             # Schema validation
│   ├── integration/          # End-to-end pipeline
│   └── unit/                 # Metric logic
└── paper/                    # Generated figures and draft text
```

**Structure Decision**: Single-project structure selected to minimize overhead. The `code/` directory contains all logic for metric extraction, study administration (Streamlit), and statistical analysis. `data/` is strictly separated into raw and processed to enforce Data Hygiene (Principle III).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Linear Mixed-Effects Models (LMM)** | Required by FR-003 to handle repeated measures (multiple clips per participant) and random intercepts for participant ID. | Fixed-effects ANOVA would violate statistical assumptions by ignoring within-subject correlation, inflating Type I error. |
| **Benjamini-Hochberg Correction** | Required by FR-004 to control False Discovery Rate across multiple predictors (entropy, variance, object count). | Standard Bonferroni is too conservative for exploratory psychological metrics, risking Type II errors. |
| **YOLOv8n (Nano)** | Required by FR-001 for object detection within NFR-001 (CPU, <30s for 10 images). Enforced by `contracts/background_frame.schema.yaml` and `BackgroundFrame` entity. | Heavier models (YOLOv8m/l) exceed CPU time/RAM limits; no detection model would miss the "object count" variable. |
| **Sensitivity Analysis Sweep** | Required by FR-005/FR-005b to demonstrate robustness of findings across alpha thresholds. | Single-threshold reporting is insufficient for rigorous psychological research and fails the "stability" metric. |
| **Balanced Block Randomization** | Required to handle 50 stimuli with 100 participants without infeasible Latin Square permutations. | Latin Square for 50 conditions requires 50 distinct sequences, which is impractical for N=100. |

## FR/SC Coverage Map

| ID | Type | Plan Phase/Step |
| :--- | :--- | :--- |
| FR-001 | Metric Extraction | `code/metrics/extract_visual.py` (Phase 2) |
| FR-002 | Administer Assessment | `code/study/app.py` (Phase 3) |
| FR-002b | Baseline RT | `code/study/app.py` (Phase 3, Baseline Condition) |
| FR-002c | Counterbalancing | `code/study/stimuli_loader.py` (Balanced Block Randomization) |
| FR-003 | LMM & VIF | `code/analysis/models.py` (Phase 4) |
| FR-004 | Multiple Comparison | `code/analysis/corrections.py` (Phase 4) |
| FR-005 | Sensitivity Analysis | `code/analysis/sensitivity.py` (Phase 4) |
| FR-005b | Stability Metric | `code/analysis/sensitivity.py` (SD of effect sizes) |
| FR-006 | Pilot Validation | `code/metrics/validate_pilot.py` (Phase 1) |
| FR-007 | Null Simulation | `code/utils/synthetic_data.py` (Pipeline Validation Only) |
| SC-001 | Metric Validation | Phase 1 (Pilot Correlation r > 0.5) |
| SC-002 | Significance Flag | Phase 4 (Adjusted p < 0.05) |
| SC-003 | RT Baseline Diff | Phase 4 (RT - Baseline RT) |
| SC-004 | FWER Control | Phase 4 (Null Sim FWER ≈ 0.05) |
| SC-005 | Stability | Phase 4 (SD of effect sizes) |
