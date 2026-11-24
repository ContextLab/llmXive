# Quickstart: Running the Intent‑Graph Evaluation

> All commands assume you are at the repository root on a fresh GitHub Actions runner (or a comparable local environment).

## 1️⃣ Set Up the Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2️⃣ Download π‑Bench Data
```bash
python src/pipelines/download_pi_bench.py
# Streams the dataset, writes each task JSON under data/raw/, and records a SHA‑256 checksum.
```

## 3️⃣ Parse & Normalize Traces
```bash
python src/pipelines/parse_traces.py \
    --raw-dir data/raw \
    --out-csv data/derived/normalized_traces.csv
```

## 4️⃣ Infer Missing Intents (Deterministic LLM)
```bash
python src/pipelines/infer_missing_intents.py \
    --input-csv data/derived/normalized_traces.csv \
    --out-csv data/derived/inferred_intents.csv \
    --seed 42
```
*Uses `google/flan-t5-small` with fixed seed and greedy decoding.*

## 5️⃣ Build Intent Graphs (Inferred‑Only)
```bash
python src/pipelines/build_intent_graph.py \
    --traces-csv data/derived/normalized_traces.csv \
    --inferred-csv data/derived/inferred_intents.csv \
    --out-dir data/derived/intent_graphs \
    --latency-out data/derived/graph_construction_latency.csv \
    --max-tokens 2048
```
*Validates each JSON against `contracts/intent_graph.schema.yaml`.*

## 5b️⃣ Build Ground‑Truth‑Only Graphs (Control)
```bash
python src/pipelines/build_intent_graph_gt.py \
    --traces-csv data/derived/normalized_traces.csv \
    --out-dir data/derived/intent_graphs_gt \
    --latency-out data/derived/graph_construction_latency.csv \
    --max-tokens 2048
```
*Uses only ground‑truth intents; no inferred intents are incorporated.*

## 6️⃣ Run Agents (three seeds)
```bash
for SEED in 101 202 303; do
  python src/pipelines/run_lightweight_agent.py \
      --graph-dir data/derived/intent_graphs \
      --seed $SEED \
      --out data/derived/inference_logs/lightweight_seed${SEED}.csv

  python src/pipelines/run_lightweight_agent_gt.py \
      --graph-dir data/derived/intent_graphs_gt \
      --seed $SEED \
      --out data/derived/inference_logs/lightweight_gt_seed${SEED}.csv

  python src/pipelines/run_raw_baseline.py \
      --raw-dir data/raw \
      --max-tokens 2048 \
      --seed $SEED \
      --out data/derived/inference_logs/raw_seed${SEED}.csv

  python src/pipelines/run_null_baseline.py \
      --raw-dir data/raw \
      --seed $SEED \
      --out data/derived/inference_logs/null_seed${SEED}.csv
done
```

## 7️⃣ Evaluate (includes offline latency)
```bash
python src/pipelines/evaluate.py \
    --logs-dir data/derived/inference_logs \
    --graph-dir data/derived/intent_graphs \
    --graph-gt-dir data/derived/intent_graphs_gt \
    --graph-latency data/derived/graph_construction_latency.csv \
    --out-dir data/derived/eval_results
```
*Produces `summary.csv`, `report.md`, and PNG figures under `data/derived/eval_results/figures/`.*

## 8️⃣ Verify Contracts
```bash
pytest -q tests/contract
```
All Intent Graph JSON files must pass schema validation.

## 9️⃣ Inspect the Results
```bash
cat data/derived/eval_results/report.md
```
You will see:
- Single‑label accuracy, precision, recall, and F1 for Graph, Raw, Null, and Graph‑GT conditions (ground‑truth‑only control).  
- Wilcoxon and paired‑t test p‑values, 95 % bootstrap confidence intervals.  
- **Online** inference latency per turn and percentage reduction (SC‑002).  
- Offline LLM inference + graph‑construction latency (reported separately).  
- Graph‑construction success rate (≥ 95 %).  
- List of any “Null Graph” tasks for manual review.

---

