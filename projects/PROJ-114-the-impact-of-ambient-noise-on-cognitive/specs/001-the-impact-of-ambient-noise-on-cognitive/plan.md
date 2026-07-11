# Implementation Plan: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

**Branch**: `001-ambient-noise-cognitive-flexibility` | **Date**: 2026-07-11 | **Spec**: `specs/001-ambient-noise-cognitive-flexibility/spec.md`
**Input**: Feature specification from `/specs/001-ambient-noise-cognitive-flexibility/spec.md`

## Summary

This feature implements a **computational pipeline prototype** to investigate the non-linear ("inverted-U") relationship between ambient noise levels and cognitive flexibility. 
**Scope Clarification**: Due to the absence of a verified public dataset linking continuous ambient noise logs to specific task-switching performance metrics, this implementation focuses on **validating the statistical pipeline and data processing logic**. 
The system ingests raw decibel logs (currently synthetic for pipeline validation) and task-switching performance data (from a verified MTurk dataset), filters participants, normalizes reaction times, and fits linear mixed-effects models (LMM). 
The pipeline includes robustness checks via sensitivity analysis on noise thresholds. 
**Crucially**, any statistical findings regarding the "inverted-U" hypothesis generated in this phase are designated as **validation artifacts** (testing code robustness) and **not** as empirical scientific conclusions. The scientific hypothesis test is deferred until a real, linked dataset is acquired.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `pyyaml`, `snakemake`, `pytest`  
**Storage**: Local CSV/Parquet files within `data/` directory (raw, intermediate, processed)  
**Testing**: `pytest` with contract validation against YAML schemas in `contracts/` (specifically `contracts/analysis_dataset.schema.yaml` and `contracts/model_results.schema.yaml`).  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Research Pipeline Prototype  
**Performance Goals**: Complete analysis of N=150 participants within 6 hours on CPU-only runner. Memory usage < 6 GB.  
**Constraints**: No GPU acceleration; no heavy deep learning; all statistical methods must be CPU-tractable; strict adherence to data hygiene (checksums, immutable raw data).  
**Scale/Scope**: Single study (N=150), 3 noise categories, 1 primary LMM + sensitivity sweeps.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `code/` will pin all dependencies in `requirements.txt`. Random seeds (numpy, statsmodels) will be set globally. Workflow is deterministic. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be validated against the `# Verified datasets` block (MTurk CSV). No external URLs will be invented. |
| **III. Data Hygiene** | PASS | Raw data in `data/raw/` will be checksummed. Transformations will produce new files in `data/processed/`. PII scan will be enforced. |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` will be derived programmatically from `data/processed/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | **Enforced via `Snakefile` rule `hash_artifacts`**: After every successful run of `preprocess`, `models`, and `sensitivity`, the `Snakefile` computes SHA-256 hashes of the output files in `data/` and updates `state/projects/PROJ-114-.../state.yaml` with the new `artifact_hashes` map. |
| **VI. Environmental Context Fidelity** | PASS | Noise logs and task scores are treated as distinct artifacts. Aggregation logic ensures time-window independence from task execution. |
| **VII. Non-Linear Hypothesis Testing** | PASS | The plan explicitly includes a quadratic term in the LMM and a likelihood-ratio test to compare linear vs. quadratic models. **Note**: In this prototype phase, this tests the *pipeline's ability* to detect non-linearity, not the existence of the effect in the real world. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ambient-noise-cognitive-flexibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/
├── data/
│   ├── raw/             # Immutable raw data (checksummed)
│   ├── processed/       # Derived data (filtered, aggregated)
│   └── results/         # Model outputs, figures
├── code/
│   ├── __init__.py
│   ├── config.py        # Thresholds, paths, seeds
│   ├── preprocess.py    # FR-001 to FR-003
│   ├── models.py        # FR-004, FR-005, FR-008
│   ├── robustness.py    # FR-006, FR-007
│   └── main.py          # Helper script for local debugging (NOT primary entry)
├── tests/
│   ├── test_preprocess.py
│   ├── test_models.py
│   └── test_contracts.py
├── Snakefile            # PRIMARY WORKFLOW ORCHESTRATION ENTRY POINT
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The workflow is linear (Raw -> Process -> Model -> Report) and fits within a single Python package. **Snakemake (`Snakefile`) is the primary entry point** for both CI and local execution to enforce computational task ordering and reproducibility. `main.py` is a helper script used only for local debugging or as a specific Snakemake target, not the primary driver.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Mixed-Effects Models** | Required to handle within-subject variance and random intercepts for participants (FR-004). | Fixed-effects ANOVA would ignore the hierarchical structure of repeated measures per participant, violating statistical assumptions. |
| **Sensitivity Sweep** | Required to test robustness of thresholds (FR-006). | Single threshold analysis is fragile and fails to address calibration variance. |
| **Snakemake Workflow** | Ensures reproducible, ordered execution and automatic re-runs on data changes (Constitution I). | Manual script execution is error-prone and fails the "reproducibility" gate. |