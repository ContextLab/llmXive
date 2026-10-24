# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-10-23 | **Spec**: `specs/001-influence-of-visual-salience/spec.md`  
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

## Summary
The pipeline consists of (1) strict verification of the OpenNeuro ds003123 dataset, (2) CPU‑only generation of pixel‑wise salience maps using the DeepGaze II model (with a deterministic spectral‑residual fallback for out‑of‑memory or time‑exceeding cases), (3) semantic ROI mask creation for “faces” via YOLOv8 and for “weapons” via Detectron2 (lazy‑imported, with YOLOv8 fallback if Detectron2 is unavailable), (4) extraction of fixation metrics from the raw eye‑tracking logs, (5) alignment of salience scores with fixation metrics plus low‑level visual covariates, (6) collinearity diagnostics (VIF & optional PCA), (7) fitting of two linear mixed‑effects models (Model A: random intercepts; Model B: random intercepts + salience slopes), (8) Benjamini‑Hochberg FDR correction, (9) simulation‑based power analysis, (10) generation of a mandatory “correlational only” disclaimer, and (11) contract‑based validation of all artifacts.

All steps run on the GitHub Actions free‑tier CPU runner; DeepGaze II inference is performed on down‑sampled 224 × 224 images to stay within the 7 GB RAM / 6 h limit. The pipeline aborts cleanly with a clear error code if the required OpenNeuro dataset is not present, satisfying the fabrication‑gate.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (CPU‑only, pip‑installable):
  - `torch>=2.0.0` (CPU‑only wheels) – required for DeepGaze II  
  - `deepgaze2-pytorch>=0.1.0` (hypothetical lightweight wrapper)  
  - `opencv-contrib-python>=4.8.0` (spectral‑residual fallback)  
  - `ultralytics>=8.0.0` (YOLOv8)  
  - `detectron2>=0.7` (weapon detection; lazy‑imported)  
  - `pandas>=2.2.0`, `numpy>=1.26.0`, `scikit-image>=0.22.0`  
  - `statsmodels>=0.14.0`, `pingouin>=0.5.4` (mixed‑effects & diagnostics)  
  - `scikit-learn>=1.3.0`, `pytest>=8.0.0`, `jsonschema>=4.21.0`  
- **Storage**: Local filesystem under `data/` (raw, interim, processed).  
- **Testing**: `pytest`; contract tests validate output files against the three schemas in `contracts/`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h).  
- **Constraints**: Full separation of salience‑generation code (`code/salience/`) from eye‑tracking code (`code/eye_tracking/`) (Constitution Principle VI).  
- **Scale/Scope**: ~200 stimulus images; ~10 k trials (typical for ds003123). DeepGaze II inference occurs within a few tenths of a second per image (down‑sampled), total [deferred]; Detectron weapon detection is achieved with near‑real‑time processing speed per image.; YOLOv* face detection operates with low latency, on the order of a fraction of a second per image.; mixed‑effects fitting < 2 min.

## Constitution Check
| Principle | Status | Action |
|---|---|---|
| I. Reproducibility | PASS | Fixed random seeds in `code/config.py`; deterministic DeepGaze II inference (fixed weight download URL) and spectral‑residual fallback. |
| II. Verified Accuracy | PASS | No fabricated dataset URLs; all external resources are open‑source and version‑pinned. |
| III. Data Hygiene | PASS | Raw data never altered; `data/raw/checksums.json` records SHA‑256 of every raw file; all transformations write new files with documented derivations. |
| IV. Single Source of Truth | PASS | Every figure/statistic derives from `data/processed/aligned_data.csv` and `data/processed/results.json`. |
| V. Versioning Discipline | PASS | Content hashes recorded in project state; any artifact change updates the timestamp. |
| VI. Perceptual‑Cognitive Independence | PASS | Separate modules (`code/salience/` vs `code/eye_tracking/`) with no shared imports; validated by `independence_validator.py`. |
| VII. Bidirectional Result Interpretation | PASS | `model_fit.py` emits interpretation blocks for both significant and null outcomes; disclaimer enforced. |

## Project Structure
```text
specs/001-influence-of-visual-salience/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── output.schema.yaml
    └── salience.schema.yaml

code/
├── config.py                # seeds, thresholds, paths
├── bootstrap.py             # --root argument, creates logs/, writes requirements.txt, quickstart.md
├── ingestion/
│   └── verify_data.py       # strict structure + SHA‑256 checksums
├── salience/
│   └── generate_maps.py     # DeepGaze II primary; spectral‑residual fallback
├── eye_tracking/
│   ├── parse_fixations.py   # fixation metric extraction
│   └── segment_roi.py       # YOLOv8 (faces) + Detectron2 (weapons); lazy imports, fallback
├── analysis/
│   ├── align_data.py
│   ├── orthogonalize.py     # VIF & optional PCA
│   ├── model_fit.py         # LMM A/B, FDR, power, disclaimer
│   └── diagnostics.py
├── utils/
│   ├── resource_validator.py
│   ├── independence_validator.py
│   └── final_validator.py
└── main.py                  # orchestrates the full pipeline

data/
├── raw/                     # manual placement of ds003123 + checksums.json
├── interim/
│   ├── salience_maps/
│   ├── masks/
│   └── fixations.csv
└── processed/
    ├── aligned_data.csv
    └── results.json
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Detectron2 import | Heavy compiled dependency, but required by FR‑008 | YOLOv8 alone does not satisfy the ensemble requirement; we keep Detectron2 with lazy import and graceful degradation. |
| DeepGaze II CPU cost | Potentially exceeds budget on full‑resolution images | Down‑sampling to 224 × 224 and batch‑processing keeps runtime < 2 min; spectral‑residual fallback guarantees completion. |
| Bootstrap path monkey‑patching | Test failure (T001) | `bootstrap.py` now accepts an explicit `--root` argument and uses `paths.root` correctly. |
| Data verification silent on participants | Missing enforcement (T002) | `verify_data.py` now aborts with `DATA_MISSING_001` if no `sub‑*` directories are present and computes non‑empty checksums. |
| Salience generation failure (T003) | Previously used only spectral‑residual | Replaced with DeepGaze II primary method; fallback ensures no hard failure. |
| ROI mask import error (T004) | Detectron2 caused import error | Lazy import with try/except; fallback to YOLOv8 for weapons if Detectron2 unavailable. |
| Fixation parsing error (T005) | Script crashed on malformed logs | Added robust CSV parsing, missing‑field handling, and explicit warnings. |

## Phase Overview & Task Mapping to FR/SC

| # | Task | FR / SC | Verifiable Artifact |
|---|---|---|---|
| T001 | **Bootstrap with explicit root** (`bootstrap.py --root <dir>`) – creates `logs/`, writes `requirements.txt` and `quickstart.md` under the supplied root. Unit test `tests/test_bootstrap.py` asserts files exist in the temp path. | — (infra) | `logs/` dir, `requirements.txt`, `quickstart.md` under temp root; passing `pytest tests/test_bootstrap.py`. |
| T002 | **Strict data verification** (`verify_data.py`) – checks `data/raw/ds003123/stimuli/` and at least one `sub‑*` participant folder, computes SHA‑256 for every file, writes non‑empty `data/raw/checksums.json`. Exits 1 with `DATA_MISSING_001` on failure. | Assumptions; Principle III | Non‑empty `checksums.json`; passing `tests/test_verify_data.py`. |
| T003 | **CPU salience map generation** (`generate_maps.py`) – loads DeepGaze II (CPU) on down‑sampled images; if a frame exceeds memory/time thresholds, falls back to OpenCV `StaticSaliencySpectralResidual`. Writes `<stimulus_id>.npy` and `salience_metadata.json` conforming to `salience.schema.yaml`. | FR‑001, SC‑001, SC‑002 | One `.npy` per image, matching resolution; `salience_metadata.json`; passing `tests/test_salience.py`. |
| T004 | **ROI masks via YOLOv8 + Detectron2** (`segment_roi.py`) – lazy import of `ultralytics` (faces) and `detectron2` (weapons). Detectron2 used when available; otherwise YOLOv8 processes weapons as well. Low‑confidence detections (<0.85) are discarded and logged; if any detector unavailable, masks are marked `undetected` and pipeline continues. Writes binary `.png` masks and `mask_metadata.csv`. | FR‑008 (ensemble), FR‑002 | Mask files + `mask_metadata.csv`; passing `tests/test_segment_roi.py` (includes graceful‑degradation test). |
| T005 | **Fixation extraction** (`parse_fixations.py`) – parses raw eye‑tracking logs, computes dwell time, first‑fixation probability, fixation latency per trial/ROI; excludes trials with missing data, logs warnings. | FR‑002 | `data/interim/fixations.csv` with required columns; passing `tests/test_parse_fixations.py`. |
| T006 | **Alignment & covariates** (`align_data.py`) – merges salience ROI means, low‑level visual features (luminance, contrast, edge density, scene complexity) with fixation metrics → `aligned_data.csv`. Reports alignment proportion (SC‑005). | FR‑003, FR‑009, SC‑005 | `aligned_data.csv` validated against `dataset.schema.yaml`. |
| T007 | **Collinearity diagnostics** (`orthogonalize.py`) – computes VIF for all predictors; if any VIF > 5, applies PCA orthogonalization to the low‑level covariates. Writes pre/post VIF to `logs/diagnostics.log` and to `results.json`. | FR‑009, SC‑006 | VIF report in `results.json`. |
| T008 | **Mixed‑effects modeling** (`model_fit.py`) – fits Model A (random intercepts for participants & items) and Model B (adds random slope for salience) using `statsmodels.MixedLM`. Applies Benjamini‑Hochberg FDR to all fixed‑effect p‑values. Stores estimates, CIs, and stability metric (`|β_A − β_B|`). | FR‑004, FR‑005, FR‑006, SC‑004 | `results.json` conforming to `output.schema.yaml`. |
| T009 | **Power analysis** (`diagnostics.py`) – simulation‑based (500 reps) using actual N, effect size f = 0.15, ICC ≈ 0.1, α = 0.05; stores `power_estimate` and `power_status` (valid if ≥ 0.8). | SC‑003 | Power fields in `results.json`. |
| T010 | **Disclaimer enforcement** (integrated in `model_fit.py`) – any JSON/CSV artifact containing p‑values < 0.05 receives a `"disclaimer": "correlational only"` field; also added to `results.json`. | FR‑007 | Disclaimer present in validated artifacts. |
| T011 | **Independence & resource validation** (`independence_validator.py`, `resource_validator.py`) – asserts no shared imports between salience and eye‑tracking modules; logs peak RAM/CPU time vs free‑tier limits. | Principle VI, SC‑002 | Passing validator runs; `logs/resource.log`. |
| T012 | **Contract validation & end‑to‑end run** (`final_validator.py` + `main.py --stage full`) – executes T002→T011 in order, validates all outputs against the three schemas. | FR‑007 (gate) | Successful pipeline run (or clean abort with `DATA_MISSING_001`); all contract tests pass. |

All tasks are ordered so that data is downloaded before any consumer step, models are fitted before evaluation, and figures would be generated after model results (figure generation is delegated to the downstream paper stage).

---

