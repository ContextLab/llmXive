# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-10-17 | **Spec**: `specs/001-influence-of-visual-salience/spec.md`  
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

## Summary
The pipeline builds a reproducible end‑to‑end analysis that (1) verifies the presence of the OpenNeuro Moral Foundations Eye‑Tracking dataset (manual placement required; no automated download), (2) computes CPU‑friendly pixel‑wise salience maps for every stimulus image using the GBVS algorithm with explicit error handling, (3) applies an optional GPU fallback (DeepGaze II) only for images where GBVS fails, (4) creates semantic ROI masks for faces and weapons via YOLOv8 and Detectron2, (5) extracts fixation metrics (first‑fixation probability, dwell time, fixation latency) from the raw eye‑tracking logs, (6) aligns salience scores with fixation metrics per trial, (7) adds low‑level visual covariates (luminance, contrast, edge density) and semantic covariates (moral valence, scene complexity), (8) reduces collinearity via PCA orthogonalization of visual features, (9) fits linear mixed‑effects models with FDR correction and a sensitivity analysis, and (10) validates all outputs against JSON/YAML contracts while enforcing the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets>=2.18.0`  
  - `torch==2.2.0` (CPU‑only; GPU optional for DeepGaze II)  
  - `torchvision`  
  - `statsmodels>=0.14.0`  
  - `opencv-python>=4.8.0`  
  - `ultralytics>=8.0.0` (YOLOv8)  
  - `detectron2>=0.7`  
  - `pandas>=2.2.0`  
  - `numpy>=1.26.0`  
  - `scikit-image>=0.22.0` (for GBVS implementation via `pySaliencyMap`)  
  - `scikit-learn>=1.3.0` (PCA for collinearity reduction)  
  - `pingouin>=0.5.4` (VIF, power simulation)  
  - `vaderSentiment>=3.3.2` (optional; for moral valence extraction if captions available)  
- **Storage**: Local filesystem under `data/` (raw, interim, processed).  
- **Testing**: `pytest` with contract tests (`tests/contract/`).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h). CPU‑first; DeepGaze II runs only if `torch.cuda.is_available()` (GPU escape hatch).  
- **Constraints**:  
  - All predictor (salience) and outcome (eye‑tracking) code paths are isolated (Constitution Principle VI).  
  - Manual dataset placement required (verified‑datasets rule); no automated download.  
- **Scale/Scope**: a set of stimulus images; expected a substantial number of eye-tracking trials; A sufficient sample size will be determined through power analysis to ensure adequate statistical power for detecting effects of interest..

## Constitution Check
| Principle | Status | Action |
|---|---|---|
| I. Reproducibility | **PASS** | Random seeds are pinned in `code/config.py`; dataset path is fixed. |
| II. Verified Accuracy | **PASS** | All external model weights are fetched from verified HuggingFace URLs (DeepGaze II, YOLOv8, Detectron2). |
| III. Data Hygiene | **PASS** | Raw data never altered; every transformation writes a new file with checksum recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | **PASS** | Every figure/table traces to rows in `data/processed/aligned_data.csv` and entries in `data/processed/results.json`. |
| V. Versioning Discipline | **PASS** | Content hashes recorded; timestamps updated on change. |
| VI. Perceptual‑Cognitive Independence | **PASS** | Salience generation (`code/salience/`) and eye‑tracking extraction (`code/eye_tracking/`) live in separate modules; `independence_validator.py` asserts no shared objects. |
| VII. Bidirectional Result Interpretation | **PASS** | Scripts output both positive and null interpretations equally; disclaimer added to all results. |

## Project Structure
```text
specs/001-influence-of-visual-salience/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── salience.schema.yaml
└── SCR-001-Exclusion-of-LowLevel-Covariates.md

code/
├── __init__.py
├── config.py                # seeds, thresholds, batch sizes, device selection
├── ingestion/
│   └── verify_data.py       # checks ds003123 presence; no download attempted
├── salience/
│   ├── generate_maps.py     # GBVS primary (CPU), with error handling
│   └── deepgaze_fallback.py # DeepGaze II GPU fallback (optional, Kaggle only)
├── eye_tracking/
│   ├── parse_fixations.py   # extracts dwell, first‑fixation, latency
│   └── segment_roi.py       # YOLOv8 (faces) + Detectron2 (weapons) ensemble
├── analysis/
│   ├── align_data.py        # merges salience, fixations, semantic covariates
│   ├── orthogonalize.py     # PCA orthogonalization of visual features
│   ├── model_fit.py         # LMM, FDR, disclaimer insertion
│   └── diagnostics.py       # VIF (pre/post), power simulation, sensitivity analysis
├── utils/
│   ├── resource_validator.py
│   ├── independence_validator.py
│   └── final_validator.py   # schema validation + disclaimer enforcement
└── main.py                  # orchestrator that runs the pipeline step‑by‑step

data/
├── raw/                     # manual placement of ds003123 (OpenNeuro)
├── interim/
│   ├── salience_maps/
│   ├── salience_metadata.json
│   ├── masks/
│   └── fixations.csv
└── processed/
    ├── aligned_data.csv
    └── results.json
```

## Phase Overview & Mapping to FR/SC

| Phase | Core Tasks | FR(s) Covered | SC(s) Covered | Deterministic Artifact |
|------|------------|---------------|---------------|------------------------|
| **0 – Verify Dataset** | `code/ingestion/verify_data.py` checks presence of `data/raw/ds003123/` and records checksum. No download attempted. | — | SC‑001 (proportion of successful maps), SC‑005 (alignment proportion) | `state/projects/...yaml` checksum entry |
| **1a – Salience Map Generation (CPU Primary)** | `code/salience/generate_maps.py` runs GBVS on CPU for all 200 images; writes `.npy` + metadata JSON per image. Explicit error handling: high-contrast images logged as fallback_needed. | FR‑001, FR‑009 (low‑level covariates derived from same images) | SC‑001, SC‑002 | `data/interim/salience_maps/<stimulus_id>.npy` + `salience_metadata.json` |
| **1b – Salience Map Generation (GPU Fallback, Optional)** | `code/salience/deepgaze_fallback.py` runs ONLY if (a) CUDA available AND (b) images marked fallback_needed exist. Processes failed images on Kaggle GPU; updates metadata. | FR‑001 (fallback for failed images) | SC‑001 (completion rate) | Updated `salience_metadata.json` with fallback_used=True entries |
| **2 – ROI Mask Creation** | `code/eye_tracking/segment_roi.py` runs YOLOv8 for faces and Detectron2 for weapons; stores binary masks (`.png`). | FR‑008 | — | `data/interim/masks/<stimulus_id>_face.png` etc. |
| **3 – Eye‑Tracking Metric Extraction** | `code/eye_tracking/parse_fixations.py` parses raw logs, computes dwell, first‑fixation prob, fixation latency; outputs `fixations.csv`. | FR‑002 | — | `data/interim/fixations.csv` |
| **4 – Alignment & Feature Augmentation** | `code/analysis/align_data.py` merges salience scores, ROI masks, fixation metrics, low‑level visual features (luminance, contrast, edge density), and semantic covariates (moral valence, scene complexity) → `aligned_data.csv`. | FR‑003, FR‑009 | SC‑005, SC‑006 (VIF pre-orthogonalization) | `data/processed/aligned_data.csv` |
| **5 – Collinearity Reduction** | `code/analysis/orthogonalize.py` computes VIF for all predictors; if any VIF > 5, applies PCA to orthogonalize luminance, contrast, edge_density; reports pre/post VIF in diagnostics.log. | FR‑009 (refined covariate handling) | SC‑006 (post-orthogonalization VIF) | `logs/diagnostics.log` with VIF summary |
| **6 – Statistical Modeling** | `code/analysis/model_fit.py` fits Model A (random intercepts) and Model B (random slopes) using orthogonalized features; applies Benjamini‑Hochberg FDR; writes `results.json`. | FR‑004, FR‑005, FR‑006, FR‑007 | SC‑003 (power check), SC‑004 (stability), SC‑006 (post-orthogonalization VIF) | `data/processed/results.json` |
| **7 – Validation & Contracts** | `code/utils/final_validator.py` validates `aligned_data.csv` against `dataset.schema.yaml`, `results.json` against `output.schema.yaml`, and `salience_metadata.json` against `salience.schema.yaml`; ensures disclaimer present. | FR‑007 | — | Pass/fail log; artifacts unchanged |
| **8 – Resource & Power Guardrails** | `code/utils/resource_validator.py` monitors RAM/CPU usage; aborts if >7 GB or >6 h; `diagnostics.py` runs simulation‑based power analysis (500 reps, n_participants=50, trials_per_participant=100, f=0.15). | — | SC‑002, SC‑003 | Log file `logs/resource.log` + power report in `results.json` |

All phases are ordered so that data is available before any consumer step, satisfying the computational ordering rule.

---

## Power Analysis Parameters

The power analysis (Phase 8) assumes:
- **Sample Size**: 50 participants, 100 trials per participant (total trials aligned with spec's ~10k estimate).
- **Effect Size**: f = 0.15 (small-to-moderate effect in a mixed model).
- **ICC (Intra-Class Correlation)**: ≈ 0.1 for both participants and items (typical for eye-tracking studies).
- **Significance Level**: α = 0.05 (post-FDR correction).
- **Simulation**: Multiple datasets generated with these parameters; power is estimated as the proportion of simulations where p < α.
- **Threshold**: If power < 0.8, the study is flagged as "invalid for inference" (SC‑003) regardless of observed p-value.

This power analysis is conditional on the assumed sample size. If the actual study has fewer participants or trials, power will be lower and the result may be invalid.
