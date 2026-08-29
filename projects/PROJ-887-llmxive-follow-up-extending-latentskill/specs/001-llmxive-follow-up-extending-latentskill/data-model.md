# Data Model: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Data Flow Diagram

```mermaid
graph TD
    A[Raw LoRA Weights (A/B)] -->|Download & Verify| B(data/raw/lora_weights/)
    B -->|Flatten & Normalize| C[data/processed/skill_index.npy]
    D[Task Descriptions] -->|Embed (MiniLM)| E[data/processed/query_embeddings.npy]
    C -->|Vector Search| F[Retrieval Output: Weights]
    F -->|Apply to Base LLM| G[Environment Logic (ALFWorld/Search-QA)]
    G -->|Binary Outcome| H[data/results/success_log.csv]
    H -->|Statistical Test| I[data/results/stats_raw.json]
    I -->|BH Correction| J[data/results/stats_report.json]
    K[Composite Validation Subset (CVS)] -->|Ground Truth Weights| L[Linearity Validation]
    L -->|Reconstruction Error| J
```

## Artifact Specifications

### 1. Raw Data (`data/raw/lora_weights/`)
- **Format**: Directory containing `.pt` or `.bin` files for each task.
- **Structure**:
  - `task_001/`: `adapter_config.json`, `adapter_model.bin` (or separate `A.pt`, `B.pt`).
  - `task_002/`: ...
- **Constraint**: Files must be unmodified downloads. Checksums recorded in `state/...yaml`.

### 2. Processed Vector Index (`data/processed/skill_index.npy`)
- **Format**: NumPy `.npy` file.
- **Content**:
  - `vectors`: 2D array `[N, D]` of float32, unit-normalized.
  - `metadata`: Dict or separate `.json` mapping indices to `task_id`, `task_description`, `original_file_path`.
- **Shape**: $N$ = number of adapters, $D$ = flattened dimension.

### 3. Composite Validation Subset (CVS)
- **Source**: A [deferred] split of the original LatentSkill dataset containing ground-truth weights for known composite tasks.
- **Usage**: Used for FR-007 (text-weight alignment) and SC-005 (reconstruction error). If absent, SC-005 falls back to Functional Linearity.

### 4. Evaluation Results (`data/results/success_log.csv`)
- **Columns**: `task_id`, `method` (NN, Mean, Weighted, Baseline, Zero-Shot), `run_id`, `success` (0/1), `latency_ms`.
- **Constraint**: One row per run. No aggregation performed at this stage.

### 5. Statistical Reports
- **`data/results/stats_raw.json`**: Raw p-values for each comparison.
- **`data/results/stats_report.json`**: Final report with BH-corrected p-values, effect sizes, and pass/fail flags against SC-001/SC-002. Includes `linearity_metric_type` ("geometric" or "functional").

## Schema Definitions

The following schemas define the structure of the output artifacts. The implementation must validate against these before proceeding. These contracts are **derived** from the definitions below.

### Skill Vector Metadata
```yaml
# contracts/skill_vector.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  task_id:
    type: string
    description: "Unique identifier for the skill task"
  task_description:
    type: string
    description: "Natural language description of the task"
  vector_path:
    type: string
    description: "Relative path to the flattened vector in skill_index.npy"
  normalization_method:
    type: string
    enum: ["L2"]
    description: "Normalization applied to the vector"
  original_weights_hash:
    type: string
    description: "SHA256 hash of the original A/B weight files"
required:
  - task_id
  - task_description
  - vector_path
  - normalization_method
  - original_weights_hash
```

### Evaluation Result Record
```yaml
# contracts/evaluation_result.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  task_id:
    type: string
  method:
    type: string
    enum: ["nearest_neighbor", "arithmetic_mean", "cosine_weighted", "baseline", "zero_shot"]
  run_id:
    type: integer
    description: "Sequence number of the run for this task/method pair"
  success:
    type: integer
    enum: [0, 1]
    description: "Binary outcome from environment logic"
  latency_ms:
    type: number
    description: "Time taken for skill selection (ms)"
  timestamp:
    type: string
    format: date-time
required:
  - task_id
  - method
  - run_id
  - success
  - latency_ms
```

### Statistical Report
```yaml
# contracts/stats_report.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  summary:
    type: object
    properties:
      total_tasks:
        type: integer
      total_runs:
        type: integer
      linearity_metric_type:
        type: string
        enum: ["geometric", "functional"]
        description: "Metric used for linearity validation"
      linearity_validated:
        type: boolean
        description: "True if linearity metric passed threshold"
      reconstruction_error:
        type: number
        description: "Max cosine distance for known composites (if geometric)"
  comparisons:
    type: array
    items:
      type: object
      properties:
        method:
          type: string
        baseline:
          type: string
        raw_p_value:
          type: number
        bh_corrected_p_value:
          type: number
        significant:
          type: boolean
        effect_size:
          type: number
      required:
        - method
        - baseline
        - raw_p_value
        - bh_corrected_p_value
        - significant
  sensitivity_analysis:
    type: object
    properties:
      top_k_values:
        type: array
        items:
          type: integer
      robustness_score:
        type: number
        description: "Variance of performance across k values"
required:
  - summary
  - comparisons
  - sensitivity_analysis
```

## Data Integrity & Hygiene

- **Checksums**: Every file in `data/raw/` and `data/processed/` must have a corresponding `.sha256` file.
- **Immutability**: Scripts must never overwrite files in `data/raw/`. Derivations in `data/processed/` must be new files.
- **Validation**: The `cli.py` entry point must run schema validation on `stats_report.json` before writing to disk.
