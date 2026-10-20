# Quickstart: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Prerequisites
* Python 3.11+  
* `pip` ≥ 23  
* At least **7 GB** RAM (recommended)

## Installation

```bash
# 1. Enter the project directory
cd projects/PROJ-975-llmxive-follow-up-extending-from-chatbot

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install exact dependencies
pip install -r code/requirements.txt
```

## Running the Full Experiment

### Step 1 – Generate Synthetic Data
```bash
python code/generate_data.py --seed 42 --overlap high
```
*Creates* `data/raw/tasks.json`, `data/raw/skills.json`, and `data/checksums.json` (project‑owned).

### Step 2 – Execute Agent (all library sizes, pruning enabled)
```bash
python code/agent.py \
    --library-sizes 10 20 30 40 50 60 70 80 90 100 \
    --overlap high \
    --pruning
```
*Produces* `data/results/metrics.csv` with the exact header:
```
run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case
```

### Step 3 – Align Logging Configuration
The `code/logging_config.py` file defines `LOG_COLUMNS`. **Before running the agent, ensure that `LOG_COLUMNS` exactly matches the header above** (see Phase 3b in the plan). This guarantees schema validation will succeed.

### Step 4 – Run Analysis
```bash
python code/analysis.py --input data/results/metrics.csv
```
*Outputs* `data/results/analysis_report.json` containing:
- `breakpoint_estimate`
- VIF values
- Pruning‑effect statistics
- Permutation and likelihood‑ratio p‑values
- Optional sensitivity sweep results.

### Step 5 – Validate Contracts
```bash
pytest tests/contract/
```
All JSON and CSV files must pass schema validation; any failure aborts the pipeline.

### Step 6 – Verify End‑to‑End Reproducibility
Run the Quickstart steps on a fresh runner (e.g., in a new GitHub Actions job) to confirm that the same `analysis_report.json` is produced.  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **Timeout / MemoryError** during data generation | High overlap with default embedding dimension exceeds RAM | Reduce overlap (`--overlap medium`) or increase the runner’s memory limit (if possible). |
| **Schema mismatch** when running `pytest` | Generated JSON missing required fields | Rerun `generate_data.py` after fixing the seed/overlap arguments; ensure the script completes without warnings. |
| **Missing columns** in `metrics.csv` | `logging_config.py` not updated | Verify that `LOG_COLUMNS` in `logging_config.py` matches the required header (see Quickstart Step 3). |
| **Embedding dimension error** (`shapes (384,) and (768,) not aligned`) | Mismatch between model output and schema | Ensure the skill schema expects 384 dimensions (as defined) and that `sentence-transformers/all-MiniLM-L6-v2` is used. |
| **Pruning removes wrong skills** | Old heuristic still in code | Confirm `pruning.py` implements the “high similarity” rule (max cosine > 0.70). |

---


