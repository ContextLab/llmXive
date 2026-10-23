# Quickstart: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

## Prerequisites
- **Python** 3.11+  
- **Git** for cloning the repository  
- **CPU‑only** environment (GitHub Actions free‑tier or local machine with ≥2 cores, ~7 GB RAM)  

## Installation
```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-884-llmxive-follow-up-extending-self-improvi

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Verify Test Suite (addresses previously failing T001 & T002)
```bash
pytest tests/unit/
```
- **T001 fix**: `tests/unit/test_generator.py` now imports `DataGenerationError` from `code.dataset.errors`.  
- **T002 fix**: `tests/unit/test_symbolic_planner.py` catches the real exception classes `ParseFailure` and `ContradictionDetected`.  

All unit tests should now pass.

## Phase 0 – Pilot Dataset & Verification
```bash
python -m code.main --pilot --seed 42
```
- Generates a small set of puzzles (N = 10‑30).  
- Runs deterministic verification on a known correct solution to confirm < 100 ms latency.  
- Outputs pilot logs to `data/processed/pilot_run.jsonl`.

## Phase 1 – Full Experiments

### Symbolic‑guided BES
```bash
python -m code.main \
    --method symbolic \
    --pop-size 50 \
    --generations 20 \
    --output data/processed/symbolic_run.jsonl \
    --seed 42
```

### Neural‑verifier Baseline
```bash
python -m code.main \
    --method neural \
    --pop-size 50 \
    --generations 20 \
    --output data/processed/neural_run.jsonl \
    --seed 42
```
Both commands use the **same** puzzle set (generated once with `--seed 42`) so that success‑rate comparisons are based on matched instances. The success‑rate is computed as `valid_solutions / total_instances`; puzzles that the symbolic planner cannot decompose are counted as failures (success = 0) to keep denominators identical.

## Phase 2 – Statistical Analysis
```bash
python -m code.analysis.stats \
    --symbolic data/processed/symbolic_run.jsonl \
    --neural data/processed/neural_run.jsonl \
    --output data/processed/results.json
```
Produces:
- `success_rate`, `mean_time`, `p_value_mcnemar`, `p_value_t`, `significance` fields (validated against `contracts/output.schema.yaml`).  
- `scalability_regression.csv` containing log‑log regression coefficients.

## Reproducibility Checklist
- **Random seeds** are fixed (`--seed`).  
- **Checksums**: run `sha256sum data/raw/*` and compare to `state/...yaml`.  
- **Environment**: `pip freeze > env.txt` should match `requirements.txt`.  

## Troubleshooting
- **MemoryError**: Reduce `--pop-size` or `--generations`.  
- **Verifier timeout (>100 ms)**: Inspect `data/raw/verifier_*.py` for inefficiencies; ensure no heavy imports.  
- **LLM slowdown**: The script automatically falls back to a smaller model (`distilgpt2`) if runtime exceeds 30 s per generation batch.  

---

