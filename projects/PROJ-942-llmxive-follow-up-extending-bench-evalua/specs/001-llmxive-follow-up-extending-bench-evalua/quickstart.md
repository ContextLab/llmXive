# Quickstart: Running the Intent‑Graph Evaluation

> All commands assume you are in the repository root and have a fresh GitHub Actions runner (or equivalent local environment).

## 1️⃣ Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2️⃣ Download π‑Bench Data
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

## 4️⃣ Build Intent Graphs (records construction latency)
```bash
# First, compute the median token budget for the baseline to ensure fair comparison
python src/utils/compute_median_graph_token_budget.py --out data/derived/token_budget.txt

python src/pipelines/build_intent_graph.py \
    --input-csv data/derived/normalized_traces.csv \
    --out-dir data/derived/intent_graphs \
    --token-budget $(cat data/derived/token_budget.txt) \
    --seed 42 \
    --log-latency data/derived/graph_construction_latency.csv
```
*The script validates each JSON against `contracts/intent_graph.schema.yaml` and prunes low-confidence nodes if the graph exceeds the token budget.*

## 5️⃣ Run Agents (three seeds)
```bash
for SEED in 101 202 303; do
  python src/pipelines/run_lightweight_agent.py \
      --graph-dir data/derived/intent_graphs \
      --seed $SEED \
      --out data/derived/inference_logs/lightweight_seed${SEED}.csv
  python src/pipelines/run_raw_baseline.py \
      --raw-dir data/raw \
      --token-budget $(cat data/derived/token_budget.txt) \
      --seed $SEED \
      --out data/derived/inference_logs/raw_seed${SEED}.csv
  python src/pipelines/run_null_baseline.py \
      --raw-dir data/raw \
      --seed $SEED \
      --out data/derived/inference_logs/null_seed${SEED}.csv
done
```

## 6️⃣ Evaluate (includes graph‑construction latency)
```bash
python src/pipelines/evaluate.py \
    --logs-dir data/derived/inference_logs \
    --graph-dir data/derived/intent_graphs \
    --graph-latency data/derived/graph_construction_latency.csv \
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
* F1 scores (micro‑averaged, multi‑label) for Graph, Raw, Null (only on ground‑truth tasks)
* Wilcoxon and t‑test p‑values, bootstrap CIs
* Total Latency (Construction + Inference) and reduction percentages
* Graph‑construction success rate