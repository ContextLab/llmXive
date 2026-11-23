# Quickstart: llmXive follow‑up: extending “Anti‑Self‑Distillation for Reasoning RL via Pointwise Mutual Information”

## Prerequisites
- Python 3.11+  
- Git  
- Internet access (to download the verified BigBench shards)

## Installation

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-933-llmxive-followup-extending-anti-self-di/code/
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Verify dataset access**
   The script `data/download.py` will automatically download the three verified BigBench shards, populate `data/raw/`, and generate checksums:
   ```bash
   python data/download.py
   ```

## Running the Full Pipeline

The orchestrator `main.py` executes all phases in order:

```bash
python main.py --mode full --timeout 18000   # 5 h = 18 000 s
```

- `--mode data_prep` – only download & preprocessing.  
- `--mode train` – runs both AntiSD and StandardSD training loops (**200 steps per prompt**, not 500).  
- `--mode analyze` – computes diversity, deliberation, Human‑Eval‑Proxy, statistical tests, and writes `final_report.json`.

All outputs are written under `data/` as described in `data-model.md`.

## Configuration

Edit `config/settings.yaml` to adjust:

| Parameter | Description | Default |
|---|---|---|
| `seed_list` | List of random seeds for repeated runs | `[2026, 2027, 2028]` |
| `max_steps` | Training steps per prompt (**200**) | `200` |
| `model_name` | HuggingFace model identifier (tinybert) | `google/bert_uncased_L-2_H-128_A-2` |
| `deliberation_tokens` | List of tokens to count | `["let's think", "consider", "however", "wait"]` |
| `timeout_seconds` | Hard timeout for the whole run (FR‑013) | `18000` |

## Output Locations

- **Raw data**: `data/raw/` (cached shards)  
- **Processed data**: `data/processed/` (filtered prompts, context split, teacher logits)  
- **Training logs**: `data/results/training_run_*.jsonl` (includes `training_time_seconds` & `peak_memory_mb`)  
- **Human evaluation scores**: `data/results/human_eval_scores.csv`  
- **Final analysis (SSoT)**: `data/results/final_report.json`  

## Troubleshooting

- **Out‑of‑memory**: Tinybert is already minimal; if still OOM, reduce `max_steps` (will affect power) or request a larger runner.  
- **Insufficient rationales**: The audit will emit `data/raw/audit_report.json`; if fewer than 30 prompts meet the ≥ 3‑rationale threshold, the pipeline will abort and report insufficient data.  
- **Timeout**: If the job is killed, partial results are saved to `data/results/partial_*.jsonl`. Rerun with a higher `timeout_seconds` if the CI environment permits (max 6 h).  

---

