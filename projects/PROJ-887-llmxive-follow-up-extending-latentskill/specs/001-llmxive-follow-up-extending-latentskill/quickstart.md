# Quickstart: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

## Prerequisites

* Python 3.11+
* Git
* 7 GB+ RAM (for running the full pipeline)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmxive-follow-up
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
 *Note: `requirements.txt` pins `torch` to CPU-only version and `llama-cpp-python` for CPU inference.*

4. **Download Data**:
 Run the ingestion script to download LoRA weights (ensure you have network access).
 ```bash
 python src/ingestion/download_weights.py --output data/raw
 ```
 *If the specific HuggingFace dataset is unavailable, the script will log a warning and skip that task, allowing the pipeline to proceed with available data.*

## Running the Pipeline

### Step 1: Build the Skill Vector Database
```bash
python src/ingestion/flatten_lora.py --input data/raw --output data/processed
```
*Output*: `data/processed/skill_vectors.npy`, `data/processed/skill_metadata.json`.

### Step 2: Run Evaluation
This script performs retrieval, synthesis, and evaluation on a held-out set of tasks.
```bash
python src/evaluation/runner.py \
 --vectors data/processed/skill_vectors.npy \
 --metadata data/processed/skill_metadata.json \
 --tasks data/raw/composite_tasks.json \
 --runs 5 \
 --output data/results/eval_log.csv
```

### Step 3: Statistical Analysis
```bash
python src/evaluation/stats.py \
 --input data/results/eval_log.csv \
 --output data/results/stats_summary.json
```

## Verification

Check the output `data/results/stats_summary.json` for:
* `linearity_correlation`: Should be $\ge 0.6$ (FR-007).
* `significant_methods`: List of methods where `p_value_bh < 0.05` (FR-006).
* `latency_ms`: Selection time (SC-003).

## Troubleshooting

* **OOM Error**: Reduce the number of concurrent tasks or switch to a smaller base model in `src/utils/config.py`.
* **Dataset 404**: Verify the URL in `src/ingestion/download_weights.py` against the `Verified datasets` block in `research.md`.
