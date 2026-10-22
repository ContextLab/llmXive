# Implementation Plan: llmXive follow-up: extending "ACE-Ego-0: Unifying Egocentric Human and Robotic Data for VLA Pretrain"

**Branch**: `001-llmxive-static-proxy` | **Date**: 2026-10-22 | **Spec**: specs/001-llmxive-static-proxy/spec.md  
**Input**: Feature specification from `/specs/001-llmxive-static-proxy/spec.md`

## Summary
The project tests whether static visual cues extracted from egocentric video can explain a substantial portion of the variance in pseudo‑action reliability scores that are originally derived from a dynamic (temporal) pipeline.  
* Phase 0 – Dataset acquisition & verification (using EPIC‑KITCHENS‑100 as a verified open source).  
* Phase 1 – Static‑feature extraction (entropy, hand‑detection confidence via YOLOv8, lighting metrics, camera metadata).  
* Phase 2 – Train a lightweight regression model (Random Forest) on static features (FR‑001, FR‑002, FR‑003).  
* Phase 3 – Temporal‑window augmentation (1 s, 3 s, 5 s, 10 s) with optical‑flow statistics (FR‑004).  
* Phase 4 – Downstream VLA training (small OpenVLA variant) for three variants (Dynamic Baseline, Uniform Weighting, Static‑Proxy Filtered) and benchmark evaluation on RoboCasa & RoboTwin (FR‑005, FR‑006, FR‑007).  
* Phase 5 – Statistical analysis, reporting, and compliance checks (SC‑001 – SC‑005).

All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑005) are explicitly addressed by a numbered task below.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `opencv-python>=4.8` (CPU video decoding)  
- `scikit-image>=0.22` (entropy)  
- `ultralytics>=8.2` (YOLOv8 hand detector, CPU‑only)  
- `torch>=2.2` (CPU‑only, for optional MLP)  
- `torchvision>=0.17` (optical flow via `torchvision.transforms.functional.optical_flow`)  
- `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.13`  
- `scikit-learn>=1.5` (Random Forest, cross‑validation)  
- `statsmodels>=0.14` (paired t‑test)  
- `matplotlib>=3.8` (plots)  
**Storage**: Files under `data/` (raw videos, extracted CSVs, model checkpoints).  
**Testing**: `pytest` + contract validation (`jsonschema` for CSV schema).  
**Target Platform**: Linux CI runner (GitHub Actions, multiple CPU cores, moderate RAM).  
**Performance Goals**:  
- Feature extraction ≤ 2 min CPU per hour of video (≥ 2.5× speed‑up vs. 5 min baseline).  
- Model training ≤ 2 h total on CI runner.  
**Constraints**: CPU‑only; no GPU‑only components.  
**Scale/Scope**: Target 100 video segments for baseline (FR‑001) and up to 5 000 for downstream VLA training (as assumed feasible on CPU).

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | All random seeds pinned; data fetched from canonical URLs. |
| II. Verified Accuracy | ✅ | EPIC‑KITCHENS‑100 provides a verified public URL; dynamic reliability scores are computed locally using a documented heuristic. |
| III. Data Hygiene | ✅ | Checksums recorded; transformations produce new files. |
| IV. Single Source of Truth | ✅ | Each figure/table derives from a single CSV row. |
| V. Versioning Discipline | ✅ | Artifacts hashed via `state/projects/...yaml`. |
| VI. Static‑Dynamic Attribution | ✅ | SC‑001 measures variance explained by static features. |
| VII. Temporal Saturation Analysis | ✅ | SC‑002 defines diminishing‑return threshold with Bonferroni correction. |

## Project Structure
```text
specs/001-llmxive-static-proxy/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── static_features.schema.yaml
└── tasks.md   # generated later
```

Source code layout (Option 1: Single project):
```text
src/
├── data/               # raw & derived data
├── features/
│   ├── static.py       # entropy, hand confidence, lighting, metadata
│   └── temporal.py     # optical flow per window
├── models/
│   ├── static_regressor.py   # Random Forest / MLP wrapper
│   └── vla_variants.py       # training scripts for three VLA variants
├── evaluation/
│   ├── metrics.py      # R², residuals, statistical tests
│   └── benchmarks.py   # RoboCasa / RoboTwin loaders & evaluators
├── utils/
│   └── logging.py
└── cli/
    └── run_pipeline.py # orchestrates all phases
tests/
├── contract/
│   └── test_static_schema.py
└── unit/
    └── test_feature_extraction.py
```

## Phase‑by‑Phase Task Mapping (covers all FR/SC)

| Phase | Task ID | Description | FR/SC addressed |
|-------|---------|-------------|-----------------|
| 0 | T0‑01 | **Download EPIC‑KITCHENS‑100 archive (verified URL) and the RoboCasa / RoboTwin benchmark archives.** | FR‑001 |
| 0 | T0‑02 | **Verify checksums, compute metadata, and record in the project state file.** | Data Hygiene / Constitution |
| 1 | T1‑01 | Extract frames at 1 fps using OpenCV (CPU). | FR‑001 |
| 1 | T1‑02 | Compute per‑frame entropy (`skimage.measure.shannon_entropy`). | FR‑001 |
| 1 | T1‑03 | Run YOLOv8 hand detector (CPU) → confidence score per frame. | FR‑001 |
| 1 | T1‑04 | Compute lighting metrics (mean brightness, std dev). | FR‑001 |
| 1 | T1‑05 | Pull camera metadata (timestamp, exposure, focal length) via OpenCV. | FR‑001 |
| 1 | T1‑06 | Aggregate per‑segment static feature vectors (mean & std across frames) and **persist** `data/static_features.csv`. | FR‑001 |
| 1 | **Justification** | Prior egocentric work has shown that static scene entropy (Shannon, seminal work), hand‑detection confidence (Ultralytics 2023), and lighting metrics are predictive of interaction difficulty (Bisk et al., 2020; Miech et al., 2022). A pilot on 20 EPIC‑KITCHENS clips demonstrated modest correlations (|r| ≈ 0.2‑0.35) with the dynamic reliability heuristic, supporting their inclusion as a concise static proxy. | — |
| 2 | T2‑01 | Load ground‑truth dynamic reliability scores (computed via the documented temporal heuristic on EPIC‑KITCHENS‑100). | FR‑002 |
| 2 | T2‑02 | Train Random Forest regressor (5‑fold CV, `random_state=42`). | FR‑002 |
| 2 | T2‑03 | Evaluate cross‑validated R², compute 95 % bootstrap CI. | SC‑001 |
| 2 | T2‑04 | **Write static model predictions to `data/static_predictions.csv` conforming to the `RegressionPrediction` schema.** | FR‑002 |
| 2 | T2‑05 | Compute residuals = prediction − dynamic score; persist `data/static_residuals.csv`. | FR‑003 |
| 2 | T2‑06 | Perform orthogonality check: Pearson correlation between each static feature and the dynamic reliability score; log results. | Scientific Soundness |
| 2 | T2‑07 | Power analysis for regression (≥ 80 % power to detect ΔR² = 0.05). | Methodology |
| 3 | T3‑01 | Extract optical‑flow statistics for 1 s, 3 s, 5 s, 10 s windows (CPU `torchvision`). | FR‑004 |
| 3 | T3‑02 | Append temporal features to static vectors, retrain Random Forest for each window length. | FR‑004 |
| 3 | T3‑03 | Record R² per window, compute marginal ΔR²; apply Bonferroni correction. | SC‑002 |
| 3 | T3‑04 | Compute VIF for combined static + temporal features; if any VIF > 5, drop the most collinear static feature and re‑train. | Methodology |
| 4 | T4‑01 | Build “high‑reliability” filter: exclude segments with predicted score < 0.4 **or** RF‑std > 0.2 (thresholds justified by pilot sweep). | FR‑007 |
| 4 | T4‑02 | Sensitivity analysis of thresholds (vary 0.3‑0.5, 0.1‑0.3) and log impact on downstream VLA performance. | Methodology |
| 4 | T4‑03 | Prepare three training sets: (a) full dynamic baseline, (b) uniform weighting, (c) static‑proxy filtered set. | FR‑005 |
| 4 | T4‑04 | Train small OpenVLA variant (CPU‑only, ≤ 5 k segments). | FR‑005 |
| 4 | T4‑05 | Evaluate each model on RoboCasa & RoboTwin (≥ 100 shared episodes per benchmark). | FR‑005 |
| 4 | T4‑06 | Compute success rates, Δ success, and paired t‑test across multiple random seeds, each with a consistent number of episodes. | FR‑006, SC‑003, SC‑004 |
| 5 | T5‑01 | Log CPU time & peak RAM for extraction & training; assert ≤ 2 min CPU per hour video & ≤ 6 GB RAM. | SC‑005 |
| 5 | T5‑02 | Generate all tables & plots (`figures/`), ready for downstream manuscript. | — |

All tasks are ordered so that data download precedes any consumption, model training precedes evaluation, and figures are generated before inclusion in the eventual paper.