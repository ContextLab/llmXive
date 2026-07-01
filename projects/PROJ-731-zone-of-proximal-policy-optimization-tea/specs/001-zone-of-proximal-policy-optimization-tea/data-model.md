# Data Model: Zone of Proximal Policy Optimization

## Overview

This document defines the data structures for the ZPPO project. It covers the schema for training logs, benchmark results, and the prompt buffer metadata. All data is stored in JSONL or CSV formats for easy parsing and analysis.

## Entities

### 1. TrainingRun
Represents a single execution of the PPO training loop.
*   **Attributes**:
    *   `run_id`: Unique string identifier (e.g., `run_001_seed_42_10k`).
    *   `prompt_size`: Integer (0, 10000, 50000, 200000).
    *   `seed`: Integer.
    *   `start_time`: ISO 8601 timestamp.
    *   `end_time`: ISO 8601 timestamp (or `null` if interrupted).
    *   `status`: String (`completed`, `interrupted`, `error`).
    *   `memory_fallback_triggered`: Boolean.
    *   `kl_adaptations`: Integer (count of learning rate reductions due to high KL).
    *   `final_step_count`: Integer (total steps executed).

### 2. PerformanceMetric
Represents a benchmark evaluation result at a specific step.
*   **Attributes**:
    *   `run_id`: String (FK to TrainingRun).
    *   `step_count`: Integer.
    *   `benchmark_name`: String (`lambada_openai`, `truthful_qa`, `mmlu`).
    *   `accuracy`: Float (0.0 - 1.0).
    *   `timestamp`: ISO 8601 timestamp.

### 3. PromptBufferMetadata
Describes the versioned prompt dataset used.
*   **Attributes**:
    *   `buffer_id`: String (e.g., `oasst1_10k_v1`).
    *   `size`: Integer.
    *   `source_dataset`: String (`OpenAssistant/oasst1`).
    *   `checksum`: String (SHA-256 of the file content).
    *   `creation_date`: ISO 8601 timestamp.
    *   `sample_method`: String (`random`, `stratified`).

## File Formats

### Training Logs (`results/training_logs/{run_id}.jsonl`)
Each line is a JSON object representing a step-level log.
```json
{
  "step": 100,
  "reward_mean": 0.45,
  "kl_divergence": 0.02,
  "learning_rate": 0.0001,
  "memory_status": "ok",
  "timestamp": "2026-06-23T10:00:00Z"
}
```

### Benchmark Results (`results/benchmarks/{run_id}_benchmarks.csv`)
CSV file with columns: `step_count, benchmark_name, accuracy`.

### Aggregated Analysis Data (`results/analysis/aggregated.csv`)
CSV file for post-hoc non-parametric analysis. Columns: `run_id, prompt_size, seed, final_step_count, benchmark_name, final_accuracy`.
*Note: This file contains the final accuracy for each run, aggregated by prompt size, suitable for Kruskal-Wallis and Kendall's Tau tests.*


## projects/PROJ-731-zone-of-proximal-policy-optimization-tea/specs/001-zone-of-proximal-policy-optimization-tea/quickstart.md
# Quickstart: Zone of Proximal Policy Optimization

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with 7GB+ RAM, 2+ CPU cores).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-731-zone-of-proximal-policy-optimization-tea
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Training Loop

To run a single training experiment (e.g., 10k prompts, seed 42):

```bash
python code/train_ppo.py \
  --prompt-size 10000 \
  --seed 42 \
  --max-steps 1000 \
  --output-dir results/
```

**Arguments**:
- `--prompt-size`: Number of teacher demonstrations (0, 10000, 50000, 200000).
- `--seed`: Random seed for reproducibility.
- `--max-steps`: Maximum PPO iterations (default 1000).
- `--output-dir`: Directory to save logs and checkpoints.

## Evaluating Benchmarks

To evaluate a specific checkpoint on all three benchmarks:

```bash
python code/eval_benchmarks.py \
  --checkpoint results/checkpoints/checkpoint_200 \
  --benchmarks lambada_openai truthful_qa mmlu \
  --output results/benchmarks/eval_200.csv
```

## Analyzing Results

After running multiple seeds (e.g., 3 per condition), aggregate the data:

```bash
python code/analyze.py \
  --input results/analysis/aggregated.csv \
  --output results/analysis/statistical_results.json
```

This script will perform:
1. **Kendall's Tau**: To test for a monotonic trend between prompt size and accuracy.
2. **Kruskal-Wallis H-test**: To detect significant differences between the four prompt-size groups.
3. **Dunn's Test (with Bonferroni)**: If Kruskal-Wallis is significant, to identify specific pairwise differences (e.g., 0k vs 10k, 50k vs 200k).
4. **Plateau Inference**: A descriptive report indicating if the gain from 50k to 200k is statistically insignificant compared to earlier gains.

## Troubleshooting

- **Memory Error**: If you encounter OOM, reduce `--prompt-size` or `--batch-size`. The system will automatically log `MEMORY_FALLBACK` if it samples the buffer.
- **Dataset Access**: Ensure you have internet access to download `oasst1` and benchmarks.
- **Timeout**: If the job exceeds 6 hours, the process will be terminated. The last checkpoint will be saved.