# Implementation Plan: llmXive follow‑up: extending “PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula”

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026‑10‑21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-llmxive-physs-filter/spec.md`

## Summary
The experiment tests whether a **post‑generation physics‑consistency filter** (PyBullet) applied to synthetic robotic‑manipulation videos can produce a curated dataset that enables downstream policy learning **comparable** (≤ 15 % gap) to the joint‑optimization approach of PhysisForcing. The pipeline consists of:

1. **Generation** – synthesize videos with the open‑source Wan2.1 model (FR‑001).  
2. **Physics filtering** – score each video with a headless PyBullet simulation (FR‑002).  
3. **Curation** – discard the bottom fraction of videos based on a 60‑th‑percentile raw score = 60 (FR‑003, SC‑001).  
4. **Training** – train an **≈ 50 M‑parameter** diffusion model on the curated set using CPU‑only PyTorch (FR‑004, FR‑007, SC‑005).  
5. **Evaluation** – compute R‑Bench and PAI‑Bench scores and validate with an independent MuJoCo check (FR‑005, FR‑008, SC‑002, SC‑006).  
6. **Statistical testing** – run Two‑One‑Sided Tests (TOST) with a 15 % equivalence margin, power ≥ 0.80, α = 0.05, d = 0.5 (FR‑006, FR‑013, SC‑003, SC‑004).  

All steps are orchestrated on a GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h per job). When a CPU‑only step fails, the runner automatically off‑loads to a free Kaggle GPU (GPU escape hatch) using `kaggle_offload: true`.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `torch==2.3.0` (CPU‑only)  
  - `pybullet==3.2.6` (headless)  
  - `mujoco==3.1.6` (CPU‑only)  
  - `datasets==2.18.0` (HuggingFace)  
  - `opencv-python==4.9.0`  
  - `pandas==2.2.2`  
  - `scipy==1.13.0` (TOST & diagnostics)  
  - `seaborn==0.13.2` (figures)  
- **Storage**: Files under `data/` (raw assets, generated videos, curated manifest, model checkpoints, reports).  
- **Testing**: `pytest==8.2.2` + contract tests in `tests/contract`.  
- **Target Platform**: Linux runner in GitHub Actions (CPU‑only).  
- **Constraints**:  
  - No CUDA libraries may be loaded (FR‑007).  
  - Training wall‑time ≤ 4 h (FR‑004, SC‑005).  
  - RAM usage ≤ 7 GB per task.  
- **Scale/Scope**: Generate a batch of **200** videos (configurable), retain the top 60 % after filtering, train the diffusion model for **10** epochs (empirically fits within 4 h on the free tier).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All random seeds are fixed (`src/utils/seeding.py`). Data downloads use deterministic HF URLs with SHA‑256 checksums recorded in the project state file. |
| II. Verified Accuracy | Every external citation (Wan2.1, PyBullet, MuJoCo, R‑Bench, PAI‑Bench) is taken from the verified URLs list provided in the spec. |
| III. Data Hygiene | Raw downloads are stored under `data/raw/` with checksums; every transformation writes a new file under `data/derived/` (e.g., filtered manifest, augmented videos). |
| IV. Single Source of Truth | All figures and tables are generated from JSON/CSV artifacts produced by the pipeline; no manual transcription. |
| V. Versioning Discipline | Artifact filenames embed a content hash (e.g., `curated_dataset_8a3f…csv`). The `state/projects/...yaml` file is updated after each run. |
| VI. Physics‑Consistency Verification | PyBullet filter discards videos whose raw score < 60 (the 60‑th percentile) as required by the spec and Constitution Principle VI. |
| VII. Benchmark Alignment | Evaluation exclusively uses **R‑Bench** and **PAI‑Bench**; results are compared against the PhysisForcing baseline and the unfiltered baseline, fulfilling Principle VII. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-physisforcin/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── video_sample.schema.yaml
    ├── physics_score.schema.yaml
    ├── curated_dataset.schema.yaml
    ├── config.schema.yaml
    ├── benchmark_result.schema.yaml
    ├── evaluation_result.schema.yaml
    └── dataset_schema.schema.yaml

code/
├── config.yaml                # populated at runtime
├── utils/
│   ├── verify_env.py          # FR‑021, FR‑007
│   ├── seeding.py
│   └── profile_memory.py
├── generation/
│   ├── download_wan_weights.py
│   └── generate_videos.py
├── filtering/
│   ├── pybullet_filter.py
│   └── mujoco_validator.py
├── augmentation/
│   └── geometric_augmenter.py
├── training/
│   └── train_diffusion.py      # ≈ 50 M‑parameter model
└── evaluation/
    ├── evaluate_benchmarks.py
    └── tost_equivalence.py

data/
├── raw/
│   ├── wan2.1/
│   └── pybullet_examples/
├── generated/
│   └── videos/
├── curated/
│   └── curated_dataset.csv
├── models/
│   └── diffusion_checkpoint.pt
└── reports/
    ├── benchmark_RBench.json
    ├── benchmark_PAIBench.json
    └── tost_results.json

tests/
├── contract/
│   └── test_contracts.py
└── unit/
    └── test_*.py
```

## Task List (mapping FR/SC)

| ID | Description | FR/SC addressed | Script |
|----|-------------|----------------|--------|
| T0 | **CPU‑Only Audit** – assert `torch.cuda.is_available() is False` | FR‑021, FR‑007 | `src/utils/verify_env.py` |
| T1 | Load `config.yaml` and expose parameters | FR‑023 | `src/utils/verify_env.py` |
| T2 | Download Wan2.1 weights & PyBullet example assets | — (data hygiene) | `download_wan_weights.py`, `download_pybullet_examples.py` |
| T3 | **Generate Videos** (batch size from config) | FR‑001 | `generate_videos.py` |
| T4 | Validate each generated video against `video_sample.schema.yaml` | FR‑014, FR‑024 | `pytest -q tests/contract/test_contracts.py::test_video_sample_schema` |
| T5 | **Run Physics Filter** (score 0‑100 → normalized 0‑1) | FR‑002, FR‑003, SC‑001 | `pybullet_filter.py` |
| T6 | Validate curated manifest against `curated_dataset.schema.yaml` | FR‑014 | `pytest -q tests/contract/test_contracts.py::test_curated_dataset_schema` |
| T7 | **Augment** (only if curated < 30) to reach n ≥ 30, flag `augmented:true` | Edge‑case handling, FR‑009 (implicit) | `geometric_augmenter.py` |
| T8 | **Train ≈ 50 M‑parameter diffusion model** (CPU‑only, mixed‑precision, batch = 4, epochs = 10) | FR‑004, FR‑007, SC‑005 | `train_diffusion.py` |
| T9 | Record training duration; fail if > 4 h | SC‑005 | `profile_memory.py` |
| T10 | **Validate filter with MuJoCo** (independent physics check) | FR‑008, SC‑006 | `mujoco_validator.py` |
| T11 | Compute Pearson correlation between PyBullet and MuJoCo scores | SC‑006 | `mujoco_validator.py` |
| T12 | **Evaluate on R‑Bench & PAI‑Bench** for filtered, unfiltered, and PhysisForcing baselines | FR‑005, SC‑002 | `evaluate_benchmarks.py` |
| T13 | Extract average physical‑consistency scores (SC‑002) | SC‑002 | `evaluate_benchmarks.py` |
| T14 | Compute performance gap vs. PhysisForcing baseline (SC‑003) | SC‑003 | `evaluate_benchmarks.py` |
| T15 | **Assumption checks** – Shapiro‑Wilk, Levene | FR‑013, FR‑017 | `tost_equivalence.py` (pre‑checks) |
| T16 | **Run TOST** with Bonferroni‑adjusted α (0.025) | FR‑006, FR‑013, SC‑004 | `tost_equivalence.py` |
| T17 | Assert p < 0.05 (SC‑004) | SC‑004 | `tost_equivalence.py` |
| T18 | **Generate final report** aggregating SC‑001‑SC‑006 | — | `generate_report.py` |
| T19 | Quickstart coverage – end‑to‑end run (see `quickstart.md`) | FR‑022 | CI script invoking T0‑T18 |
| T20 | Contract tests for all schemas (video, physics, curated, config, benchmark, evaluation, dataset) | FR‑014, FR‑024 | `pytest -q tests/contract/` |

## Success Criteria Mapping
| SC | Pipeline step(s) |
|----|------------------|
| SC‑001 | T5/T6 – retention rate recorded in `curated_dataset.csv`. |
| SC‑002 | T13 – average MuJoCo‑validated scores extracted from benchmark JSONs. |
| SC‑003 | T14 – % difference vs. PhysisForcing baseline (must be ≤ 15 %). |
| SC‑004 | T17 – p‑value < 0.05 after Bonferroni correction. |
| SC‑005 | T9 – training time ≤ 4 h. |
| SC‑006 | T11 – Pearson r < 0.95 between PyBullet and MuJoCo scores. |

---
