# Quickstart: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Prerequisites

- Python 3.11+
- 7GB+ RAM (CPU-only) or 16GB+ VRAM (GPU escape hatch)
- HuggingFace CLI token (for model access)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd specs/001-llmxive-followup
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Download Datasets**:
   ```bash
   # Download MMLU (STEM Subset)
   python src/data/download.py --dataset HuggingFaceH4/mmlu --subset STEM --output data/raw/mmlu_stem.jsonl
   # Download OpenScience (Raw Source for OpenSci-Reason)
   python src/data/download.py --dataset nvidia/OpenScience --output data/raw/open_science_raw.jsonl
   ```

## Running the Pipeline

### Step 1: Curate & Unify Prompts
Filter raw data and merge into a unified dataset with `domain` labels.
```bash
python src/data/curate.py \
  --input data/raw/open_science_raw.jsonl \
  --output data/intermediate/open_sci_reason.jsonl \
  --filter ill_structured

python src/data/preprocess.py \
  --mmlu data/raw/mmlu_stem.jsonl \
  --opendsi data/intermediate/open_sci_reason.jsonl \
  --output data/intermediate/prompts_unified.jsonl
```

### Step 2: Generate Responses
Run inference for SU-01 and Baseline on both MMLU and OpenSci-Reason.
```bash
python src/inference/run_generation.py \
  --model SU-01 \
  --dataset data/intermediate/prompts_unified.jsonl \
  --output data/intermediate/responses_SU01.jsonl \
  --temperature 0.7 \
  --max_tokens 2048 \
  --device cpu
```
*Note: If OOM occurs, the script will auto-switch to 8-bit quantization or fail gracefully.*

### Step 3: Score Responses
Run the proxy scoring model.
```bash
python src/inference/scoring.py \
  --input data/intermediate/responses_SU01.jsonl \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --output data/intermediate/scores.jsonl \
  --quantize 8bit
```

### Step 4: Validate Proxy Model
Check correlation with Gold Standard (Manually Curated).
```bash
python src/analysis/validation.py \
  --scores data/intermediate/scores.jsonl \
  --gold-standard data/raw/gold_standard_50.json \
  --threshold 0.6 \
  --fallback-mode auto
```
*Note: If correlation < 0.6, the script will attempt to switch to a fallback proxy or human-only mode.*

### Step 5: Statistical Analysis
Compute correlations, t-tests, and LME.
```bash
python src/analysis/simple_stats.py \
  --olympiad-scores data/intermediate/mmlu_results.jsonl \
  --open-sci-scores data/intermediate/scores.jsonl \
  --output data/final/simple_stats.json

python src/analysis/lme_analysis.py \
  --data data/intermediate/scores.jsonl \
  --output data/final/lme_results.json
```

## Troubleshooting

- **OOM Error**: Ensure `--quantize 8bit` is used. If still failing, reduce `batch_size` to 1.
- **Timeout**: Reduce dataset size to 200 prompts.
- **CUDA Required**: If the script detects CUDA dependencies, it will attempt to offload to a GPU environment (if available) or fail with a clear error message.
- **Proxy Validation Failed**: If the primary proxy fails, the system will automatically attempt the fallback proxy. Check `logs/validation.log` for details.
