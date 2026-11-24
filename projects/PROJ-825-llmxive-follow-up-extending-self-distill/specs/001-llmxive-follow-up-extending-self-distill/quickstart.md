# Quickstart: llmXive follow‑up: extending "Self‑Distilled Agentic Reinforcement Learning"

## Prerequisites
* Python 3.11+  
* ≥ 8 GB RAM (minimum for 8‑bit quantization)  
* Git  

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-825-llmxive-follow-up-extending-self-distill/code/

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Experiments

### 1. GRPO Baseline (ALFWorld)
```bash
python main.py \
  --variant grpo \
  --env alfworld \
  --seed 42 \
  --max-steps 2000000 \
  --output-dir data/processed/grpo-alfworld
```

### 2. Baseline SDAR (Teacher + Student) – ALFWorld
```bash
python main.py \
  --variant baseline \
  --env alfworld \
  --seed 42 \
  --max-steps 2000000 \
  --output-dir data/processed/baseline-alfworld
```

### 3. Student‑Only Gating – ALFWorld
```bash
python main.py \
  --variant student-only \
  --env alfworld \
  --seed 42 \
  --max-steps 2000000 \
  --output-dir data/processed/student-only-alfworld
```

### 4. Paired Trajectory Replay (Correlation Analysis)
After the Baseline run finishes, replay its trajectories through the Student‑Only agent:

```bash
python main.py \
  --variant student-only-replay \
  --env alfworld \
  --input-trajectories data/processed/baseline-alfworld/trajectories.jsonl \
  --output-dir data/processed/student-only-replay-alfworld
```

### 5. Statistical Analysis (after several runs per variant)
```bash
python metrics/statistical_test.py \
  --grpo-dir data/processed/grpo-alfworld \
  --baseline-dir data/processed/baseline-alfworld \
  --student-only-dir data/processed/student-only-alfworld \
  --replay-dir data/processed/student-only-replay-alfworld \
  --output data/processed/comparison_report.json
```

## Expected Outputs
* `data/processed/<variant>-<env>.jsonl` – step‑level metrics (`H_t`, `S_t`, `g_t`, CPU time, memory).  
* `data/processed/episode_metrics.parquet` – episode‑level aggregates for bootstrapping.  
* `data/processed/comparison_report.json` – JSON report containing p‑value, effect size, cost reduction, performance retention, and Pearson r.  
* `data/processed/correlation_analysis.csv` – raw paired‑trajectory correlation data.  

## Troubleshooting
* **OOM**: Reduce `context_window_size` in `config.py` or switch to a smaller retriever model.  
* **NaN gating scores**: Verify that `is_valid=False` entries are logged; they indicate unstable context retrieval.  
* **Slow execution**: Ensure the runner supports AVX; if CPU fails to load the model, the script will abort with a clear error (no GPU fallback).  
* **Early stopping too early**: Adjust `reward_threshold` or `consecutive_episodes` in `config.py`.  

---
