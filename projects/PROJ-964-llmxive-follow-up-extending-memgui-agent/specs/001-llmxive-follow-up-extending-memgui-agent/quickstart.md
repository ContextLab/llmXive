# Quickstart: llmXive follow-up: extending "MemGUI-Agent"

## Prerequisites

*   Python 3.11+
*   Access to Hugging Face (for MemGUI/Phi-3 and Sentence Transformers)
*   16GB+ RAM recommended (for 8B model loading, though 4-bit quantization reduces this)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `transformers`, `sentence-transformers`, `datasets`, `statsmodels`, `scipy`, `pandas`, `pytest`, `bitsandbytes`.*

## Data Preparation

The synthetic benchmark is generated automatically. If you wish to regenerate:

```bash
cd code
python data_generation/synthetic_benchmark.py \
  --num_trajectories 30 \
  --min_steps 50 \
  --max_steps 60 \
  --output_path ../data/synthetic_benchmark/trajectories.jsonl
```

*   This script uses procedural generation based on verified state templates. It does not require the MemGUI dataset.

## Execution

### 1. Run Baseline (CPU Only)
```bash
cd code
python main.py \
  --mode baseline \
  --data_path ../data/synthetic_benchmark/trajectories.jsonl \
  --model_name openbmb/MemGUI-8B-SFT \
  --quantization 4bit \
  --output_path ../logs/baseline/results.jsonl
```

### 2. Run Recall-Enhanced Agent
```bash
cd code
python main.py \
  --mode recall \
  --data_path ../data/synthetic_benchmark/trajectories.jsonl \
  --model_name openbmb/MemGUI-8B-SFT \
  --retriever all-MiniLM-L6-v2 \
  --threshold 0.75 \
  --output_path ../logs/recall/results.jsonl
```

### 3. Run Controls (Noise & Shuffled)
```bash
cd code
python main.py \
  --mode recall \
  --data_path ../data/synthetic_benchmark/trajectories.jsonl \
  --model_name openbmb/MemGUI-8B-SFT \
  --retriever all-MiniLM-L6-v2 \
  --control_type noise \
  --output_path ../logs/control_noise/results.jsonl

python main.py \
  --mode recall \
  --data_path ../data/synthetic_benchmark/trajectories.jsonl \
  --model_name openbmb/MemGUI-8B-SFT \
  --retriever all-MiniLM-L6-v2 \
  --control_type shuffled \
  --output_path ../logs/control_shuffled/results.jsonl
```

### 4. Run Statistical Analysis (GLMM)
```bash
cd code
python evaluation/stats.py \
  --baseline ../logs/baseline/results.jsonl \
  --recall ../logs/recall/results.jsonl \
  --noise ../logs/control_noise/results.jsonl \
  --shuffled ../logs/control_shuffled/results.jsonl \
  --output ../data/results/stats_summary.json
```

## Validation

*   **Check Logs**: Ensure `logs/` contain `results.jsonl` with `success` (binary), `latency`, and `memory_footprint` fields.
*   **Check Stats**: `data/results/stats_summary.json` should contain the GLMM coefficients and p-values.
*   **Plausibility**: If running the full pipeline, ensure the `coherence_validator.py` script passed the >0.8 plausibility threshold.