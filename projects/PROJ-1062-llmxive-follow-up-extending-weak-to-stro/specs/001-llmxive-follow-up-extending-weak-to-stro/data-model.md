# Data Model: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

## Data Sources

### 1. AIME 2024 Dataset
*   **Source**: `MathArena/aime_2024` (HuggingFace)
*   **Format**: Parquet
*   **Fields**: `id`, `year`, `problem_number`, `question`, `answer`, `part`
*   **Usage**: Training and evaluation prompts; ground-truth token extraction.

### 2. Teacher Checkpoints
*   **Source**: HuggingFace Hub
*   **Models**: `pre_rl_checkpoint`, `post_rl_checkpoint` (Dense Transformer)
*   **Usage**: Computation of implicit reward signal.

### 3. Student Checkpoints
*   **Source**: HuggingFace Hub
*   **Models**: `Qwen/Qwen1.5-MoE-A2.7B`, `state-spaces/mamba-1.3b`
*   **Usage**: Initialization of training loops.

## Data Flow

1.  **Raw Data**: Downloaded from HuggingFace to `data/raw/aime_2024.parquet`.
2.  **Processed Data**:
    *   `data/processed/train_split.parquet`: Training subset (a representative set of problems).
    *   `data/processed/held_out_split.parquet`: Held-out subset for evaluation.
    *   `data/processed/reward_signals.parquet`: Contains `prompt`, `ground_truth_tokens`, `reward_scores`.
    *   `data/processed/student_outputs.jsonl`: Contains `model_id`, `prompt`, `generated_tokens`, `log_probs`, `reward_accumulated`.
3.  **Results**: `artifacts/results.yaml`: Aggregated metrics, p-values, and comparative summary.

## Schema Definitions

### Dataset Schema
*   **Source**: `data/raw/aime_2024.parquet`
*   **Fields**:
    *   `id`: string (unique identifier)
    *   `question`: string (prompt text)
    *   `answer`: string (ground truth solution)
    *   `part`: string (optional part identifier)

### Reward Signal Schema
*   **Source**: `data/processed/reward_signals.parquet`
*   **Fields**:
    *   `prompt_id`: string
    *   `token_id`: integer
    *   `log_prob_pre`: float
    *   `log_prob_post`: float
    *   `implicit_reward`: float (computed as `log_prob_post - log_prob_pre`)

### Results Schema
*   **Source**: `artifacts/results.yaml`
*   **Fields**:
    *   `experiment_id`: string
    *   `architecture`: string (MoE, SSM)
    *   `training_regime`: string (Direct-OPD, Baseline)
    *   `avg_log_prob_improvement`: float
    *   `p_value_raw`: float
    *   `p_value_adjusted`: float
    *   `significant`: boolean
