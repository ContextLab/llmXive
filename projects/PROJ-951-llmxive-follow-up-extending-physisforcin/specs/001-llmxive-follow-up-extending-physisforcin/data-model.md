# Data Model: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

## Entities & Relationships

### VideoSample
- **Description**: A single generated video clip with associated metadata.
- **Attributes**:
  - `id`: Unique identifier (UUID).
  - `prompt`: Text prompt used for generation.
  - `video_path`: Relative path to MP4 file in `data/raw/`.
  - `physics_score`: Float (0.0 - 1.0) from PyBullet filter.
  - `pass_status`: Boolean (True if score ≥ 60th percentile).
  - `generation_timestamp`: ISO 8601 string.
  - `generation_status`: "success", "failed", "crash".

### CuratedDataset
- **Description**: The collection of `VideoSample` entities that passed the filter.
- **Attributes**:
  - `dataset_id`: UUID.
  - `total_samples`: Integer.
  - `retention_rate`: Float (percentage retained).
  - `min_score`: Float (minimum score in curated set).
  - `samples`: List of `VideoSample` references.

### TrainedModel
- **Description**: The 50M parameter diffusion model trained on `CuratedDataset`.
- **Attributes**:
  - `model_id`: UUID.
  - `architecture`: String (e.g., "UNet-Diffusion-50M").
  - `training_epochs`: Integer.
  - `final_loss`: Float.
  - `checkpoint_path`: Path to model weights.
  - `training_config`: JSON object of hyperparameters.

### BenchmarkResult
- **Description**: Evaluation metrics for a model on R-Bench and PAI-Bench.
- **Attributes**:
  - `model_id`: Reference to `TrainedModel` or `BaselineModel`.
  - `r_bench_score`: Float.
  - `pai_bench_score`: Float.
  - `sample_count`: Integer (n).
  - `tost_p_value`: Float (from equivalence test).
  - `equivalence_flag`: Boolean (True if gap ≤ 15% and p < 0.05).

## Data Flow Diagram

1. **Generation**: `Wan2.1` -> `data/raw/video_*.mp4` + `data/raw/metadata.jsonl`.
2. **Filtering**: `data/raw/*` -> `PyBullet Filter` -> `data/curated/scores.parquet` + `data/curated/video_*.mp4`.
3. **Validation**: `data/curated/*` -> `MuJoCo Validator` -> `data/validation/mujoco_scores.parquet`.
4. **Training**: `data/curated/*` + `config.yaml` -> `Train Loop` -> `data/models/model_*.pt`.
5. **Evaluation**: `data/models/*` + `data/validation/*` -> `R-Bench/PAI-Bench` -> `data/results/evaluation.json`.

## Storage Schema

- **Raw Videos**: `data/raw/` (MP4).
- **Metadata**: `data/raw/metadata.jsonl` (JSON Lines).
- **Curated Data**: `data/curated/` (MP4 + `scores.parquet`).
- **Validation**: `data/validation/` (Parquet).
- **Models**: `data/models/` (PyTorch `.pt` files).
- **Results**: `data/results/` (JSON).
