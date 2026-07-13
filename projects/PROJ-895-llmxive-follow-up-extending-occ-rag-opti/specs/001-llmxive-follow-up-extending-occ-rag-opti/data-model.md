# Data Model: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

## Entities & Relationships

### Core Entities

1. **ModelParameter**
   - `layer_id` (int): Layer index in the model.
   - `param_id` (str): Unique identifier for parameter (e.g., "layer_3.head_2.weight").
   - `param_type` (str): "attention_head" or "feed_forward_neuron".
   - `sensitivity_score` (float): Z-score of performance drop when masked.
 - `is_critical` (bool): True if in top **[deferred]** by sensitivity.

2. **FaithfulnessRecord**
   - `sample_id` (str): Unique ID for QA sample.
   - `model_type` (str): "original", "pruned", or "random_pruned".
   - `con_fiqa_accuracy` (float): ConFiQA accuracy score.
   - `citation_precision` (float): Citation precision score.
   - `context_faithfulness_score` (float): Weighted sum of above.

3. **SensitivityExperiment**
   - `experiment_id` (str): Unique ID for masking run.
   - `masking_unit` (str): "head" or "neuron".
   - `baseline_type` (str): "random_subset" (size-matched).
   - `delta_faithfulness` (float): Change in faithfulness score.

### Relationships

- `ModelParameter` → `SensitivityExperiment`: Many-to-one (each parameter participates in multiple experiments).
- `FaithfulnessRecord` → `ModelParameter`: Indirect (faithfulness computed from model using parameters).
- `SensitivityExperiment` → `FaithfulnessRecord`: One-to-many (each experiment produces multiple faithfulness records).

## Data Flow

1. **Raw Data**: OCC-RAG model weights + synthetic QA corpus (JSONL).
2. **Processed Data**:
   - `sensitivity_results.csv`: Parameter rankings.
   - `pruned_model_weights.pt`: Pruned model state dict.
   - `faithfulness_scores.csv`: Per-sample scores for original/pruned/random-pruned models.
3. **Final Artifacts**: Statistical test results (p-value, confidence interval).

## Schema Constraints

- **Checksums**: All raw files in `data/raw/` must have checksums recorded in `data/checksums.json`.
- **Immutability**: Raw data never modified; derivations written to new files.
- **PII**: No personally identifiable information in datasets.