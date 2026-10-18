# Quickstart: Running the Intent‑Graph Evaluation

> All commands assume you are in the repository root and have a fresh GitHub Actions runner (or equivalent local environment).

## 1️⃣ Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2️⃣ Download $\pi$‑Bench Data
```bash
python -c "from datasets import load_dataset; load_dataset('pi_bench', data_dir='data/raw')"
# The script records a SHA‑256 checksum in state/...yaml automatically.
```

## 3️⃣ Parse & Normalize Traces
```bash
python src/pipelines/parse_traces.py \
    --raw-dir data/raw \
    --out-csv data/derived/normalized_traces.csv
```

## 4️⃣ Build Intent Graphs
```bash
python src/pipelines/build_intent_graph.py \
    --input-csv data/derived/normalized_traces.csv \
    --out-dir data/derived/intent_graphs \
    --seed 42
```
*The script validates each JSON against `contracts/intent_graph.schema.yaml`.*

## 5️⃣ Run Agents (three seeds)
```bash
for SEED in 101 202 303; do
  python src/pipelines/run_lightweight_agent.py \
      --graph-dir data/derived/intent_graphs \
      --seed $SEED \
      --out data/derived/inference_logs/lightweight_seed${SEED}.csv
  python src/pipelines/run_raw_baseline.py \
      --raw-dir data/raw \
      --seed $SEED \
      --out data/derived/inference_logs/raw_seed${SEED}.csv
  python src/pipelines/run_null_baseline.py \
      --raw-dir data/raw \
      --seed $SEED \
      --out data/derived/inference_logs/null_seed${SEED}.csv
done
```

## 6️⃣ Evaluate
```bash
python src/pipelines/evaluate.py \
    --logs-dir data/derived/inference_logs \
    --graph-dir data/derived/intent_graphs \
    --out-dir data/derived/eval_results
```
*Produces `summary.csv`, `report.md`, and PNG figures.*

## 7️⃣ Verify Contracts
```bash
pytest -q tests/contract
```
All JSON graphs must pass schema validation.

## 8️⃣ Inspect Results
```bash
cat data/derived/eval_results/report.md
```
You will see:
* F1 scores for Graph, Raw, Null
* Wilcoxon p‑values, t‑test p‑values, bootstrap CIs
* Latency reduction percentages
* Graph‑construction success rate

---

