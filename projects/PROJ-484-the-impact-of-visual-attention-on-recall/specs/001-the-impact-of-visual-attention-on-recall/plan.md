# Implementation Plan: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Branch**: `001-visual-attention-recall` | **Date**: 2026-07-11 | **Spec**: `specs/001-visual-attention-recall/spec.md`
**Input**: Feature specification from `specs/001-visual-attention-recall/spec.md`

## Summary

This feature implements a computational pipeline to investigate how trait anxiety modulates the relationship between gaze fixation duration on threat stimuli and subsequent recall accuracy in a Rapid Serial Visual Presentation (RSVP) task. The technical approach involves downloading an open RSVP dataset, preprocessing raw eye-tracking data using an I-VT velocity-threshold algorithm to extract fixation metrics, mapping stimulus IDs to emotional valence labels (threat/neutral) to generate a clean analysis-ready CSV file.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `statsmodels` (for mixed-effects GLM), `scikit-learn` (for preprocessing/splitting), `matplotlib`/`seaborn` (for visualization), `datasets` (Hugging Face for streaming), `requests` (for raw downloads).  
**Storage**: Local filesystem (`data/` for raw/processed, `artifacts/` for logs/plots).  
**Testing**: `pytest` (unit tests for preprocessing logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Research pipeline / Data analysis script.  
**Performance Goals**: Complete full pipeline (download, preprocess, model, plot) within 4 hours on 2-core CPU; memory usage < 7GB.  
**Constraints**: No GPU available on primary runner; no synthetic data generation; strict adherence to open data sources only.  
**Scale/Scope**: Moderate cohort (estimated a cohort of participants from open RSVP datasets); A substantial number of trials will be conducted.

> **Critical Feasibility Note**: The provided "Verified datasets" block indicates NO verified source for the RSVP dataset (OpenNeuro ds001435) or the IAPS/NimStim stimulus database. The STAI links provided are unrelated (image captions). **The plan below assumes a hypothetical verified substitute exists or that the "NO verified source" status is a temporary search failure and proceeds with the methodology, but explicitly flags this gap in the Research section.**

## Constitution Check

*Gates determined based on constitution file*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt` and random seeds. All data processing steps are scripted, not manual.
- **II. Verified Accuracy**: The plan strictly adheres to the "Verified datasets" block. Since RSVP and IAPS have NO verified sources, the plan explicitly notes this as a potential failure point and will not fabricate a URL. If the pipeline cannot locate a verified source, it will exit with a clear error.
- **III. Data Hygiene**: Raw data will be downloaded with checksums (if available) or preserved as-is. Derived files (cleaned CSV) will be written to new filenames. No PII handling is expected in open datasets, but a scan is included.
- **IV. Single Source of Truth**: Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper.
- **V. Versioning Discipline**: Artifacts will be hashed. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research-stage artifact change updates this project's `state/projects/PROJ-484-the-impact-of-visual-attention-on-recall.yaml` `updated_at` timestamp.
- **VI. Temporal-Load Experimental Fidelity**: The preprocessing step will verify stimulus presentation rates. **Logic**: The system will extract `stimulus_duration_ms` from metadata. If missing, it will attempt to infer duration from the known RSVP frame rate and sequence structure (e.g., `frames * (1000/fps)`). **Failure Condition**: If the only available metric is `ISI` (Inter-Stimulus Interval) and `ISI != duration`, the system will FAIL with "ERROR: Cannot verify Temporal-Load constraint; ISI does not equal stimulus duration." This prevents the logical error of assuming ISI = duration.
- **VII. Multi-Modal Data Independence Verification**: All analyses correlating gaze fixation duration with recall accuracy MUST treat eye-tracking data and behavioral recall responses as independently derived signals.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-attention-recall/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-484-the-impact-of-visual-attention-on-recall/
├── data/
│   ├── raw/             # Raw downloads (preserved)
│   └── processed/       # Cleaned CSVs, logs
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download_data.py
│   ├── preprocess.py
│   ├── model_fit.py
│   ├── visualize.py
│   └── run_pipeline.py  # Entry point
├── tests/
│   ├── test_preprocess.py
│   ├── test_model.py
│   └── test_integration.py
└── artifacts/
    ├── figures/
    └── logs/
```

**Structure Decision**: Single project structure chosen for simplicity and tight coupling of data processing and analysis. No separate frontend/backend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mixed-effects model (GLMM) | Required to handle crossed random effects (participant, stimulus) and test the 3-way interaction. | Fixed-effects models would ignore individual variability and stimulus-specific effects, inflating Type I error. |
| I-VT Algorithm | Standard for extracting fixations from raw gaze coordinates in RSVP. | Simple thresholding on velocity is insufficient for noisy eye-tracking data; I-VT is robust. |
| Streaming Data | **Defensive Pattern**: While a large number of trials (approximately a moderate amount of data) fit comfortably within available system memory, streaming is retained to ensure robustness against unexpected dataset bloat or future scale-up without OOM. | Loading full dataset is feasible now, but streaming ensures the pipeline remains valid if the dataset grows to >1M trials. |

## Phases & Tasks

### Phase 0: Data Verification & Geometry Calibration (NEW)

1.  **Task**: Search for verified RSVP datasets on OpenNeuro and other reputable sources.
2.  **Task**: **Variable Validation**: Parse the dataset manifest to verify the presence of ALL four required variables: Eye-tracking (x,y,timestamp), Valence, Recall, STAI. If any are missing, log specific missing fields and exit with `ERROR: Variable X missing`.
3.  **Task**: **Geometry Calibration**: Extract screen width (pixels), viewing distance (mm), and sampling rate (Hz) from metadata. Calculate the pixel-threshold for the I-VT algorithm:
    `threshold_pixels_per_frame = (deg/s) * (pixels_per_degree) / (sampling_rate_hz)`.
    *Note: `pixels_per_degree` is derived from screen width and viewing distance. If metadata is missing, the pipeline halts with "ERROR: Cannot calibrate I-VT threshold without screen geometry."*
4.  **Task**: **Temporal-Load Check**: Verify `stimulus_duration_ms` in metadata. If missing, attempt to infer from `frame_count * (1000/fps)`. **If only `ISI` is available and `ISI != duration`, fail.**
5.  **Output**: Log file indicating success/failure of data verification, variable presence, and geometry calibration.

### Phase 1: Data Preprocessing & Cleaning

1.  **Task**: Download raw RSVP dataset via `wget`.
2.  **Task**: Extract fixation duration using I-VT algorithm with the **calculated** pixel-threshold from Phase 0.
3.  **Task**: Map stimulus IDs to emotional valence (threat/neutral).
4.  **Task**: Merge participant STAI scores.
5.  **Task**: Filter invalid trials (missing data, excessive blinks).
6.  **Output**: Cleaned analysis-ready CSV file (`data/processed/analysis.csv`).

### Phase 2: Statistical Modeling & Analysis

1.  **Task**: Fit mixed-effects logistic regression model using `statsmodels`.
2.  **Task**: Perform Likelihood-Ratio Test (LRT).
3.  **Task**: Check model convergence and report diagnostics.
4.  **Alternative Hypothesis**: If power analysis shows insufficient sample size for the three-way interaction, focus on the two-way interaction between fixation duration and valence.
5.  **Output**: Model results JSON file (`artifacts/logs/model_results.json`).

### Phase 2.5: Power Analysis (NEW - Addresses SC-003)

1.  **Task**: Execute Monte Carlo simulation (A sufficient number of iterations will be performed to ensure convergence., alpha=0.05, target effect size f² ≥ 0.15) based on the observed sample size and variance components from the fitted model.
2.  **Task**: Calculate achieved power for the three-way interaction term.
3.  **Task**: Report power metric in `artifacts/logs/power_analysis.json`.
4.  **Output**: Power analysis report.

### Phase 3: Visualization & Reporting

1.  **Task**: Generate marginal effects plots showing the relationship between fixation duration and recall probability for high vs. low anxiety groups with confidence intervals.
2.  **If convergence fails (indicated by non-OK status in logs) or singularity is detected (variance components near zero), simplify random effects to a random intercept only, and evaluate model fit using AIC/BIC.**
3.  **Output**: PNG image of the marginal effects plot (`artifacts/figures/marginal_effects.png`).

