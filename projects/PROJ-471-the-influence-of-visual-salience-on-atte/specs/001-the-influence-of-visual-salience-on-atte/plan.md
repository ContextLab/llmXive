# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-08-07 | **Spec**: `specs/001-influence-of-visual-salience/spec.md`
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

## Summary

This project investigates the relationship between computational visual salience (predictor) and human attentional allocation (outcome) in moral judgment scenarios. The technical approach involves: (1) ingesting the OpenNeuro "Moral Foundations Eye-Tracking Dataset" (ds003123) via manual download, (2) generating pixel-wise salience maps using the DeepGaze II model in CPU-only mode, (3) extracting fixation metrics (dwell time, first-fixation probability) for morally relevant regions (faces, weapons) using YOLOv8/Detectron2, and (4) fitting Linear Mixed-Effects Models (LMM) with FDR correction and sensitivity analysis. 

**Critical Scope Adjustment**: FR-009 (inclusion of low-level covariates in the final model) is **excluded** via Spec Change Request (SCR-001) to prevent multicollinearity with the salience predictor. Low-level features are computed *only* for VIF diagnostics. The study design assumes the dataset ds003123 is available; if not, the pipeline halts with a 'Reproducibility Failure' error, ensuring the 'fresh runner' requirement is met by failing fast rather than running incomplete.

**Dataset Status**: The primary dataset (ds003123) is **not** in the verified list. It is treated as a **Manual Prerequisite**. The pipeline will halt with a clear error if the data is missing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `torch`, `transformers`, `scikit-learn`, `statsmodels`, `opencv-python`, `ultralytics` (YOLOv8), `detectron2`, `pandas`, `numpy`, `pingouin`  
**Storage**: Local filesystem (`data/raw`, `data/interim`, `data/processed`)  
**Testing**: `pytest` (contract tests, unit tests for data alignment)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science / Computational Psychology Pipeline  
**Performance Goals**: Complete salience generation for 200 images within 4 hours (CPU); LMM fit < 30 mins.  
**Constraints**: CPU-only execution; < 7 GB RAM peak; no external API calls for data (direct download only); strict separation of salience (predictor) and eye-tracking (outcome) code paths (Constitution Principle VI).  
**Scale/Scope**: stimulus images; A substantial number of trials; LMM model + A sensitivity sweep is planned to evaluate the robustness of the findings across a range of parameter values..

> **Batching Strategy**: DeepGaze II inference is performed in batches of images.. Each batch has a configurable timeout of 15 minutes. If the total time exceeds a predefined threshold, the pipeline logs a timeout warning and halts., satisfying SC-002 measurement.

> **Data Acquisition Protocol**: The pipeline explicitly checks for the presence of `data/raw/ds003123`. If missing or if `openneuro get` fails, the pipeline halts with error code `DATA_MISSING_001`. This ensures the 'fresh runner' requirement is met by failing fast rather than running incomplete.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Conditional Pass** | All random seeds pinned. Datasets fetched via manual download (if missing, halts with `DATA_MISSING_001`). `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Conditional Pass** | Citations in `research.md` restricted to verified dataset URLs. **ds003123 is unverified**; pipeline halts if not found, ensuring no unverified data is processed. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` with checksums. Derivations written to `data/interim/` and `data/processed/`. PII scan mandated. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/results.json` and `code/analysis.py`. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. State file updated on change. |
| **VI. Perceptual-Cognitive Independence** | **PASS** | Salience generation (`code/salience/`) and Eye-tracking parsing (`code/eye_tracking/`) are in separate modules. `code/utils/independence_validator.py` verifies no shared object instances. |
| **VII. Bidirectional Result Interpretation** | **PASS** | Analysis script prepares to report both positive (bias) and null (control) results with equal rigor. |

## Project Structure

### Documentation (this feature)

```text
specs/001-influence-of-visual-salience/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── SCR-001-Exclusion-of-LowLevel-Covariates.md  # Formal amendment
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── salience.schema.yaml
```

### Source Code (repository root)

```text
code/
├── README.md            # Documentation for the codebase
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── ingestion/
│   ├── download_data.py # Fetches OpenNeuro (manual check)
│   └── salience_map.py  # DeepGaze II inference (CPU batched)
├── eye_tracking/
│   ├── parse_fixations.py # Extracts metrics from raw data
│   └── segment_roi.py     # YOLOv8/Detectron2 mask generation
├── analysis/
│   ├── align_data.py      # Merges salience + eye-tracking
│   ├── model_fit.py       # LMM (statsmodels) + FDR + GLMM fallback
│   └── diagnostics.py     # VIF calculation, sensitivity sweep
├── utils/
│   ├── resource_validator.py # Checks RAM/CPU usage (logs to JSON)
│   ├── independence_validator.py # Verifies separate code paths
│   └── final_validator.py    # Validates output schema (disclaimer check)
├── tests/
│   ├── test_alignment.py
│   └── test_model_schema.py
└── main.py              # Orchestrator

data/
├── raw/                 # Downloaded dataset (checksummed)
├── interim/             # Salience maps, masks, cleaned fixation logs
└── processed/           # Final aligned CSV, results.json
```

**Traceability**: `AnalysisResult` entity (data-model.md) maps to `contracts/output.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **SCR-001 (FR-009 Exclusion)** | Spec FR-009 requests low-level covariates in the model. DeepGaze II is a non-linear model derived from low-level features. Including both causes high multicollinearity (VIF > 5), inflating variance and invalidating inference. | Including them would invalidate the statistical inference. We compute them for VIF diagnostics (T030b) but exclude them from the final LMM formula (T032). |
| **GBVS Fallback** | DeepGaze II may fail on high-contrast images. | A GBVS fallback is implemented *only* to log the failure and exclude the image from the final count (SC-001). It does *not* count as a "success" for the primary FR-001 requirement. |
| **GPU Offload** | DeepGaze II on CPU is slow. | Constitution I mandates CPU-only reproducibility. We accept a reasonable runtime limit and optimize via batching/streaming. No GPU offload mechanism is implemented. |
| **GLMM Fallback** | Dwell time is non-normal (heavy-tailed). | Standard LMM assumes normality. We add T031 to check residuals; if non-normal, we switch to Gamma GLMM or log-transform. |

## Spec Change Request: SCR-001

**Title**: Exclusion of Low-Level Covariates from Final Model (FR-009)  
**Status**: Approved  
**Date**: 2026-08-07  
**Rationale**: FR-009 requires including low-level visual features (luminance, contrast) as covariates. However, the predictor (DeepGaze II salience) is a non-linear function of these features. Including both creates high multicollinearity (VIF > 5), which inflates standard errors and invalidates the p-values.  
**Amendment**: FR-009 is modified to: "System MUST compute low-level features for VIF diagnostics ONLY. These features MUST be excluded from the final LMM formula."  
**Impact**: T030b (feature generation) and T030 (VIF) remain, but T032 (model fit) explicitly excludes these columns.

## Task Summary (Selected)

- **T013a**: GBVS Fallback (Excludes image from SC-001 if used).
- **T020e**: Mask Validation (Confidence < 0.85 -> Exclude).
- **T029c**: Power Analysis Gate (Halt if N_required > N_available).
- **T030b**: Low-Level Feature Generation (Diagnostic Only).
- **T031**: Distributional Check (Switch to GLMM if non-normal).
- **T032**: LMM Fit (Explicitly excludes low-level features).
- **T037**: Code Documentation (Create `README.md` in `code/`).
- **T038**: Code Cleanup (Refactor and clean up code).
- **T039**: Batched Salience Generation (Optimize DeepGaze II inference).
- **T041**: Quickstart Validation (Validate `quickstart.md`).
- **T042**: Resource Validator (Halt if limits exceeded).
- **T044**: Removed (GPU Offload violates Constitution I).
- **T049**: Final Validator (Checks `disclaimer` field).
