# Quickstart: llmXive follow-up: extending "COLLEAGUE.SKILL"

## Prerequisites

*   Python 3.11+
*   Sufficient RAM available (CPU) or access to Kaggle GPU (optional fallback).
*   Git.

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-llmxive-skill-separation
    cd projects/PROJ-922-llmxive-follow-up-extending-colleague-sk
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Environment**:
    ```bash
    python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    # Should return False for CPU-only run.
    ```

## Running the Pipeline

### Step 1: Generate Data
```bash
python code/data/generators/profile_generator.py --count [variable] --seed 42
python code/data/generators/task_generator.py --count [sufficient_sample_size] --seed 42
```

### Step 2: Run Inference
*Note: This will enforce a timeout per task.*
```bash
python code/inference/run_inference.py --model Llama-3-8B-Q4 --backend cpu
# Fallback: If CPU fails, the script will suggest Kaggle GPU offload.
```

### Step 3: Evaluate
```bash
python code/evaluation/score.py --input data/interim/inference_outputs.jsonl
```

### Step 4: Analyze
```bash
python code/analysis/stats.py --input data/processed/evaluation_results.jsonl
```

## Troubleshooting

*   **OOM Error**: Reduce batch size in `config.py` or switch to `Phi-3-mini`.
*   **Timeout**: If >300s, the task is logged as "timeout". Check `data/interim/inference_outputs.jsonl`.
*   **CUDA Error**: Ensure `torch` is installed without CUDA support or set `CUDA_VISIBLE_DEVICES=""`.
