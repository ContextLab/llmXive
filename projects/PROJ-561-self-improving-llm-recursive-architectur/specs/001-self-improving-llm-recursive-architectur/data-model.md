# Data Model: Self-improving LLM

## Entities

### ModelCheckpoint

Represents a trained model instance.

| Attribute           | Type     | Description                                       |
|---------------------|----------|---------------------------------------------------|
| `cycle_number`      | Integer  | The iteration number of the refinement cycle.       |
| `parameter_count`   | Integer  | Total number of parameters in the model.           |
| `architecture_modification` | String  | Description of the architectural change applied.|
| `training_time`     | Float    | Time taken to train the model (seconds).            |
| `flops`              | Float    | Number of floating-point operations performed during training.|

### PerformanceMetric

Represents evaluation results.

| Attribute        | Type     | Description                                  |
|------------------|----------|----------------------------------------------|
| `cycle_number`   | Integer  | The iteration number of the refinement cycle.|
| `benchmark_name` | String   | Name of the benchmark (GSM8K, ARC-Challenge, Wikitext-2). |
| `accuracy_or_ppl`| Float    | Accuracy (for reasoning) or Perplexity (for Wikitext-2). |
| `p_value_vs_baseline` | Float  | P-value from paired bootstrap test.            |

### RefinementCycle

Represents one iteration of the pipeline.

| Attribute          | Type     | Description                                  |
|--------------------|----------|----------------------------------------------|
| `cycle_number`     | Integer  | The iteration number of the refinement cycle.|
| `pre_modification_params` | Integer | Parameter count before modification        |
| `post_modification_params`|Integer|Parameter count after modifcation            |
| `training_duration`| Float    | Training time for this cycle                 |
| `evaluation_results`| List     | List of PerformanceMetric objects.          |
| `success_status`   | Boolean  | Indicates whether the cycle completed successfully.|

## Data Flow

1.  **Raw Data**: OpenWebText, GSM8K, ARC-Challenge, Wikitext-2 (downloaded from Hugging Face Datasets).
2.  **Processed Data**: Training data subset (OpenWebText) for each cycle; evaluation datasets preprocessed for benchmarking.
3.  **Model Checkpoints**: Saved after each training iteration.
4.  **Performance Metrics**: Calculated and stored after evaluation.
5. **Trajectory Data**: Aggregated performance metrics across cycles to analyze trends.

## Schema Definitions (contracts/trajectory_entry.schema.yaml)

The `trajectory_entry.schema.yaml` defines the structure of the output JSON, including `plateau_cycle_index` and `trade_off_metrics`.