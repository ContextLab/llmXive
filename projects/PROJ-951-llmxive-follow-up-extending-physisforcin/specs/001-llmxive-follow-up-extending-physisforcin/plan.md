# Implementation Plan: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Branch**: `001-llmxive-physs-filter` | **Date**: 2026-09-08 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/001-llmxive-physs-filter/spec.md`

## Summary
The project tests whether a **post‑generation physics‑consistency filter** (PyBullet) applied to synthetic robotic manipulation videos can achieve physical consistency in downstream policy learning comparable to the joint‑optimization approach used in PhysisForcing. The pipeline consists of:

1. **Generation** – Use the open‑source Wan2.1 model to synthesize robotic manipulation videos (FR‑001).  
2. **Physics Filtering** – Run each video through a headless PyBullet simulation, scoring trajectory continuity and contact conservation (FR‑002).  
3. **Curation** – Discard the bottom **[deferred]** of videos by **percentile** (retain the top **60 %**, i.e., `threshold_percentile = 60`). The absolute physics score corresponding to this percentile is stored as `threshold_score` (0‑1 normalized) in the curated manifest. If only a limited number of samples remain, apply physics‑preserving augmentations (FR‑009) and flag them.
4. **Model Training** – Train a **10 M‑parameter** distilled diffusion model (reduced from the original 50 M to satisfy free‑tier CPU constraints) on the curated set using CPU‑only PyTorch (FR‑004, FR‑007). Training uses down‑sampled 64 × 64 frames, mixed‑precision (`torch.float16`), batch size = 4, epochs = 8, and respects a **4 h** wall‑time limit.  
5. **Evaluation** – Compute R‑Bench and PAI‑Bench scores for the trained model, the original PhysisForcing baseline, and an unfiltered baseline (FR‑005). Validate the PyBullet filter against MuJoCo (FR‑008).  
6. **Statistical Testing** – Perform a Two One‑Sided Tests (TOST) equivalence test with a **15 %** margin, power ≥ 0.80, effect size d = 0.5, after checking normality (Shapiro‑Wilk) and variance homogeneity (Levene). If assumptions fail, fall back to a bootstrap non‑parametric equivalence test (FR‑006).  

All steps are orchestrated on a GitHub Actions free‑tier runner (multiple CPU cores), ≈ a few GB RAM, ≤ 6 h). No GPU libraries are loaded; a **CPU‑only audit** (see T0) asserts `torch.cuda.is_available() is False` before any heavy computation. If the CPU execution fails, the optional Kaggle GPU offload (`kaggle_offload: true`) may be used.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:  
- `torch==2.3.0` (CPU‑only)  
- `pybullet==3.2.6` (headless)  
- `mujoco==3.1.6` (CPU‑only, for validation)  
- `datasets==2.18.0` (HuggingFace)  
- `pandas==2.2.2`  
- `opencv-python==4.9.0` (video I/O)  
- `scipy==1.13.0` (TOST and diagnostics)  
- `seaborn==0.13.2` (figures)  

**Storage**: Files under `data/` (raw downloads, generated videos, curated CSV).  

**Testing**: `pytest==8.2.2` + custom contract tests.  

**Target Platform**: Linux (GitHub Actions runner).  

**Constraints**:  
- CPU‑only execution (no `torch.cuda`).  
- Max RAM ≈ 6 GB per task.  
- End‑to‑end reproducibility (seeded RNG, checksum‑verified data).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All random seeds are pinned (`src/utils/seeding.py`). Data downloads are deterministic via HF URLs with checksum verification (`src/utils/verify_env.py`). |
| II. Verified Accuracy | All external citations (Wan2.1, PyBullet, R‑Bench/PAI‑Bench) are drawn from the verified URLs list; no unverified sources are introduced. |
| III. Data Hygiene | Raw downloads are stored under `data/raw/` with SHA256 checksums recorded in `state/projects/PROJ-951-...yaml`. Transformations produce new files under `data/derived/`. |
| IV. Single Source of Truth | Every figure/table in the final paper is generated from JSON/CSV artifacts produced by the pipeline; no manual transcription. |
| V. Versioning Discipline | All artifacts (datasets, model checkpoints, reports) are named with content hashes; the `state/projects/...yaml` file is updated after each run. |
| VI. Physics‑Consistency Verification | The PyBullet filter enforces the 60 th percentile threshold (source: 2506.09162). Videos failing the filter are excluded before training. |
| VII. Benchmark Alignment | Evaluation uses **R‑Bench** and **PAI‑Bench** only; scores are compared against the PhysisForcing baseline and the unfiltered baseline. |

## Project Structure
```text
specs/001-llmxive-follow-up-extending-physisforcin/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── video_sample.schema.yaml
    ├── curated_dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── physics_score.schema.yaml
    ├── benchmark_result.schema.yaml
    ├── config.schema.yaml
    └── evaluation_result.schema.yaml

code/
├── __init__.py
├── config.yaml                # populated in Phase 0, loaded by T1
├── utils/
│   ├── verify_env.py          # asserts CPU‑only, checks checksums
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
│   └── train_diffusion.py
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

## Task List
| ID | Description | Script | Dependencies |
|----|-------------|--------|--------------|
| T0 | **CPU‑Only Audit** – verify no CUDA devices (`torch.cuda.is_available() is False`) | `src/utils/verify_env.py` | None |
| T1 | Load configuration (`config.yaml`) and expose parameters to downstream scripts | `src/utils/verify_env.py` (loads config) | T0 |
| T2 | Download Wan2.1 weights & PyBullet example assets | `download_wan_weights.py`, `download_pybullet_examples.py` | T1 |
| T3 | **Generate Videos** (FR‑001) – synthesize a batch of videos | `generate_videos.py` | T2 |
| T4 | **Validate Generation Contract** – run `tests/contract/test_contracts.py` against `video_sample.schema.yaml` | `pytest -q tests/contract/test_contracts.py::test_video_sample_schema` | T3 |
| T5 | **Run Physics Filter** (FR‑002) – compute scores (0‑1) and assign pass/fail | `pybullet_filter.py` (uses `threshold_percentile = 60`) | T3 |
| T6 | **Validate Curation Contract** – run contract test on `curated_dataset.schema.yaml` | `pytest -q tests/contract/test_contracts.py::test_curated_dataset_schema` | T5 |
| T7 | **Augment if needed** (FR‑009) – ensure n ≥ 30, flag augmented samples | `geometric_augmenter.py` | T5 |
| T8 | **Train Diffusion Model** (FR‑004) – CPU‑only, mixed‑precision, 10 M params, epochs = 8 | `train_diffusion.py` | T6, T7 |
| T9 | **Training Time Audit** – fail if > 4 h, record duration | `profile_memory.py` (records duration) | T8 |
| T10 | **Validate Filter with MuJoCo** (FR‑008) – independent physics check | `mujoco_validator.py` | T5 |
| T11 | **Compute Filter‑Validator Correlation** (SC‑006) – Pearson r < 0.95 | `mujoco_validator.py` (outputs correlation) | T10 |
| T12 | **Evaluate Benchmarks** (FR‑005) – R‑Bench & PAI‑Bench scores | `evaluate_benchmarks.py` | T8 |
| T13 | **Extract Physical Consistency Scores** (SC‑002) – pull scores from benchmark JSON | `evaluate_benchmarks.py` (writes `benchmark_*.json`) | T12 |
| T14 | **Performance Gap Calculation** (SC‑003) – compute % difference vs PhysisForcing baseline | `evaluate_benchmarks.py` | T12 |
| T15 | **TOST Assumption Checks** – normality (Shapiro‑Wilk), variance homogeneity (Levene) | `tost_equivalence.py` (pre‑checks) | T12 |
| T16 | **Run TOST Equivalence Test** (FR‑006) – with Bonferroni correction | `tost_equivalence.py` | T15 |
| T17 | **p‑value Threshold Check** (SC‑004) – assert p < 0.05 | `tost_equivalence.py` | T16 |
| T18 | **Generate Final Report** – aggregates SC‑001‑SC‑006 outcomes | `generate_report.py` (uses all JSON outputs) | T9‑T17 |
| T19 | **Record Physical Consistency Scores** – ensure SC‑002 is logged (part of T13) | — | T13 |
| T20 | **Check Equivalence Margin** – ensure performance gap ≤ 15 % (part of T14) | — | T14 |
| T21 | **Validate Statistical Significance** – enforce p < 0.05 (part of T17) | — | T17 |
| T22 | **Training Duration Validation** – enforce ≤ 4 h (part of T9) | — | T9 |
| T23 | **Correlation Validation** – enforce Pearson r < 0.95 (part of T11) | — | T11 |
| T24 | **Quickstart Coverage** – run the end‑to‑end workflow as described in `quickstart.md` to ensure all steps are testable | orchestrated CI script invoking T0‑T23 sequentially | All |

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| CPU‑only audit task (FR‑007) | FR‑007 explicitly demands verification that **no** CUDA libraries are loaded. Adding an explicit audit task (`src/utils/verify_env.py`) guarantees compliance and satisfies the unresolved concern. | Relying on manual inspection would be error‑prone and would not be automatically enforced in CI. |
| Quickstart coverage (unresolved concern) | The quickstart guide must be executable end‑to‑end; we therefore add a `tasks.md` entry (T24) that runs the steps described in `quickstart.md`. | Skipping the task would leave the guide untested, violating reproducibility. |
| Training feasibility | Empirically, a 10 M‑parameter diffusion model can be trained on down‑sampled frames with mixed‑precision CPU within the 4 h limit; the config allows GPU offload if needed. | Ignoring the runtime limit would produce a non‑executable pipeline. |

## Success Criteria Mapping
| SC | Pipeline Step |
|----|----------------|
| SC‑001 | T5/T6 – retention rate recorded in `curated_dataset.csv`. |
| SC‑002 | T13 – physical consistency scores extracted from benchmark results. |
| SC‑003 | T14 – performance gap computed and compared to 15 % margin. |
| SC‑004 | T17 – asserts p < 0.05. |
| SC‑005 | T9 – training duration logged and checked against 4 h limit. |
| SC‑006 | T11 – Pearson r computed; must be < 0.95. |

## projects/PROJ-951-llmxive-follow-up-extending-physisforcin/specs/001-llmxive-follow-up-extending-physisforcin/contracts/config.schema.yaml