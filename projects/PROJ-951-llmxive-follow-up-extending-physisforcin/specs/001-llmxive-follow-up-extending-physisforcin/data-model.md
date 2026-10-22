# Data Model: llmXive follow‑up: extending “PhysisForcing”

## Overview
The pipeline manipulates five core entities. Each entity has a dedicated contract schema under `specs/…/contracts/`.

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **VideoSample** | A synthetic robotic‑manipulation video with generation metadata. | `video_id`, `prompt`, `video_path`, `generation_timestamp`, `physics_score`, `filter_status`, `augmented` |
| **CuratedDataset** | Manifest of all `VideoSample`s that passed the PyBullet filter (and any augmentations). | `dataset_id`, `total_samples`, `threshold_percentile`, `threshold_score`, `samples` (list of `VideoSampleRef`), `created_at`, `augmented`, `augmentation_method` |
| **TrainedModel** | Checkpoint of the distilled diffusion model and its training metadata. | `model_id`, `checkpoint_path`, `training_epochs`, `final_train_loss`, `seed`, `timestamp` |
| **BenchmarkResult** | Evaluation metrics for a given model on a benchmark. | `result_id`, `model_id`, `r_bench_score`, `pai_bench_score`, `downstream_success_rate`, `mujoco_correlation`, `tost_p_value`, `equivalence_flag`, `training_duration` |
| **TOSTResult** | Outcome of the equivalence test between two models on a benchmark. | `model_id_a`, `model_id_b`, `benchmark_name`, `equivalence_margin`, `p_value`, `equivalent` |

All files reside under `data/`:

```text
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
```

## Normalization Note
* PyBullet produces raw scores on a **0‑100** scale.  
* The filter normalizes them to **0‑1** before writing to `physics_score.schema.yaml`.  
* The 60‑th percentile raw score = 60 (source 2506.09162) corresponds to a normalized threshold of **0.60**; this value is stored as `threshold_score` in the curated manifest.

## Data Hygiene
* **Checksums** – Every raw download is verified via SHA‑256; hashes are recorded in the project state file.  
* **Immutability** – Raw files are never overwritten; transformations (filtering, augmentation) produce new files with distinct filenames.  
* **Versioning** – Artifact filenames embed a content hash (e.g., `curated_dataset_8a3f…csv`). The state file is updated after each run.

## Single Source of Truth
All downstream figures, tables, and statistical statements are derived directly from the JSON/CSV artifacts listed above; no manual transcription occurs.

---
