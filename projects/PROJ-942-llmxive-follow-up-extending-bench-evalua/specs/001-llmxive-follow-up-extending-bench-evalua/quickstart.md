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
# The script streams the dataset, writes files under data/raw/, and records a SHA‑256 checksum.
```

## 3️⃣ Parse & Normalize Traces
```bash
python src/pipelines/parse_traces.py \
    --raw-dir data/raw \
    --out-csv data/derived/normalized_traces.csv
```

## 4️⃣ Compute Model Max Token Budget (for fair baseline truncation)
```bash
# For the OPT‑125m model we use a max context of 2048 tokens.
echo 2048 > data/derived/model_max_tokens.txt
```

## 5️⃣ Build Intent Graphs (LLM‑based, records construction latency)
```bash
python src/pipelines/build_intent_graph_llm.py \
    --input-csv data/derived/normalized_traces.csv \
    --out-dir data/derived/intent_graphs \
    --max-tokens $(cat data/derived/model_max_tokens.txt) \
    --seed 42 \
    --latency-out data/derived/graph_construction_latency.csv
```
*The script validates each JSON against `contracts/intent_graph.schema.yaml`, uses a deterministic LLM prompt with a fixed seed, and prunes low‑confidence nodes if the token budget is exceeded.*

## 6️⃣ Run Agents (three seeds)
```bash
for SEED in 101 202 303; do
  python src/pipelines/run_lightweight_agent.py \
      --graph-dir data/derived/intent_graphs \
      --seed $SEED \
      --out data/derived/inference_logs/lightweight_seed${SEED}.csv

  python src/pipelines/run_raw_baseline.py \
      --raw-dir data/raw \
      --max-tokens $(cat data/derived/model_max_tokens.txt) \
      --seed $SEED \
      --out data/derived/inference_logs/raw_seed${SEED}.csv

  python src/pipelines/run_null_baseline.py \
      --raw-dir data/raw \
      --seed $SEED \
      --out data/derived/inference_logs/null_seed${SEED}.csv
done
```

## 7️⃣ Evaluate (includes graph‑construction latency)
```bash
python src/pipelines/evaluate.py \
    --logs-dir data/derived/inference_logs \
    --graph-dir data/derived/intent_graphs \
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
- Micro‑averaged F1 for Graph, Raw, and Null conditions (ground‑truth subset).  
- Wilcoxon and paired‑t test p‑values, 95 % bootstrap confidence intervals.  
- **Online** inference latency per turn and percentage reduction.  
- Offline graph‑construction mean latency and overall success rate (≥ 95 %).  

---

