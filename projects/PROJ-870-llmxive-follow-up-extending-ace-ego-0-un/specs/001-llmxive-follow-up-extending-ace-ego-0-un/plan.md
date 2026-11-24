# Implementation Plan: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Branch**: `001-llmxive-static-proxy` | **Date**: 2026-10-24 | **Spec**: specs/001-llmxive-static-proxy/spec.md  
**Input**: Feature specification from `/specs/001-llmxive-static-proxy/spec.md`

## Summary
The project evaluates how much variance in pseudo‑action reliability scores can be explained by **static visual cues** extracted from egocentric frames, and how much additional temporal context improves prediction.  It then tests whether a **static‑proxy filtered** training set can yield Vision‑Language‑Action (VLA) models whose downstream performance is within a few percent of a full dynamic baseline.  All steps run on the CPU‑only GitHub Actions free tier; any GPU‑only component is avoided.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `opencv-python>=4.8` (CPU video decoding)  
  - `scikit-image>=0.22` (entropy)  
  - `mediapipe>=0.10` (MediaPipe Hands, CPU)  
  - `torch>=2.2` (CPU‑only, optional MLP)  
  - `torchvision>=0.17` (CPU fallback for optical flow)  
  - `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.13`  
  - `scikit-learn>=1.5` (Random Forest, CV)  
  - `statsmodels>=0.14` (paired tests, power analysis)  
  - `matplotlib>=3.8` (plots)  
  - `datasets>=2.18` (HuggingFace dataset loading, streaming)  
  - `jsonschema>=4.22` (contract validation)  
- **Storage**: Plain files under `data/` (raw downloads, CSV feature tables, model checkpoints).  
- **Testing**: `pytest` + contract validation (`jsonschema`).  
- **Target Platform**: Linux CI runner (2 CPU cores, ~7 GB RAM, ~14 GB disk).  

## Compute Feasibility (CPU‑first)
| Stage | Max Data Size | Frame Rate | Method | Expected CPU time* | Peak RAM |
|-------|---------------|------------|--------|--------------------|----------|
| Static extraction | ≤ 1 000 segments (≈ 2 h video) | 0.5 fps (adaptive ↓ to 0.25 fps if RAM > 5 GB) | OpenCV decode + MediaPipe Hands | ≤ 8 min CPU per hour of video | ≤ 5 GB |
| Temporal windows | Same subset | 0.5 fps (down‑sampled to 0.25 fps if RAM > 5 GB) | OpenCV Farneback optical flow (CPU) | ≤ 5 min CPU per hour | ≤ 5 GB |
| Regression training | ≤ 1 000 rows | – | Random Forest (n_estimators=200) | ≤ 2 min total | ≤ 2 GB |
| VLA training | ≤ 3 000 episodes (≈ 10 h video) | – | Small OpenVLA variant (2‑layer transformer, CPU) | ≤ 2 h total | ≤ 5 GB |
| Evaluation | ≥ 100 episodes per benchmark | – | Model inference (CPU) | ≤ 15 min total | ≤ 2 GB |

\*All estimates are conservative; the pipeline includes an **automatic down‑sampling fallback** that reduces the frame rate to 0.25 fps if peak RAM exceeds 5 GB, logging the adaptation.

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed random seeds; deterministic dataset loaders. |
| II. Verified Accuracy | ✅ | All external data fetched from the verified URLs listed in `research.md`. |
| III. Data Hygiene | ✅ | Checksums recorded; each transformation writes a new file. |
| IV. Single Source of Truth | ✅ | All figures/tables trace back to rows in `data/` and code blocks. |
| V. Versioning Discipline | ✅ | Artifacts hashed in the project state file. |
| VI. Static‑Dynamic Attribution | ✅ | SC‑001 measures variance explained by static features. |
| VII. Temporal Saturation Analysis | ✅ | SC‑002 defines a diminishing‑return threshold with Bonferroni correction. |

## Project Structure
```text
specs/001-llmxive-static-proxy/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── static_features.schema.yaml
│   ├── regression_prediction.schema.yaml
│   ├── temporal_window_features.schema.yaml
│   ├── static_residual.schema.yaml
│   ├── vla_experiment_result.schema.yaml
│   └── equivalence_test_result.schema.yaml
└── tasks.md   # generated later
```

Source‑code layout (Option 1: Single‑project):
```text
src/
├── data/                     # raw downloads & derived CSVs
├── features/
│   ├── static.py             # entropy, hand confidence, lighting, metadata
│   └── temporal.py           # optical‑flow statistics per window
├── models/
│   ├── static_regressor.py   # Random Forest / optional MLP wrapper
│   └── vla_variants.py       # Training scripts for three VLA variants
├── evaluation/
│   ├── metrics.py            # R², residuals, statistical tests
│   └── benchmarks.py         # RoboCasa / RoboTwin loaders & evaluators
├── utils/
│   └── logging.py
└── cli/
    └── run_pipeline.py       # Orchestrates all phases
tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_feature_extraction.py
```

## Phase‑by‑Phase Task Mapping (covers all FR/SC)

| Phase | Task ID | Description | FR/SC addressed |
|-------|---------|-------------|-----------------|
| 0 | T0‑01 | **Download verified datasets**: VLA parquet, RoboCasa zip, RoboTwin zip via `datasets.load_dataset(..., streaming=True)`. Verify SHA‑256 checksums and record them in `state/projects/...yaml`. | FR‑001 (data availability) |
| 0 | T0‑02 | Record dataset metadata (record counts, file sizes) for reproducibility. | Constitution (III, IV) |
| 1 | T1‑01 | Extract frames at **0.5 fps** (adaptive down‑sampling to 0.25 fps if RAM > 5 GB) using OpenCV (CPU). | FR‑001 |
| 1 | T1‑02 | Compute per‑frame Shannon entropy (`skimage.measure.shannon_entropy`). | FR‑001 |
| 1 | T1‑03 | Run MediaPipe Hands (CPU) → hand‑presence confidence per frame. | FR‑001 |
| 1 | T1‑04 | Compute lighting metrics (mean & std of grayscale intensity). | FR‑001 |
| 1 | T1‑05 | Pull camera metadata: timestamp (derived), exposure, focal length – record `NaN` when missing; later impute with column mean. | FR‑001 |
| 1 | T1‑06 | Aggregate per‑segment static feature vectors (mean ± std) → `data/static_features.csv`. | FR‑001 |
| 2 | T2‑01 | Compute **dynamic reliability** using the ACE‑Ego‑0 optical‑flow heuristic (implemented locally, CPU). | FR‑002 (target variable) |
| 2 | T2‑02 | Train Random Forest regressor (`n_estimators=200`, `random_state=42`). | FR‑002 |
| 2 | T2‑03 | Evaluate 5‑fold CV, bootstrap 95 % CI for $R^2$ (10 000 resamples). | SC‑001 |
| 2 | T2‑04 | Persist predictions → `data/static_predictions.csv` (conforms to `RegressionPrediction` schema). | FR‑002 |
| 2 | T2‑05 | Compute residuals = prediction − dynamic reliability → `data/static_residuals.csv`. | FR‑003 |
| 2 | T2‑06 | **Orthogonality assessment**: Pearson *r*, partial correlations, mutual information. | Methodological rigor |
| 2 | T2‑07 | **Power analysis** for regression: with **N = 300** segments (≥ 300 observations) we achieve ≥ 80 % power to detect Δ$R^2$ = 0.05 (α = 0.05, 8 predictors). | Methodology |
| 2 | T2‑08 | Record VIF; drop any feature with VIF > 5 before final model. | Methodology |
| 3 | T3‑01 | Compute optical‑flow statistics for windows **1 s, 3 s, 5 s, 10 s** using OpenCV Farneback (CPU). | FR‑004 |
| 3 | T3‑02 | Append temporal features to static vectors, retrain Random Forest for each window length. | FR‑004 |
| 3 | T3‑03 | Record $R^2$ per window, compute marginal Δ$R^2$, apply **Bonferroni correction** (α/4). | SC‑002 |
| 3 | T3‑04 | Compute VIF for combined feature set; drop any > 5 and re‑train. | Methodology |
| 4 | T4‑01 | **High‑reliability filter**: ROC analysis on a validation split selects a cutoff that maximizes Youden’s J for predicting reliability ≥ 0.4. Log chosen threshold. | FR‑007 |
| 4 | T4‑02 | **Sensitivity analysis**: Vary cutoff ±0.05 (prediction) and ±0.05 (RF‑std); report downstream VLA impact with 95 % CI. | Methodology |
| 4 | T4‑03 | Prepare three training sets: (a) full dynamic baseline, (b) uniform weighting, (c) static‑proxy filtered set from T4‑01. | FR‑005 |
| 4 | T4‑04 | Train **small OpenVLA variant** (CPU‑only, ≤ 3 000 episodes, 2‑layer transformer encoder). | FR‑005 |
| 4 | T4‑05 | Evaluate each VLA model on RoboCasa & RoboTwin (≥ 100 shared episodes each) → `results/vla_{variant}_{benchmark}.csv`. | FR‑005 |
| 4 | T4‑06 | Perform **equivalence test (TOST)** with margin ±2 % on success‑rate differences between Dynamic Baseline and Static‑Proxy models (per benchmark, 5 seeds). | FR‑006, SC‑003, SC‑004 |
| 4 | T4‑07 | **Power analysis for downstream comparison**: With 5 seeds × 100 episodes we have > 80 % power to detect ≤ 3 % gap at α = 0.05 given the ±2 % equivalence margin. | Methodology |
| 5 | T5‑01 | Log CPU time & peak RAM for each pipeline stage (`psutil`). Assert ≤ 10 min CPU per hour video and ≤ 6 GB RAM; if RAM exceeds, automatically down‑sample to **0.25 fps** and log adaptation. | SC‑005 |
| 5 | T5‑02 | Generate all tables & figures (`figures/`) and a markdown report (`report/summary.md`). | — |

All tasks are ordered so that **data download precedes any consumption**, **model training precedes evaluation**, and **figures are generated before manuscript hand‑off**.

## Contracts
The plan explicitly relies on the following JSON‑Schema files (all present in `contracts/`):
- `static_features.schema.yaml`
- `regression_prediction.schema.yaml`
- `temporal_window_features.schema.yaml`
- `static_residual.schema.yaml`
- `vla_experiment_result.schema.yaml`
- `equivalence_test_result.schema.yaml`

These schemas will be validated by the `validate-contracts` stage of the pipeline.

---


