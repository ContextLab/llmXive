# Quickstart: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites

* Python 3.11+
* `llama-cpp-python` (with `llama.cpp` backend) or `onnxruntime`
* Git (for repository access)
* Sufficient RAM (for CPU inference) or access to a Kaggle GPU (for auto-offload)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or venv\Scripts\activate # Windows
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

### Step 1: Generate Ground Truth Data (US-001)
This step downloads GSM8K, runs full-precision feature extraction, and executes quantized inference via `llama.cpp`.

```bash
python code/data/generate_ground_truth.py --model meta-llama/Meta-Llama-3-8B --levels INT4 INT8 FP8 --output data/processed/training_sample.parquet
```
*Note: If `llama.cpp` fails on CPU, the script will auto-offload to Kaggle GPU if configured.*

### Step 2: Train the Gap Predictor (US-002)
Trains a Kernel Ridge Regression model on the generated dataset.

```bash
python code/models/train_predictor.py --input data/processed/training_sample.parquet --output data/models/gap_predictor.pkl
```

### Step 3: Evaluate and Validate (US-003)
Computes correlation, bound verification, and runs the MIPU benchmark.

```bash
python code/models/evaluate_predictor.py --model data/models/gap_predictor.pkl --data data/processed/training_sample.parquet --output data/metrics/metrics.json
```

## Verification

* **Check Metrics**: Inspect `data/metrics/metrics.json` for Pearson correlation > 0.8 and bound consistency.
* **Reproducibility**: Re-run the pipeline with `--seed 42` to verify identical results (checksums match).
* **Contract Tests**: Run `pytest tests/contract/` to validate data schemas.

## Troubleshooting

* **`llama.cpp` load error**: Ensure the model is quantized correctly (e.g., `Q4_K_M.gguf`). Check `code/utils/llama_engine.py` for fallback logic.
* **Out of Memory**: Reduce the sample size in `generate_ground_truth.py` or use the GPU escape hatch.
* **Zero Divergence**: If all KL divergences are zero, the prompts may be too simple. Increase prompt complexity or sample size.
