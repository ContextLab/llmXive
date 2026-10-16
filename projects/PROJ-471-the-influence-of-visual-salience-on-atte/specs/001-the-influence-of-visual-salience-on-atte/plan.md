# Implementation Plan: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Branch**: `001-influence-of-visual-salience` | **Date**: 2026-10-16 | **Spec**: `specs/001-influence-of-visual-salience/spec.md`  
**Input**: Feature specification from `/specs/001-influence-of-visual-salience/spec.md`

## Summary
The project quantifies how computational visual salience (predictor) relates to human attentional allocation (outcome) during moral‑judgment image viewing. The pipeline consists of:

1. **Data Availability Check** – verify that the OpenNeuro Moral Foundations Eye‑Tracking Dataset (ds003123) is present locally (manual prerequisite).  
2. **Salience Map Generation (FR‑001)** – compute pixel‑wise salience maps for all a set of stimulus images using **GBVS** (CPU‑friendly) as the primary method; **DeepGaze II** is retained only as an optional GPU fallback (`device="cuda"`).  
3. **ROI Mask Generation (FR‑008)** – create semantic masks for “faces” (YOLOv8) and “weapons” (Detectron2) when not supplied.  
4. **Eye‑Tracking Metric Extraction (FR‑002)** – parse raw eye‑tracking files to obtain first‑fixation probability, dwell time, **fixation latency** for each predefined ROI.  
5. **Alignment (FR‑003)** – merge salience scores with fixation metrics per trial using unique trial IDs.  
6. **Low‑Level Feature Computation (FR‑009)** – compute **luminance**, **contrast**, **edge density** for each stimulus; these are **included as covariates** in the mixed‑effects model (not merely diagnostic).  
7. **Statistical Modeling (FR‑004, FR‑005, FR‑006, FR‑007)** – fit a linear mixed‑effects model with salience *and* low‑level covariates as fixed predictors, random intercepts for participants and items, and random slopes for salience in Model B. Apply Benjamini‑Hochberg FDR correction. Always append the required `"disclaimer": "correlational only"` field to the results JSON (per contract). Conduct sensitivity analysis comparing Model A (intercepts only) vs Model B (intercepts + slopes).  
8. **Resource & Power Validation (SC‑002, SC‑003)** – enforce RAM/CPU limits; perform a **simulation‑based power analysis** for the mixed‑effects design (500 replicates, effect size f = 0.15, α = 0.05). Abort with `POWER_INSUFFICIENT` if power < 0.8.  
9. **Output Validation (contracts)** – validate final CSV/JSON artifacts against schema files and ensure the disclaimer is present.

All steps are deterministic, produce real files, and are verifiable via the contract schemas.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets`, `torch==2.2.0`, `transformers`, `statsmodels`, `opencv-python`, `ultralytics` (YOLOv8), `detectron2`, `pandas`, `numpy`, `pingouin`  
- **Storage**: Local filesystem (`data/raw`, `data/interim`, `data/processed`)  
- **Testing**: `pytest` (contract tests, unit tests for alignment & model schema)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h) – **CPU‑first**; GPU escape hatch only for optional DeepGaze II fallback.  
- **Constraints**: Strict separation of predictor (salience) and outcome (eye‑tracking) code paths (Constitution Principle VI).  
- **Scale/Scope**: 200 stimulus images, A substantial number of eye‑tracking trials..

## Constitution Check
| Principle | Status | Action |
|---|---|---|
| I. Reproducibility | PASS | Random seeds pinned; dataset fetched manually but path fixed. |
| II. Verified Accuracy | PASS (conditional) | All external weights are auto‑downloaded from verified HuggingFace URLs. |
| III. Data Hygiene | PASS | Raw data unchanged; derived files checksum‑recorded. |
| IV. Single Source of Truth | PASS | Every figure/table traces to rows in `data/processed/aligned_data.csv` and entries in `data/processed/results.json`. |
| V. Versioning Discipline | PASS | Content hashes recorded; timestamps updated on change. |
| VI. Perceptual‑Cognitive Independence | PASS | Salience generation (`code/salience/`) and eye‑tracking parsing (`code/eye_tracking/`) are separate modules; `independence_validator.py` asserts no shared objects. |
| VII. Bidirectional Result Interpretation | PASS | Scripts output both positive and null interpretations equally. |

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
├── config.py                # seeds, thresholds, batch size
├── ingestion/
│   └── verify_data.py       # aborts if ds003123 missing
├── salience/
│   └── generate_maps.py     # GBVS primary, DeepGaze II GPU fallback
├── eye_tracking/
│   ├── parse_fixations.py   # extracts dwell, first‑fixation, latency
│   └── segment_roi.py       # YOLOv8 + Detectron2 ensemble
├── analysis/
│   ├── align_data.py
│   ├── model_fit.py         # LMM with covariates, FDR, disclaimer
│   └── diagnostics.py       # VIF, edge density, power simulation
├── utils/
│   ├── resource_validator.py
│   ├── independence_validator.py
│   └── final_validator.py   # schema validation + disclaimer insertion
└── main.py                  # orchestrator

data/
├── raw/                     # manual placement of ds003123
├── interim/
│   ├── salience_maps/
│   ├── masks/
│   └── fixations.csv
└── processed/
    ├── aligned_data.csv
    └── results.json
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Covered By | Description |
|---|---|---|
| FR‑001 | Salience generation (`code/salience/generate_maps.py`) | GBVS pixel‑wise maps for all 200 images; DeepGaze II fallback on GPU. |
| FR‑002 | Eye‑tracking parsing (`code/eye_tracking/parse_fixations.py`) | Extraction of first‑fixation probability, dwell time, **fixation latency**. |
| FR‑003 | Alignment (`code/analysis/align_data.py`) | Merges salience scores with fixation metrics via trial IDs. |
| FR‑004 | Model fitting (`code/analysis/model_fit.py`) | LMM with random intercepts (participants, items). |
| FR‑005 | Sensitivity analysis (`code/analysis/diagnostics.py`) | Comparison of Model A vs Model B, stability metric recorded. |
| FR‑006 | FDR correction (`code/analysis/model_fit.py`) | Benjamini‑Hochberg applied to all p‑values. |
| FR‑007 | Final validator (`code/utils/final_validator.py`) | Unconditionally adds `"disclaimer": "correlational only"` to results JSON. |
| FR‑008 | ROI segmentation (`code/eye_tracking/segment_roi.py`) | YOLOv8 (faces) + Detectron2 (weapons) ensemble; flags low‑confidence masks. |
| FR‑009 | Diagnostics (`code/analysis/diagnostics.py`) | Computes luminance, contrast, **edge density**; includes them as covariates in the model. |
| SC‑001 | Salience generation logs (`resource_validator.py`) | Success proportion logged; failures counted. |
| SC‑002 | Resource validator (`resource_validator.py`) | RAM/CPU usage compared to GitHub Actions limits. |
| SC‑003 | Power analysis (`diagnostics.py`) | Simulation‑based power check; aborts with `POWER_INSUFFICIENT` if < 0.8. |
| SC‑004 | Sensitivity analysis output (`results.json`) | Stability metric recorded and compared across models. |
| SC‑005 | Alignment log (`data/interim/alignment_log.csv`) | Proportion of aligned trials recorded. |
| SC‑006 | VIF calculation (`diagnostics.py`) | VIF values for all predictors compared to threshold 5. |

---

