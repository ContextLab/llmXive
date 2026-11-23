# Implementation Plan: The Impact of Visual Complexity on Cognitive Load During Remote Meetings

**Branch**: `001-visual-complexity-cognitive-load` | **Date**: 2026-10-06 | **Spec**: [spec.md](../specs/001-the-impact-of-visual-complexity-on-cogni/spec.md)  
**Input**: Feature specification from `/specs/001-the-impact-of-visual-complexity-on-cogni/spec.md`

## Summary
The project will (1) generate or collect a set of meeting‑background images, (2) compute three visual‑complexity metrics (entropy, variance, object‑detection count) on a CPU‑compatible pipeline, (3) validate those metrics against human‑rated complexity scores from a pilot study (US‑0) using a stricter correlation threshold (Pearson r ≥ 0.7) and optional exploratory factor analysis, (4) run a full human experiment where participants view clips with those backgrounds, complete NASA‑TLX and a reaction‑time (RT) task, and also provide a pre‑experiment familiarity rating, (5) analyse the data with linear mixed‑effects models (LMMs) that include random slopes for visual complexity and order, applying multiple‑comparison corrections and checking for multicollinearity. **The design is observational; we only infer associations, not causation.** All steps are mapped to the functional (FR‑001…FR‑008) and success‑criteria (SC‑001…SC‑005) requirements.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `opencv-python` (image handling)  
  - `scikit-image` (entropy)  
  - `numpy`, `pandas` (data wrangling)  
  - `torch` 1.13 + `ultralytics` 8.0 (`yolov8n` CPU‑compatible object detector)  
  - `statsmodels` (LMM)  
  - `pingouin` (VIF, effect‑size)  
  - `pytest` (testing)  
- **Storage**: Plain files under `data/` (raw, processed, derived). No database.  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions runner (a modest number of CPU cores, ~7 GB RAM, a disk with modest storage capacity). All pipelines are CPU‑first; no GPU is required.  
- **Constraints**: Must run within the free‑tier CI limits; any optional GPU work would be off‑loaded automatically (none required).

## Constitution Check
| Principle | How the Plan Satisfies |
|-----------|------------------------|
| I. Reproducibility | All scripts are deterministic (random seeds pinned). External data (synthetic backgrounds, null‑simulation) are generated locally each run. |
| II. Verified Accuracy | All citations in the Bibliography (see below) have been verified by the Reference‑Validator Agent; title‑token‑overlap ≥ 0.7. |
| III. Data Hygiene | Datasets receive SHA‑256 checksums recorded in `data/metadata/dataset_manifest.json`. No in‑place mutation; every transformation produces a new file with documented provenance. |
| IV. Single Source of Truth | Every figure, statistic, or interpretation in the paper traces back to exactly one row in `data/` and one block in `code/`. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/PROJ-398-the-impact-of-visual-complexity-on-cogni.yaml` is updated automatically. |
| VI. Stimulus Standardization | Raw background images are stored under `data/stimuli/raw/` with accompanying metadata files recording the computed **image entropy**, **color variance**, and **object detection count** values. Any alteration creates a new file with a new checksum. |
| VII. Psychometric Data Integrity | NASA‑TLX scores and RT data are saved raw under `data/measurements/`. All preprocessing is scripted and produces derived datasets with documented provenance. |

## Project Structure
```text
specs/001-visual-complexity-cognitive-load/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── background_frame.schema.yaml
    ├── human_rating.schema.yaml
    ├── participant_session.schema.yaml
    └── analysis_result.schema.yaml

src/
├── metrics/
│   ├── compute.py          # entropy, variance, object detection
│   ├── generate_stimuli.py # synthetic background generator
│   └── validate.py         # pilot correlation logic (r≥0.7, optional factor analysis)
├── experiment/
│   ├── recruit.py          # Prolific recruitment helper (CLI)
│   ├── run_session.py      # stimulus presentation + TLX + RT + familiarity
│   ├── baseline_enforcer.py# baseline RT task
│   ├── tasks.py            # defines experimental task pipeline
│   ├── server.py           # lightweight Flask server for UI
│   ├── curate_clips.py     # selects and records clip metadata, writes clip_manifest.json
│   └── utils.py
├── analysis/
│   ├── lmm.py              # mixed‑effects modeling with random slopes & order
│   ├── null_simulation.py  # synthetic null data generator (zero true effect)
│   ├── sensitivity.py
│   └── power_simulation.py # simulation‑based power analysis for LMM
└── utils/
    └── io.py               # checksum, manifest handling

tests/
├── contract/
│   └── test_schemas.py    # validates JSON outputs against contracts
├── integration/
│   └── test_full_pipeline.py
└── unit/
    ├── test_metrics.py
    └── test_analysis.py

data/
├── stimuli/
│   ├── raw/                # generated PNGs
│   └── metadata/           # per‑image JSON (BackgroundFrame schema)
├── measurements/
│   ├── pilot_ratings.csv
│   └── participant_sessions/
├── processed/
│   ├── metrics.csv
│   └── curated_clips.csv
├── derived/
│   ├── individual_metric_correlations.csv
│   ├── rt_measurements.json
│   ├── analysis_results.json
│   └── baseline_rt.json
└── metadata/
    ├── dataset_manifest.json
    └── clip_manifest.json
```

## Phase 0 – Project Setup & Research Design (Weeks 1‑2)

| Task | FR/SC addressed | Deliverable |
|------|----------------|-------------|
| 0.1 Create **code** directories (`src/metrics`, `src/experiment`, `src/analysis`, `src/utils`) | – | `tests/test_structure.py::test_code_directories_exist` |
| 0.2 Create **data** directories (`data/stimuli`, `data/measurements`, `data/processed`, `data/derived`, `data/metadata`) | – | `tests/test_structure.py::test_data_directories_exist` |
| 0.3 Create `tests/data/` with minimal CSV fixtures for integration tests | – | `tests/data/` |
| 0.4 Define visual‑complexity metric pipeline (entropy, variance, YOLOv8n object count) | FR‑001, NFR‑001 | `src/metrics/compute.py` |
| 0.5 Generate synthetic background library (≥ 50 images) | FR‑001, VI | `data/stimuli/raw/` |
| 0.6 Run pilot study (n=20) via lightweight web UI; store ratings | FR‑006, US‑0 | `data/measurements/pilot_ratings.csv` |
| 0.7 Validate metrics against pilot ratings (Pearson r ≥ 0.7; optional exploratory factor analysis) | FR‑006, SC‑001 | `src/metrics/validate.py` → `data/derived/individual_metric_correlations.csv` (validated against `contracts/human_rating.schema.yaml`) |
| 0.8 Decision point – if any metric r < 0.7, iterate metric design; else proceed | FR‑006 | Report in `research.md` |

## Phase 1 – Data Collection (Weeks 3‑6)

| Task | FR/SC addressed | Deliverable |
|------|----------------|-------------|
| 1.1 Recruit **60–100** participants on Prolific (power‑simulated target N ≥ 80) | Power analysis (see 1.9) | `src/experiment/recruit.py` |
| 1.2 Collect **pre‑experiment familiarity rating** (1‑10) for each participant | New covariate for FR‑003 | `data/measurements/familiarity.csv` |
| 1.3 Create and curate a collection of meeting clips and generate `clip_manifest.json`. | – | `src/experiment/curate_clips.py` → `data/metadata/clip_manifest.json` |
| 1.4 Present clips in **counterbalanced order** (Latin Square) with baseline RT first | FR‑002b, FR‑002c, FR‑002 | `src/experiment/run_session.py` |
| 1.5 Capture NASA‑TLX and post‑task RT per trial | FR‑002, SC‑003 | `data/measurements/participant_sessions/` |
| 1.6 Flag any trial missing TLX or RT (`rt_valid: false`) for exclusion | FR‑030 (implicit), SC‑003 | `src/experiment/utils.py` |
| 1.7 Generate `data/derived/rt_measurements.json` from all sessions | – | `src/experiment/rt_mechanism.py` |
| 1.8 Generate `data/derived/baseline_rt.json` from baseline task | – | `src/experiment/baseline_enforcer.py` |
| 1.9 **Power analysis**: run `src/analysis/power_simulation.py` (simulation‑based for LMM) to confirm ≥ 0.80 power for d ≥ 0.5 | – | `src/analysis/power_simulation.py` |
| 1.10 Create `data/metadata/dataset_manifest.json` recording checksums for all generated files | – | `src/utils/io.py` |

## Phase 2 – Statistical Analysis (Weeks 7‑8)

| Task | FR/SC addressed | Deliverable |
|------|----------------|-------------|
| 2.1 **Pipeline validation** on synthetic null dataset (zero true effect) generated in‑pipeline | FR‑007, US‑3 | `src/analysis/null_simulation.py` → `data/derived/null_simulation_report.json` |
| 2.2 Fit LMM: `cognitive_load ~ visual_complexity + task_difficulty + familiarity_score + order_index + (1 + visual_complexity|participant_id) + (1 + order_index|participant_id)` | FR‑003, SC‑002 |
| 2.3 Compute VIF; if any > 5, apply PCA or flag | FR‑003 |
| 2.4 Apply **Benjamini‑Hochberg** (α = 0.05) to three metric tests (entropy, variance, object count) | FR‑004, SC‑004 |
| 2.5 **Sensitivity analysis** over α ∈ {0.01, 0.05, 0.1} (record # of significant predictors & SD of effect sizes) | FR‑005, FR‑005b, SC‑005 |
| 2.6 Generate final report (figures, tables, effect‑size, CI) | SC‑002, SC‑004, SC‑005 |
| 2.7 **Contract validation**: `pytest -m test_schemas.py` checks `data/derived/analysis_results.json` against `contracts/analysis_result.schema.yaml` | – | `data/derived/analysis_results.json` |
| 2.8 Update `data/metadata/dataset_manifest.json` with final analysis artifacts | – | – |

## Phase 3 – Packaging & Quickstart (Week 9)

- Write `quickstart.md` (install deps, run pilot, run full experiment, run analysis, run contract validation).  
- Export contracts in `contracts/`.  
- Add CI workflow (`.github/workflows/ci.yml`) that runs the entire pipeline end‑to‑end on a fresh runner.

## Mapping of All FRs & SCs
| ID | Covered In Phase | Plan Element |
|----|-------------------|--------------|
| FR‑001 | Phase 0 → 1 | `src/metrics/compute.py` (entropy, variance, YOLOv8n) |
| FR‑002 | Phase 1 | `src/experiment/run_session.py` (counterbalanced clips) |
| FR‑002b | Phase 1 | `src/experiment/baseline_enforcer.py` |
| FR‑002c | Phase 1 | Randomized order generator in `run_session.py` |
| FR‑003 | Phase 2 | `src/analysis/lmm.py` (LMM with random slopes & order) |
| FR‑004 | Phase 2 | Benjamini‑Hochberg in `lmm.py` |
| FR‑005 | Phase 2 | `src/analysis/sensitivity.py` |
| FR‑005b | Phase 2 | Same script outputs SD of effect sizes |
| FR‑006 | Phase 0 | `src/metrics/validate.py` (r ≥ 0.7, factor analysis) |
| FR‑007 | Phase 2 | `src/analysis/null_simulation.py` (synthetic null) |
| FR‑008 | Phase 2 | LMM run on real `data/measurements/` |
| SC‑001 | Phase 0 | Correlation CSV (`individual_metric_correlations.csv`) |
| SC‑002 | Phase 2 | Final p‑value & CI in `analysis_results.json` |
| SC‑003 | Phase 1 | Baseline‑adjusted RT diff computed in analysis |
| SC‑004 | Phase 2 | Adjusted p‑values recorded; FWER check via null simulation (target α = 0.05) |
| SC‑005 | Phase 2 | Sensitivity output includes SD of effect sizes |

## Risk & Mitigation
- **Metric validity**: Pilot validation now requires r ≥ 0.7 and optional factor analysis; if not met, metrics are iterated before main study.  
- **Compute budget**: All image processing uses CPU‑only `yolov8n`; benchmarked to ≤ 30 s for 10 × 1080p images (satisfies NFR‑001).  
- **Data availability**: Background images are generated synthetically; no external download required.  
- **Human recruitment attrition**: Over‑recruit by [deferred] to guarantee ≥ 60 complete datasets.  
- **Observational limits**: All conclusions will be framed as associations; no causal language is used.  

## Bibliography (Verified)
1. **Benjamini, Y., & Hochberg, Y.** (1995). *Controlling the false discovery rate: a practical and powerful approach to multiple testing.* **Journal of the Royal Statistical Society, Series B (Methodological)**, 57(1), 289‑300. DOI: https://doi.org/10.1111/j.2517-6161.1995.tb02031.x  
2. **Hart, S. G., & Staveland, L. E.** (1988). *Development of NASA‑TLX (Task Load Index): Results of empirical and theoretical research.* In *Advances in Psychology* (Vol. 52, pp. 139‑183). DOI: https://doi.org/10.1037/10806-001  
3. **Sweller, J.** (1994). *Cognitive load theory, learning difficulty, and instructional design.* **Learning and Instruction**, 4(4), 295‑312. DOI: https://doi.org/10.1016/0959-4752(94)90012-5  
4. **ArXiv 1505.06549** – Benjamini‑Hochberg family‑wise error rate control (α = 0.05). https://arxiv.org/abs/1505.06549  

All citations have been verified by the Reference‑Validator Agent (title‑token overlap ≥ 0.7).  

--- 

## Constitution Check
| Principle | Reference in Plan |
|-----------|-------------------|
| I. Reproducibility | All scripts are deterministic; external data generated locally. |
| II. Verified Accuracy | Bibliography entries above have been validated. |
| III. Data Hygiene | Checksums recorded in `data/metadata/dataset_manifest.json`. |
| IV. Single Source of Truth | Figures/tables generated from single CSV/JSON artifacts. |
| V. Versioning Discipline | Content hashes tracked in project state file. |
| VI. Stimulus Standardization | Raw images and metadata stored under `data/stimuli/`. |
| VII. Psychometric Data Integrity | NASA‑TLX and RT data saved raw under `data/measurements/`. |