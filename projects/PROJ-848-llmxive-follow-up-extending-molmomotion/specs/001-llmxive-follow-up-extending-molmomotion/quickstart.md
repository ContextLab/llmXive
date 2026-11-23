# Quickstart: llmXive follow-up: extending "MolmoMotion: Forecasting Point Trajectories in 3D with Language Instru"

## Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM (or a CI runner with these specs)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-848-llmxive-follow-up-extending-molmomotion
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  **Verify CPU availability** (ensure no CUDA is forced).
    ```bash
    python -c "import torch; print('Device:', torch.device('cpu'))"
    ```

## Running the Pipeline

The pipeline is executed via a single orchestration script that handles data download, subsampling, synthesis, inference, and analysis.

```bash
# Run the full pipeline
bash code/run_pipeline.sh
```

### What the script does:
1.  **Downloads** the MolmoMotion dataset from the verified Hugging Face URLs.
2.  **Subsamples** the dataset to [deferred] instances (random seed 42).
3.  **Synthesizes** dual instruction modalities (NL and Structured).
4.  **Runs Inference** using the CPU-only linear projection model.
5.  **Calculates** ATE and performs the paired t-test.
6.  **Outputs** results to `data/results/`.

## Verifying Results

After the script completes, check the output files:

1.  **Check Data Integrity**:
    ```bash
    ls -lh data/processed/
    # Should see subsampled_instances.parquet and instruction_pairs.jsonl
    ```

2.  **View Statistical Results**:
    ```bash
    cat data/results/t_test_results.json
    # Should contain p-value, mean ATE for NL, mean ATE for Structured, and significance flag.
    ```

3.  **Verify CPU Usage**:
    The script logs peak memory and CPU usage. Ensure no GPU warnings appear.

## Troubleshooting

- **OOM Error**: If the script fails with `MemoryError`, the subsample size might be too large for your specific environment. Reduce the `SUBSAMPLE_SIZE` variable in `code/run_pipeline.sh`.
- **Dataset Download Failed**: The script retries 3 times. If it fails, check your internet connection and ensure the Hugging Face URLs are accessible.
- **NaN in Predictions**: Check `data/results/predictions.jsonl` for instances marked with `status: nan`. These are excluded from the final analysis.
