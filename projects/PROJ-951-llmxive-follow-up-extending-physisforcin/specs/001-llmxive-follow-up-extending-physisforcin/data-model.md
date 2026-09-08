# Data Model: llmXive follow-up: extending "PhysisForcing"

## Overview
The pipeline manipulates three core entities:

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **VideoSample** | A single synthetic robotic manipulation video (MP4) together with generation metadata. | `video_id` (str), `prompt` (str), `video_path` (str), `generation_timestamp` (ISO8601), `physics_score` (float, **0 – 1**, normalized), `filter_status` (`"pass"` / `"fail"` / `"error"`), `augmented` (bool) |
| **CuratedDataset** | CSV manifest of all `VideoSample`s that survived the filter (and any augmentations). | `dataset_id`, `total_samples`, `threshold_percentile` (numeric, e.g., 60), `threshold_score` (absolute score 0‑1), `samples` (list of `VideoSampleRef`), `created_at`, `augmented`, `augmentation_method` |
| **TrainedModel** | Serialized checkpoint of the distilled diffusion model and its training metadata. | `model_id` (str), `checkpoint_path` (str), `training_epochs` (int), `final_train_loss` (float), `seed` (int), `timestamp` (ISO8601) |
| **BenchmarkResult** | Evaluation metrics for a given model on a benchmark. | `model_id`, `benchmark_name` (`"R-Bench"` / `"PAI-Bench"`), `score` (float), `score_std` (float), `num_samples` (int) |
| **TOSTResult** | Outcome of the equivalence test between two models on a benchmark. | `model_id_a`, `model_id_b`, `benchmark_name`, `equivalence_margin` (float), `p_value` (float), `equivalent` (bool) |

All files are stored under `data/` with the following layout:

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
All **physics scores** produced by the PyBullet filter are **normalized to the interval [0, 1]**. The filtering step retains videos whose score is at or **above the 60 th percentile** of the batch distribution; the corresponding absolute threshold is stored in the `threshold_score` field of the curated manifest. This ensures consistency between the percentile‑based filter and the absolute score recorded.

## Entities
(Details omitted for brevity; full field definitions are in the contract schemas.)

## Data Hygiene
- Raw data downloads **must** be checksummed **never** altered in place — transformations produce new files.  
- **Version** of each artifact is tracked by content hash (e.g., `curated_dataset_8a3f…csv`).  

## Single Source of Truth (​S​S​O​T ​Principle ​II ​III ​IV) ​​ ​  ​  ​ ​ ​ ​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​ ​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
