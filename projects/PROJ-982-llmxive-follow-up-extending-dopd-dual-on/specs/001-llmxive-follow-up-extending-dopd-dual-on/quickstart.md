# Quickstart: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Prerequisites
- Python 3.11 or newer  
- `git` and `pip` installed  

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-982-llmxive-follow-up-extending-dopd-dual-on
   ```

2. **Create a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r code/requirements.txt
   ```
   *Dependencies are pure‑Python (`numpy`, `scipy`, `pyyaml`, `pytest`).*

## Running Experiments

### 1. Debug a Single Seed
```bash
python code/main.py --seed 42 --regime dopd --steps 5000
```
- Generates the MDP with seed 42.  
- Trains the Student using DOPD.  
- Evaluates with and without the privileged signal.  
- Logs are written to `data/raw/` (see below) and per‑seed results to `data/processed/`.

### 2. Full Study (50 Seeds, Both Regimes)
```bash
python code/main.py --seeds 50 \
    --regimes uniform dopd \
    --steps 10000
```
- Executes 50 independent seeds for each regime.  
- Ensures distinct training/evaluation/baseline seed sets.  
- Aggregates CSVs (`results_uniform.csv`, `results_dopd.csv`).  
- Runs the Mann‑Whitney U test and writes `statistical_summary.json`.

### 3. Inspect the Statistical Summary
```bash
cat data/processed/statistical_summary.json
```
Key fields:
- `p_value` (should be < 0.05 to reject H0)  
- `effect_size` (Cliff’s Δ)  
- `is_exploratory` (true if effect size < 0.5)  
- `coefficient_of_variation` (CV of generalization accuracy)  

## Logging Details

- The **TrainingLogger** writes a JSON‑Lines file `data/raw/training_log.jsonl`.  
- Each line records `seed`, `regime`, `step`, `episode`, `loss`, `entropy`, `expected_advantage_gap` (or `null` for Uniform), and `reward`.  
- This file conforms to `contracts/training_log.schema.yaml` and serves as the single source of truth for downstream analysis.

## Testing

Run the full test suite:
```bash
pytest code/tests/ -v
```
Key tests:
- `test_env.py` – verifies hidden variable `H` is invisible to the Student.  
- `test_logging.py` – checks that `TrainingLogger` creates `data/raw/training_log.jsonl` and records required fields.  
- `test_lambda_switch.py` – ensures min‑max fallback is triggered when the advantage gap range < 0.1.  
- `test_uniform_vs_dopd.py` – integration test confirming the expected performance‑drop pattern.

## Troubleshooting

- **MemoryError**: Reduce `grid_size` in `code/env/privileged_grid.py` (max 10×10).  
- **ZeroDivisionError**: Ensure `utils/logging.py` is imported; the logger automatically writes a fallback λ = 1.0.  
- **ImportError for gym‑minigrid**: The project no longer depends on `gym-minigrid`; all environment code is pure Python.  

---

