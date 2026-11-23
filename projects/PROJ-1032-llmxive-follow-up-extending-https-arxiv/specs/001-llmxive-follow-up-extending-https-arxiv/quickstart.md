# Quickstart: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Low-Capacity Models

## Prerequisites

- **Python**: 3.11 or higher.
- **Hardware**: 2 CPU cores, 7GB RAM (minimum). GPU optional but not required.
- **Disk**: 14GB free space (for dataset cache and dependencies).
- **Dependencies**: `datasets`, `transformers`, `torch`, `bitsandbytes`, `scipy`, `numpy`, `accelerate`, `lifelines` (for survival analysis).

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-staleness-scaling
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 *Note: `bitsandbytes` will automatically detect CPU and install the CPU-compatible version. `lifelines` is required for survival analysis.*

4. **Verify installation**:
 ```bash
 python -c "import torch; import bitsandbytes; import lifelines; print('CUDA available:', torch.cuda.is_available())"
 # Expected output: CUDA available: False (CPU-only mode)
 ```

## Running the Experiment

### 1. Generate Baseline Manifests (Required First Step)

Before running asynchronous experiments, you must generate baselines for each seed.

```bash
python src/cli/run_experiment.py \
 --mode baseline \
 --model microsoft/phi-2 \
 --seeds 2 3 4 5 \
 --steps multiple epochs \
 --output data/processed/manifests
```

- This will run multiple synchronous training jobs.
- **All seeds are retained**, regardless of stability. Unstable seeds are logged.

### 2. Run Asynchronous Experiments

Once manifests are generated, run the main experiment.

```bash
python src/cli/run_experiment.py \
 --mode experiment \
 --model microsoft/phi-2 \
 --staleness 10 \
 --seeds 1 2 3 4 5 \
 --steps 500 \
 --baseline-dir data/processed/manifests \
 --output data/processed/run_logs
```

- Replace `microsoft/phi-2` with `Qwen/Qwen1.5-1.8B` for the second model.
- Adjust `--staleness` to test different regimes (0, 5, 10, 15, 20).

### 3. Analyze Results

After all runs are complete, generate the summary and statistical tests.

```bash
python src/cli/run_experiment.py \
 --mode analyze \
 --input-dir data/processed/run_logs \
 --output data/processed/summary_results.json
```

- This will compute the **Survival Analysis (Log-Rank test)**, **Levene's test**, and **t-test**.
- It will output the final table and JSON results.

### 4. Generate Figures

Generate all plots programmatically from the processed data to ensure reproducibility.

```bash
python src/cli/generate_plots.py \
 --input data/processed/summary_results.json \
 --output data/artifacts/
```

- This ensures all figures trace back to the `data/processed/` logs (Single Source of Truth).

## Configuration

You can customize the experiment via `config.yaml` in the root directory:

```yaml
model:
 phi2: "microsoft/phi-2"
 qwen: "Qwen/Qwen1.5-1.8B"

training:
 steps: 500
 batch_size: # Adjust if OOM occurs
 learning_rate: a small positive scalar appropriate for fine-tuning

staleness:
 low: 0
 high: 10
 adaptive: true

divergence:
 reward_threshold: 2.0 # Variance/Mean ratio
 gradient_threshold: 2.0 # Variance/Mean ratio
 window_size: 50
```

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `config.yaml` to 4 or 2.
- **CUDA Error**: Ensure `bitsandbytes` is installed with CPU support. If `torch.cuda.is_available()` is True but you want CPU, force `device="cpu"` in the config.
- **Dataset Download Failed**: Check your internet connection. The dataset is cached in `~/.cache/huggingface/`.
- **Baseline Unstable**: The seed is recorded as unstable but **not discarded**. The asynchronous run will still proceed.

## Expected Output

- `data/processed/manifests/`: JSON files with baseline stats.
- `data/processed/run_logs/`: JSON logs for each training run.
- `data/processed/summary_results.json`: Final statistical analysis (Survival, Levene, t-test).
- `data/artifacts/`: Plots and tables (generated programmatically).

## Next Steps

- Review the `summary_results.json` for statistical significance (Log-Rank p-value).
- Compare the staleness thresholds between Phi-2 and Qwen1.5.
- Reproduce the experiment with different models or datasets.