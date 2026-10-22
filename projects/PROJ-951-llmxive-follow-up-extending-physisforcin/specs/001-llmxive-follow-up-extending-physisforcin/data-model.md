# Data Model: llmXive follow‑up: extending "PhysisForcing"

## Overview

Four core entities, each with a contract schema under `specs/001-llmxive-physs-filter/contracts/`.

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **VideoSample** | A Wan2.1‑generated robotic‑manipulation video with generation metadata and filter outcome. | `video_id`, `prompt`, `video_path`, `generation_timestamp`, `physics_score`, `filter_status`, `condition` |
| **PhysicsScore** | Per‑video PyBullet filter output (raw 0–100 internally; normalized 0–1 when written). | `video_id`, `physics_score`, `trajectory_continuity`, `contact_conservation`, `simulation_status`, `passed_filter` |
| **CuratedDataset** | Manifest of VideoSamples per condition (filtered / unfiltered). | `dataset_id`, `condition`, `total_samples`, `threshold_percentile`, `threshold_score`, `discard_percent`, `retention_rate`, `samples`, `created_at` |
| **TrainedModel** | ≈ a multi‑million‑parameter distilled diffusion model checkpoint + training metadata. (No formal schema provided; validated informally via training logs.) | `model_id`, `condition`, `checkpoint_path`, `training_epochs`, `final_train_loss`, `training_duration_seconds`, `seed`, `timestamp` |
| **BenchmarkResult / EvaluationResult** | R‑Bench / PAI‑Bench / MuJoCo scores and TOST outcome per model. | `model_id`, `baseline_model_id`, `r_bench_score`, `pai_bench_score`, `mujoco_physics_score`, `sample_count`, `tost_p_value`, `test_used`, `equivalence_margin`, `equivalent`, `performance_gap_percent`, `pybullet_mujoco_correlation` |

## Storage Layout

```text
data/
├── raw/
│   └── wan21_videos/          # immutable downloads + SHA‑256 checksums
├── derived/
│   ├── video_samples/         # one VideoSample JSON per video
│   ├── physics_scores/        # one PhysicsScore JSON per video
│   ├── manifests/             # curated_*.json, unfiltered_*.json
│   └── models/                # diffusion checkpoints (filtered / unfiltered)
└── reports/                   # benchmark_*.json, tost_results.json, final_summary.md
```

## Score Normalization

- PyBullet produces raw scores on a **0–100** scale.
- Scores are **normalized to 0–1** when written to `physics_score.schema.yaml` / `video_sample.schema.yaml`.
- The curated minimum is the **60th percentile** with raw score = 60 (source: 2506.09162, https://arxiv.org/abs/2506.09162) → normalized threshold **0.60**, stored as `threshold_score`; any video with normalized < 0.60 is discarded. The `filter_discard_percent` (default 40) is recorded for reporting only.

## Data Hygiene

- Every raw file SHA‑256‑checksummed; hashes recorded in the project state file.
- Raw data never modified in place; all transformations write new files under `data/derived/`.
- No PII in committed data.

## Single Source of Truth

Every figure, statistic, and conclusion in `final_summary.md` is read programmatically from the JSON/CSV artifacts above (SC‑001–SC‑006); no hand‑typed derived numbers.
