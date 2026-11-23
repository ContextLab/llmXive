# Data Model: Quantization Robustness of Multi-Effect LoRA Adapters

## 1. Entity Definitions

### 1.1 SourceEffectRecord
A record representing a specific effect **before** merging.
- `effect_id`: string (e.g., "oil_painting")
- `source_path`: string (relative path to source LoRA file)
- `source_rank`: integer (computed via SVD on pre-merge matrix)
- `rank_tolerance`: float (tolerance used for SVD, e.g., 1e-5)
- `merge_protocol`: string (e.g., "WLA-OP")

### 1.2 ReferenceImage
A record for a ground-truth image used in CESR calculation.
- `image_id`: string (unique hash)
- `prompt`: string
- `effect_id`: string (or "distractor")
- `quantization_level`: string ("FP16")
- `image_path`: string
- `clip_embedding`: list[float] (512 or 768 dim)

### 1.3 GenerationResult
The core result of a generation run.
- `run_id`: string (UUID)
- `prompt`: string
- `effect_id`: string
- `quantization_level`: string ("FP16", "INT8", "INT4")
- `seed`: integer
- `image_path`: string
- `clip_similarity`: float (cosine similarity to prompt)
- `lpips_distance`: float (distance to FP16 baseline)
- `cesr_raw`: float (similarity to *other* effect references)
- `cesr_baseline`: float (mean similarity to *distractor* references)
- `cesr_normalized`: float (`cesr_raw - cesr_baseline`)
- `status`: string ("success", "skipped", "failed")
- `failure_reason`: string (optional, e.g., "MemoryLimitExceeded", "CatastrophicCollapse", "BackendUnavailable")
- `source_rank`: integer (intrinsic rank of the effect)

### 1.4 AnalysisMetric
Derived statistical outputs.
- `metric_name`: string ("quantization_effect", "rank_bleeding_correlation")
- `posterior_mean`: float
- `credible_interval_lower`: float
- `credible_interval_upper`: float
- `ess`: integer (Effective Sample Size)
- `is_underpowered`: boolean
- `is_unstable_posterior`: boolean
- `status`: string ("Valid", "Underpowered", "DescriptiveOnly")

## 2. Data Flow

1. **Input**: `config.yaml` (prompts, seeds), `data/models/` (source LoRAs).
2. **Process**:
   - Load Source LoRAs -> Compute SVD Ranks -> Save `data/subspace_ranks.json` (SourceRank).
   - Merge LoRAs (WLA-OP) -> Save `data/models/collection_lora.safetensors`.
   - Generate Baseline (FP16) -> Save `data/generated/baseline/`.
   - Generate Distractors -> Save `data/references/distractor_embeddings.json`.
   - Generate Quantized Outputs -> Compute Metrics (CLIP, LPIPS, CESR Normalized) -> Aggregate to `data/results.csv`.
3. **Output**: `data/results.csv`, `state/artifacts.yaml`, `data/analysis_results.json`.

## 3. Schema Validation

All data artifacts must conform to the schemas defined in `contracts/`.
- `data/subspace_ranks.json`: Validated against `contracts/subspace_ranks.schema.yaml`.
- `data/results.csv`: Validated against `contracts/dataset.schema.yaml`.
- `state/artifacts.yaml`: Validated against `contracts/state.schema.yaml`.
