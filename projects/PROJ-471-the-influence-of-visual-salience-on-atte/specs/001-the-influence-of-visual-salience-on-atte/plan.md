# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-10-24 (re-plan v2) | **Spec**: `specs/001-influence-of-visual-salience/spec.md`
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

> **Re-plan note (v2)**: This revision preserves the overall pipeline design but replaces the repeatedly-unverifiable components from v1:
> - **DeepGaze II / GBVS salience** (T003 failed) → **OpenCV Static Saliency (spectral residual + center-surround fallback)**: pure CPU, no model downloads, deterministic, runs in seconds per image.
> - **Detectron2 weapons segmentation** (T004 failed — import error) → **YOLOv8 for both faces and weapons** (single lightweight library; Detectron2 dropped from the toolchain).
> - **Bootstrap test path patching** (T001 failed) → bootstrap now accepts an explicit `--root` argument; no monkeypatching of toolkit internals.
> - **Data verification** (T002 failed) → `verify_data.py` strictly enforces the expected directory structure (`stimuli/` AND `sub-*` participant directories), computes real per-file SHA-256 checksums, and exits non-zero with `DATA_MISSING_001` when the structure is incomplete. Empty checksum files are a hard failure.
> Each task below now promises a **deterministically verifiable artifact** (a real file with expected schema/content, or a recorded passing test run).

## Summary

The pipeline (1) verifies the locally-placed OpenNeuro ds003123 dataset and records per-file checksums, (2) computes pixel-wise CPU salience maps for every stimulus image using OpenCV spectral-residual saliency with a center-surround fallback, (3) creates semantic ROI masks for faces and weapons using YOLOv8, (4) extracts fixation metrics (first-fixation probability, dwell time, latency) from raw eye-tracking logs, (5) aligns salience scores with fixation metrics per trial and augments with low-level visual covariates (luminance, contrast, edge density), (6) diagnoses collinearity (VIF) with optional PCA orthogonalization, (7) fits linear mixed-effects models (Model A/B) with FDR correction, power analysis, and sensitivity analysis, and (8) validates all outputs against the contracts in `contracts/`.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies** (all CPU-only, pip-installable, no compilation):
  - `opencv-contrib-python>=4.8.0` (includes `cv2.saliency` module)
  - `ultralytics>=8.0.0` (YOLOv8; weights auto-download from ultralytics CDN)
  - `statsmodels>=0.14.0`, `pingouin>=0.5.4`, `scikit-learn>=1.3.0`
  - `pandas>=2.2.0`, `numpy>=1.26.0`, `scikit-image>=0.22.0`
  - `pytest>=8.0.0`, `jsonschema>=4.21.0`
  - **Removed vs v1**: `detectron2` (import failure on CI), DeepGaze II weights (GPU model; unverifiable on CPU box), `datasets`/`torch` (no longer needed).
- **Storage**: local filesystem under `data/` (raw, interim, processed).
- **Testing**: `pytest`; contract tests validate real output files against `contracts/*.schema.yaml`.
- **Target Platform**: GitHub Actions free-tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h). **No GPU step remains** — every method has a faithful CPU form.
- **Constraints**: predictor (salience) and outcome (eye-tracking) code paths fully isolated (Constitution Principle VI). Dataset requires manual placement (no verified open download source exists — see research.md §2).
- **Scale/Scope**: ~200 stimulus images (spectral-residual saliency ≈ 0.1 s/image on CPU); eye-tracking trials as present in ds003123.

## Constitution Check

| Principle | Status | Action |
|---|---|---|
| I. Reproducibility | PASS | Seeds pinned in `code/config.py`; salience (spectral residual) is deterministic; YOLOv8 inference is deterministic at fixed confidence threshold; dataset path fixed. |
| II. Verified Accuracy | PASS | No external dataset URLs are cited (none verified for ds003123 — stated explicitly, not fabricated). YOLOv8 weights come from the standard ultralytics release channel named in code. |
| III. Data Hygiene | PASS | Raw data never altered; `data/raw/checksums.json` records SHA-256 of every raw file; every transformation writes a new file. |
| IV. Single Source of Truth | PASS | Every figure/statistic traces to `data/processed/aligned_data.csv` and `data/processed/results.json`. |
| V. Versioning Discipline | PASS | Content hashes recorded; state timestamp updated on artifact change. |
| VI. Perceptual-Cognitive Independence | PASS | `code/salience/` (image-derived) and `code/eye_tracking/` (gaze-derived) are separate modules with no shared code path; `independence_validator.py` asserts this structurally. |
| VII. Bidirectional Result Interpretation | PASS | `model_fit.py` emits interpretation blocks for both positive and null outcomes; disclaimer enforced on all p-value-bearing artifacts. |

## Project Structure

```text
specs/001-influence-of-visual-salience/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── salience.schema.yaml
└── tasks.md            # (created by /speckit-tasks)

code/
├── config.py                # seeds, thresholds, paths, confidence cutoffs
├── bootstrap.py             # --root argument; writes requirements.txt, logs/ dir
├── ingestion/
│   └── verify_data.py       # strict structure check + real SHA-256 checksums
├── salience/
│   └── generate_maps.py     # OpenCV spectral residual (primary) + center-surround fallback
├── eye_tracking/
│   ├── parse_fixations.py   # dwell, first-fixation, latency from raw logs
│   └── segment_roi.py       # YOLOv8 for faces AND weapons (lazy import, graceful degradation)
├── analysis/
│   ├── align_data.py
│   ├── orthogonalize.py     # VIF + optional PCA
│   ├── model_fit.py         # LMM A/B, FDR, power, disclaimer
│   └── diagnostics.py
├── utils/
│   ├── resource_validator.py
│   ├── independence_validator.py
│   └── final_validator.py
└── main.py

data/
├── raw/                     # manual placement of ds003123 + checksums.json
├── interim/                 # salience_maps/, masks/, fixations.csv, salience_metadata.json
└── processed/               # aligned_data.csv, results.json
```

**Structure Decision**: single-project layout; `bootstrap.py` takes an explicit `--root` argument (fixes T001).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Detectron2 dropped (deviates from FR-008's "ensemble") | Detectron2 could not be imported on the CI runner (T004 failure) | YOLOv8 alone covers both face and weapon detection with one lightweight, pip-installable library; keeping Detectron2 would leave the task unverifiable |

## Phase Overview & Task Mapping to FR/SC

All phases ordered so data exists before consumers; models fitted before evaluation; no GPU steps.

| # | Task | FR / SC | Verifiable artifact |
|---|---|---|---|
| T001 | **Bootstrap with explicit root**: `code/bootstrap.py --root <dir>` creates `logs/`, writes `requirements.txt` and `quickstart.md` under that root. Unit test `tests/test_bootstrap.py` passes by invoking the script with `--root tmp_path` (no monkeypatching). | — (infra) | recorded passing `pytest tests/test_bootstrap.py` run; files exist under tmp root |
| T002 | **Strict data verification**: `verify_data.py` requires `data/raw/ds003123/stimuli/` AND ≥1 `sub-*` directory; computes SHA-256 for every raw file into `data/raw/checksums.json`; exits 1 with `DATA_MISSING_001` and an empty-checksum guard (checksum file with zero entries ⇒ failure) when structure is incomplete. Tested against synthetic fixture trees. | Assumptions; Principle III | `data/raw/checksums.json` with ≥1 real entry (or recorded non-zero exit + error message when dataset absent); passing `tests/test_verify_data.py` |
| T003 | **CPU salience maps**: `generate_maps.py` runs OpenCV `StaticSaliencySpectralResidual` per image; on failure or degenerate output falls back to a center-surround difference map (pure numpy). Writes `.npy` map at source resolution + `salience_metadata.json` (schema-conformant, `generation_method` ∈ {spectral_residual, center_surround}). No model downloads, no GPU. | FR-001, SC-001, SC-002 | one `.npy` per input image with matching height/width; `salience_metadata.json` validates against `salience.schema.yaml`; passing `tests/test_salience.py` |
| T004 | **ROI masks via YOLOv8 only**: `segment_roi.py` lazily imports `ultralytics` inside main (module import never fails the test suite); runs YOLOv8 detection for faces and weapons; writes binary masks + `mask_metadata.csv`; low-confidence (<0.85) masks flagged, never crash. If ultralytics/weights unavailable, logs degradation and marks all ROIs `undetected` (pipeline continues; images flagged for review). | FR-008 (adapted: YOLOv8 for both classes) | mask `.png` files + `mask_metadata.csv`; passing `tests/test_segment_roi.py` (uses a tiny synthetic image; graceful-degradation path also tested) |
| T005 | **Fixation extraction**: `parse_fixations.py` parses raw eye-tracking logs (auto-detects format among ds003123's expected tabular exports); computes dwell time, first-fixation probability, fixation latency per trial/ROI; missing-data trials excluded with `excluded=True` + warning log. | FR-002 | `data/interim/fixations.csv` with required columns; passing `tests/test_parse_fixations.py` (fixture log fixture) |
| T006 | **Alignment & covariates**: `align_data.py` merges salience ROI means, masks, fixation metrics, luminance/contrast/edge-density (computed in `code/salience/`, image stream only) → `aligned_data.csv`; reports alignment proportion (SC-005). | FR-003, FR-009, SC-005 | `aligned_data.csv` validating against `dataset.schema.yaml`; alignment-proportion entry in `results.json` |
| T007 | **Collinearity diagnostics**: `orthogonalize.py` computes VIF for all predictors; PCA-orthogonalizes {luminance, contrast, edge_density} if any VIF > 5; writes pre/post VIF to `logs/diagnostics.log` and `results.json`. | FR-009, SC-006 | VIF report block in `results.json` / diagnostics log |
| T008 | **Mixed-effects modeling**: `model_fit.py` fits Model A (random intercepts: participants, items) and Model B (+ random salience slopes) via `statsmodels MixedLM`; Benjamini-Hochberg FDR on all fixed-effect p-values; 95% CI; sensitivity stability metric \|β_A − β_B\|. | FR-004, FR-005, FR-006, SC-004 | `results.json` validating against `output.schema.yaml` |
| T009 | **Power analysis**: `diagnostics.py` runs simulation-based power (500 reps, parameters from actual aligned N; effect size f=0.15, ICC≈0.1, α=0.05); sets `power_status` = valid/invalid per SC-003. | SC-003 | `power_status` + power estimate in `results.json` |
| T010 | **Disclaimer & interpretation enforcement**: p-value-bearing JSON/CSV artifacts get a `"correlational only"` disclaimer block; both positive- and null-result interpretation templates emitted (Principle VII). | FR-007 | disclaimer field present in validated artifacts |
| T011 | **Independence & resource validation**: `independence_validator.py` asserts no shared import/code path between `code/salience/` and `code/eye_tracking/`; `resource_validator.py` logs RAM/CPU-time (SC-002). | Principle VI, SC-002 | passing validator runs; `logs/resource.log` |
| T012 | **Contract validation & end-to-end run**: `final_validator.py` validates all artifacts against the three schemas; `main.py --stage full` orchestrates T002→T011 in dependency order. | FR-007 (gate) | recorded passing full-pipeline run (or recorded clean `DATA_MISSING_001` abort when dataset absent) + passing `tests/contract/` |

## Power Analysis Parameters

Unchanged from v1: simulation-based (500 reps), effect size f = 0.15, ICC ≈ 0.1 for participants and items, α = 0.05 (post-FDR). Sample-size parameters are taken from the **actual** aligned dataset (participants, trials) rather than assumed values, and the estimate is reported with an explicit limitation note if the realized N differs from design assumptions. Power < 0.8 ⇒ `power_status: "invalid"` (SC-003).
