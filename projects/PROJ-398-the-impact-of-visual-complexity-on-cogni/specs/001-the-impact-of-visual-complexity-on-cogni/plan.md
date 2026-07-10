# Implementation Plan: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Branch**: `001-visual-complexity-cognitive-load` | **Date**: 2026-06-25 | **Spec**: `specs/001-the-impact-of-visual-complexity-on-cogni/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-visual-complexity-on-cogni/spec.md`

## Summary

This project implements a computational and experimental pipeline to investigate the relationship between visual complexity in remote meeting backgrounds and cognitive load. The implementation is strictly divided into two distinct, mutually exclusive tracks to prevent the conflation of code validation with scientific hypothesis testing:

1.  **Pipeline Validation Track (Synthetic/Logic Check)**:
    *   **Purpose**: To verify that the code logic (metric extraction, LMM fitting, VIF calculation, FWER correction) runs correctly on CPU-only hardware and that the statistical pipeline handles data structures as expected.
    *   **Data Source**: Procedurally generated images (for metric extraction speed tests) and **simulated statistical residuals** (for LMM logic checks).
    *   **Constraint**: **NO scientific claims** regarding cognitive load, complexity, or human perception are derived from this track. Results here are strictly "Code Validation" reports.
    *   **Output Label**: Any report generated from this track MUST be explicitly labeled **"VALIDATION ONLY - NOT SCIENTIFIC"**. It will contain no p-values for hypothesis testing, only diagnostic metrics (e.g., "LMM fitted successfully", "VIF calculated", "Code execution time < 30s").
    *   **Null Simulation**: A specific sub-task where effect sizes are forced to zero to verify the Family-Wise Error Rate (FWER) control logic (FR-007). This is a logic check to ensure the code correctly returns non-significant results when the true effect is zero. It does **not** generate findings about complexity.

2.  **Scientific Validation Track (Real Human Data)**:
    *   **Purpose**: To test the research hypotheses (H1-H3) regarding the impact of visual complexity on cognitive load.
    *   **Data Source**: **Real human participants** (Pilot n=20 for metric validation; Main Study n=50-100 for hypothesis testing) and **real meeting background images** (or verified synthetic stimuli if real images are unavailable, but with human ratings).
    *   **Constraint**: The analysis pipeline **MUST** ingest real human ratings for the NASA-TLX and reaction-time tasks. **Synthetic cognitive load scores are PROHIBITED for the Scientific Track.**
    *   **Data Validity Gate**: The system implements a hard gate. If the input data for the Scientific Track is flagged as `source: synthetic` (for cognitive load metrics), the analysis script will **refuse to generate a scientific report** and will output an error or a "BLOCKED" status. No scientific conclusions will be generated.

The implementation strictly adheres to CPU-only constraints (2 cores, 7GB RAM) and prioritizes reproducibility and data hygiene as mandated by the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `opencv-python-headless`, `ultralytics` (CPU-only wheel), `numpy`, `pandas`, `pillow`, `pytest`  
**Storage**: Local file system (`data/stimuli/`, `data/measurements/`, `data/derived/`)  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for analysis pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM, no GPU)  
**Project Type**: Data Science / Experimental Psychology Pipeline  
**Performance Goals**: Process 10 images (1080p) in <30s; Total analysis runtime <6h.  
**Constraints**: No GPU/CUDA; No deep learning training (inference only); No PII in data; Strict reproducibility (random seeds pinned).  
**Scale/Scope**: Pilot (n=20 human ratings); Main Study (real data collection interface design; synthetic data used ONLY for code logic verification and power analysis).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All scripts will pin random seeds (`numpy`, `random`, `torch` if used for inference). Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **LIMITED** | **Code:** PASS (algorithms verified). **Data:** LIMITATION (Synthetic stimuli used for pipeline validation only; real data required for scientific claims). The plan explicitly states that synthetic data cannot satisfy the 'Verified Accuracy' standard for the final scientific conclusion. |
| **III. Data Hygiene** | **PASS** | Raw data (images, raw logs) preserved in `data/stimuli` and `data/measurements`. Derivations written to `data/derived` with checksums recorded in state YAML. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated programmatically from `data/derived` via `code/` scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. State file `updated_at` will be updated on artifact changes. |
| **VI. Stimulus Standardization** | **PASS** | Metadata for `data/stimuli/` will include computed entropy, variance, and object counts. |
| **VII. Psychometric Data Integrity** | **PASS** | NASA-TLX and RT data stored in raw form. Preprocessing scripted in `code/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-the-impact-of-visual-complexity-on-cogni/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── background_frame.schema.yaml
    ├── human_rating.schema.yaml
    ├── metrics.schema.yaml
    ├── participant_session.schema.yaml
    ├── participant_sessions.schema.yaml
    ├── analysis_result.schema.yaml
    └── analysis_results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration, paths, seeds
├── metrics/
│   ├── __init__.py
│   ├── extraction.py    # Entropy, variance, object detection (YOLOv8n CPU)
│   └── pilot_validation.py # Correlation with human ratings
├── analysis/
│   ├── __init__.py
│   ├── preprocessing.py # Cleaning, counterbalancing logic
│   ├── models.py        # LMM fitting, VIF calculation, FWER correction
│   └── sensitivity.py   # Alpha sweep analysis
├── experiments/
│   ├── __init__.py
│   ├── stimuli_loader.py
│   └── pilot_runner.py  # Interface logic for human ratings (simulated for now)
└── main.py              # Orchestration script

tests/
├── __init__.py
├── test_metrics.py
├── test_analysis.py
└── test_contracts.py    # Validates data against YAML schemas

data/
├── stimuli/             # Raw background images
├── measurements/        # Raw human ratings, RT logs
└── derived/             # Processed datasets, model outputs

requirements.txt
```

**Structure Decision**: Single `code/` directory with modular sub-packages. This minimizes overhead and ensures all processing happens in a single, reproducible environment suitable for CPU-only execution. No separate frontend/backend is implemented in this phase; the "experiment" is simulated via scripts for the pilot and analysis validation, with the understanding that a web interface would be a future feature (not in scope for this computational pipeline).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Linear Mixed-Effects Models** | Required by FR-003 to handle nested data (trials within participants) and control for participant ID. | Simple linear regression (OLS) would violate statistical assumptions by ignoring the non-independence of repeated measures from the same participant, leading to inflated Type I error rates. |
| **VIF & FWER Correction** | Required by FR-003 and FR-004 to ensure statistical rigor (multicollinearity, multiple comparisons). | Ignoring these would risk spurious findings (false positives) and misinterpretation of predictor effects, violating the "Verified Accuracy" and "Reproducibility" principles. |
| **Sensitivity Analysis (Alpha Sweep)** | Required by FR-005 (referencing `analysis_result.schema.yaml`) to demonstrate robustness of findings. | A single p-value threshold (e.g., 0.05) provides a fragile view of significance; sweeping thresholds confirms if results are stable or artifacts of arbitrary cutoffs. |
| **Pilot Correlation (FR-006)** | Required to validate automated metrics against human perception (US-0). | Automated metrics are unproven proxies; without human validation, the study lacks construct validity. |
| **Null Simulation (FR-007)** | Required to verify Family-Wise Error Rate control (US-3). | Without null simulation, the Type I error rate is unverified, risking false positives in the main analysis. |

## Phase Definitions

1.  **Phase 1 (Design)**: Generation of documentation (`plan.md`, `data-model.md`, `contracts/`, `quickstart.md`) and definition of data schemas.
2.  **Phase 2 (Pipeline Execution - Logic Check)**: Running the code to generate synthetic stimuli, extract metrics, and run LMMs on **synthetic/placeholder data** to verify:
    *   Code runs without error on CPU.
    *   LMM fitting works.
    *   VIF and FWER calculations produce valid numbers.
    *   **Crucially**: This phase produces "Code Validation" reports. **No scientific findings** are generated. The output will be explicitly labeled "VALIDATION ONLY".
3.  **Phase 3 (Scientific Execution)**: Collection of real human data (Pilot n=20, Main Study n=50-100) and real meeting backgrounds. Re-running the pipeline with **real data** to produce scientific findings. **This phase is blocked until real data is available and flagged as `source: real`.**

## Data Validity Gate

The system implements a hard gate before generating any scientific report:
- **Input Check**: The `data/measurements/` directory must contain files flagged as `source: real` (e.g., `pilot_ratings_real.csv`).
- **Validation**: If the input data for cognitive load (NASA-TLX, RT) is flagged as `source: synthetic`, the analysis script will run but the final report will be marked **"VALIDATION ONLY - NOT SCIENTIFIC"** and will contain **no** hypothesis test results (no p-values for H1-H3).
- **Blocking**: Final publication of results is blocked until the `source: real` flag is present and the pilot correlation (r > 0.5) is met with real human ratings.
- **Null Simulation Exception**: The "Null Simulation" (FR-007) is a specific logic check where the effect size is forced to zero to verify FWER control. This is **not** a hypothesis test and does not generate scientific findings about complexity. It verifies that the code correctly reports non-significance when the true effect is zero.

## Statistical Rigor & Methodological Notes

- **No Fabricated Results**: The plan explicitly forbids the use of simulated cognitive load data (NASA-TLX, reaction time) for hypothesis testing. Any analysis run on such data is for **code logic verification only** and must be clearly labeled as such.
- **Dataset Variable Fit**: The plan acknowledges that if a required variable (e.g., post-task anxiety) is missing from a dataset, the analysis cannot proceed for that variable. No imputation or synthetic generation will be used to fill this gap for the scientific track.
- **Statistical Rigor**: The plan addresses multiple-comparison correction, power justification (via G*Power prior to collection), and causal inference assumptions (observational, associational claims only).
- **Compute Feasibility**: All methods are CPU-tractable. YOLOv8n is used for inference only, not training. Data is subset to fit RAM constraints.