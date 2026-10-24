# Quickstart: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites
* Python 3.11+  
* Git  
* ≈ several GB RAM (CPU) – optional Kaggle account for automatic GPU offload.  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd PROJ-997-llmxive-follow-up-extending-the-mirage-o

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\activate  # Windows

# 3️⃣ Install dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

All scripts accept a `--seed` argument (default = 42) to guarantee reproducibility.

### Step 1 – Generate Ground‑Truth Dataset (T015 & T017)

```bash
python code/cli/generate_ground_truth.py \
  --model_hf_id meta-llama/Meta-Llama-2-3B-4bit-gguf \
  --quant_levels INT4 INT8 \
  --prompt_source gsm8k \
  --output data/processed/training_sample.parquet \
  --seed 42
```

*If the CPU cannot finish within 5 h or runs out of memory, the script automatically re‑executes on a free Kaggle GPU (no code change required).*

```bash
# Optional FP8 generation (may be a no‑op if ONNX Runtime lacks float‑8 support)
python code/cli/generate_fp8_ground_truth.py \
  --model_hf_id meta-llama/Meta-Llama-2-3B-4bit-gguf \
  --prompt_source gsm8k \
  --output data/processed/training_sample.parquet \
  --seed 42
```

### Step 2 – Validate Dataset Statistics (T016)

```bash
python code/cli/validate_dataset_stats.py \
  --input data/processed/training_sample.parquet \
  --output data/metrics/dataset_stats.json
```

*Fails the pipeline if < 5 % of KL values are non‑zero for any quantization level.*

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

### Step 6 – Measure Total Runtime (T034)

```bash
python code/cli/measure_runtime.py \
  --pipeline full \
  --output data/metrics/runtime.json
```

## Verification

*Open `data/metrics/metrics.json` and confirm:*
- `correlation_results.*.pearson_r` ≥ 0.8  
- `statistical_tests.conclusion` mentions “No significant degradation (p > 0.05)”.  
- `latency_reduction.reduction_percentage` ≥ 90.  
- `runtime.total_seconds` ≤ 21600 (6 h).  

*Contract tests* – run schema validation:

```bash
pytest -m contract
```

All tests should pass; failures indicate a schema mismatch.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `llama_engine` OOM on CPU | Model too large for available RAM | Reduce `--max_batch_size` or let the script auto‑offload to Kaggle GPU (handled automatically). |
| Many KL values are zero | Prompt set too trivial | Use the “reasoning” subset of GSM8K (`filter(lambda x: len(x["question"].split()) > 20, ...)`). |
| FP8 generation fails | ONNX Runtime without float‑8 support | The script will log a warning and set `kl_div_fp8 = 0.0`; the bound verification still proceeds for INT4/INT8. |
| Contract test failure | Schema version mismatch | Re‑install dependencies (`pip install -r code/requirements.txt`). |
| Runtime exceeds 6 h | Dataset size too large | Reduce the number of prompts (e.g., `--max_samples 350`) and re‑run; the power analysis still holds for ≥ 300 samples. |

## Reproducibility Checklist
* Seed fixed (e.g., using a constant seed value).  
* All downloads performed via Hugging Face `datasets` / `huggingface_hub`.  
* SHA‑based checksums recorded in `state/`.  
* No manual edits to CSV/Parquet files after generation.  

---
