# Quickstart: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites
* Python 3.11+  
* Git (to clone the repository)  
* Sufficient RAM (≈ 6 GB) for CPU inference; optional Kaggle GPU account for automatic offload.  

## Installation

```bash
# 1️⃣ Clone the repository
git clone 
cd PROJ-997-llmxive-follow-up-extending-the-mirage-o

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 3️⃣ Install dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

All scripts accept a `--seed` argument (default = 42) to guarantee reproducibility.

### Step 1 – Generate Ground‑Truth Dataset (T015)
```bash
python code/cli/generate_ground_truth.py \
  --model meta-llama/Meta-Llama-2-7B-4bit \
  --quant_levels INT4 INT8 FP8 \
  --prompt_source gsm8k \
  --output data/processed/training_sample.parquet \
  --seed 42
```
*If the CPU cannot finish within the 6 h window, the script automatically re‑executes on a Kaggle GPU (no code change required). The resulting `hardware_source` column records the execution device.*

### Step 2 – Validate Dataset Statistics (T016)
```bash
python code/cli/validate_dataset_stats.py \
  --input data/processed/training_sample.parquet \
  --output data/metrics/dataset_stats.json
```
*Checks that a sufficient proportion of KL values are non‑zero.*

### Step 3 – Train the Gap Predictor (T021)
```bash
python code/models/train_predictor.py \
  --data data/processed/training_sample.parquet \
  --model_out data/models/gap_predictor.pkl \
  --seed 42
```

### Step 4 – Evaluate & Verify Bounds (T022)
```bash
python code/models/evaluate_predictor.py \
  --model data/models/gap_predictor.pkl \
  --data data/processed/training_sample.parquet \
  --metrics_out data/metrics/metrics.json \
  --predictions_out data/metrics/gap_predictions.parquet
```

### Step 5 – Run the MIPU Benchmark (T027‑T029)
```bash
python code/validation/mipu_benchmark.py \
  --model data/models/gap_predictor.pkl \
  --data data/processed/training_sample.parquet \
  --output data/metrics/benchmark_report.json
```

### Step 6 – Measure Runtime (T034)
```bash
python code/cli/measure_runtime.py \
  --pipeline "full" \
  --output data/metrics/runtime.json
```

## Verification

* **Metrics check** – Open `data/metrics/metrics.json` and confirm:
  * `correlation_results.*.pearson_r` ≥ 0.8  
  * `statistical_tests.conclusion` mentions “No significant degradation (p > 0.05)”.  
  * `latency_reduction.reduction_percentage` ≥ 90.  
  * `runtime.total_seconds` ≤ 21600 (6 h).  

* **Contract tests** – Run the schema validation suite:

```bash
pytest -m contract
```

All tests should pass; failures indicate a schema mismatch.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `llama_engine` OOM on CPU | Model too large for available RAM | Reduce `--max_batch_size` or let the script auto‑offload to Kaggle GPU. |
| Zero KL divergence for many samples | Prompt too trivial | Increase prompt length or select the “reasoning” subset of GSM8K (use `is_reasoning_task=True`). |
| `generate_ground_truth.py` exits with code 1 | Missing gguf checkpoint | Download the 4‑bit gguf file (`Meta-Llama-2-7B-4bit.gguf`) from Hugging Face and place it under `data/raw/`. |
| Contract test failure | Schema version mismatch | Re‑run `pip install -r code/requirements.txt` to ensure latest `jsonschema` library. |

## Reproducibility Checklist
* Seed fixed (`--seed 42`).  
* All downloads performed via HF `datasets` / `huggingface_hub`.  
* SHA‑256 checksums recorded in `state/`.  
* No manual edits to CSV/Parquet files after generation.
