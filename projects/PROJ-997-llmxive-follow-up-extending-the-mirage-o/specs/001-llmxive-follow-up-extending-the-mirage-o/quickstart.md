# Quickstart: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Prerequisites
* Python 3.11+  
* Git  
* ≈ 6 GB RAM (CPU). No GPU required; the pipeline is CPU‑only.  

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
  --max_samples 350 \
  --seed 42
```

*If the CPU runs out of memory, the script aborts with an informative error; reduce `--max_samples` or switch to a smaller model.*  

```bash
# Optional FP8 generation (CPU only; may be a no‑op if float‑8 unsupported)
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

*Fails the pipeline if < 5 % of KL values are non‑zero for any present quantization level.*

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

### Step 5 – Run the MIPU Benchmark (T027‑T029 + T033)

```bash
python code/validation/mipu_benchmark.py \
  --model data/models/gap_predictor.pkl \
  --data data/processed/training_sample.parquet \
  --num_prompts 100 \
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
| `llama_engine` OOM on CPU | Model too large for available RAM | Reduce `--max_samples` or switch to a smaller checkpoint (e.g., 1.7 B). |
| Many KL values are zero | Prompt set too trivial | Use the “reasoning” subset of GSM8K (`len(question.split()) > 20`). |
| FP8 generation logs “unsupported” | ONNX Runtime lacks float‑8 support | No action needed; FP8 rows are simply omitted. |
| Contract test failure | Schema version mismatch | Re‑install dependencies (`pip install -r code/requirements.txt`). |
| Runtime exceeds 6 h | Dataset size too large | Reduce `--max_samples`; power analysis still holds for ≥ 300 samples. |

## Reproducibility Checklist
- Seed fixed (`--seed 42`).  
- All downloads performed via Hugging Face `datasets` / `huggingface_hub`.  
- SHA‑based checksums recorded in `state/`.  
- No manual edits to CSV/Parquet files after generation.  

---
