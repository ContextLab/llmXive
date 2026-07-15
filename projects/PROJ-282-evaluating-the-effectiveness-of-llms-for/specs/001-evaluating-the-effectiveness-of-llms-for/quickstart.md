# Quickstart: Evaluating LLM Vulnerability Detection

The following steps assume a fresh GitHub Actions runner or a local Linux environment with Python 3.11.

## 1. Clone the repository
```bash
git clone
cd llm-vuln-eval
```

## 2. Create the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Install system dependencies (static analyzers)
```bash
# Bandit is a pip package, already installed via requirements.txt
sudo apt-get update && sudo apt-get install -y cppcheck
```

## 4. Run the full pipeline (single command)
```bash
python -m code.main \
 --max-snippets 5000 \
 --batch-size 8 \
 --seed 42 \
 --output-dir data/processed
```
- The script will:
 1. Stream the three verified datasets.
 2. Parse and extract all features (including **KNN-based embedding similarity** to external corpus).
 3. Perform zero‑shot inference with the CPU‑quantized StarCoder model.
 4. Run Bandit and cppcheck on the same snippets.
 5. Compute all metrics, **Logistic Regression**, McNemar’s test (on matched samples), and the sensitivity analysis.
 6. Write JSON/CSV artefacts and generate PNG figures under `results/`.

## 5. Inspect results
```bash
# Summary JSON
cat results/summary.json | jq.

# Example metric table
python -c "import pandas as pd; print(pd.read_parquet('data/processed/analysis_metrics.parquet').head())"
```

## 6. Run the test suite (contract validation)
```bash
pytest -q
```
All contracts in `contracts/` must pass; failures indicate a breach of the data model or missing fields.

## 7. Re‑run with a different LLM (optional)
```bash
python -m code.main --model starcoder-base-4bit --max-snippets 2000
```
Replace `--model` with any model supported by `code/llm_infer.py` that can be loaded in CPU‑only mode.

---