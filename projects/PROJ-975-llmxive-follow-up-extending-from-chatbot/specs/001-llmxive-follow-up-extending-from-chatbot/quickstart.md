# Quickstart: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

## Prerequisites
- Python 3.11+  
- `pip` ≥ 23  
- At least **7 GB** RAM (recommended)

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

## Step‑by‑Step Run (end‑to‑end reproducible)

### Step 1 – Copy & Verify Contracts
```bash
python code/copy_contracts.py
```
*Copies* the contract YAML files from the spec folder into `contracts/`, verifies SHA‑256, and writes the hashes to `data/checksums.json`.  

### Step 2 – Verify Contract Copy
```bash
pytest tests/contract/test_contract_copy.py
```
Ensures every contract file in `contracts/` matches the source hash.

### Step 3 – Generate Synthetic Data
```bash
python code/generate_data.py --seed 42 --overlap high
```
Creates `data/raw/tasks.json`, `data/raw/skills.json`, and updates `data/checksums.json`.  

### Step 4 – Verify Checksums
```bash
python code/write_checksums.py data/raw/tasks.json data/raw/skills.json
```
Recomputes the SHA‑256 digests and asserts they match the entries in `data/checksums.json`.  

### Step 5 – Validate Raw Data Schemas
```bash
pytest tests/contract/test_schemas.py -k "task or skill"
```
Ensures `tasks.json` and `skills.json` conform to their respective schemas.

### Step 6 – Align Logging Configuration
The `code/logging_config.py` file defines `LOG_COLUMNS`. **Make sure it exactly matches** the required header:

```
run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case
```

If you modify the header, update `LOG_COLUMNS` accordingly.

### Step 7 – Execute the Agent (full factorial)
```bash
python code/agent.py \
    --library-sizes 10 20 30 40 50 60 70 80 90 100 \
    --overlap low medium high \
    --pruning on off \
    --seed 42 \
    --randomize-tasks
```
*Runs* the agent for **every combination** of library size, overlap level, and pruning flag, shuffling tasks **independently** for each run. Produces `data/results/metrics.csv` and logs total runtime to `data/results/runtime_report.json`.

### Step 8 – Validate Execution Logs
```bash
pytest tests/contract/test_logging_schema.py
```
Validates `metrics.csv` (experiment_log schema) **and** the JSON‑L execution logs against `execution_log.schema.yaml`.

### Step 9 – Run the Statistical Analysis
```bash
python code/analysis.py --input data/results/metrics.csv
```
Writes `data/results/analysis_report.json` containing the breakpoint estimate, VIF values, pruning‑effect statistics (direct + mediation), power analysis, and total runtime.

### Step 10 – Validate All Outputs
```bash
pytest tests/contract/test_schemas.py -k "analysis_report"
```
Checks `analysis_report.json` against its schema.

### Step 11 – Verify End‑to‑end Reproducibility
Run the entire Quickstart on a fresh runner (e.g., a new GitHub Actions job) and confirm that the final `analysis_report.json` matches the one produced in Step 9.  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **MemoryError / Timeout** during `generate_data.py` | High overlap with full 384‑dim embeddings exceeds RAM | Reduce overlap (`--overlap medium`) or run with a smaller seed; the script will abort with a clear “Memory Limit Exceeded” message. |
| **Schema mismatch** when running `pytest` | Generated JSON missing required fields | Rerun `generate_data.py` after fixing the seed/overlap arguments; ensure the script completes without warnings. |
| **Missing columns** in `metrics.csv` | `logging_config.py` not aligned with required header | Verify `LOG_COLUMNS` matches the header listed in Step 6. |
| **CLI argument error** (e.g., `--library-size` not recognized) | Using an outdated command from a previous plan | Use the updated CLI shown in Step 7 (`--library-sizes` list, `--overlap` list, `--pruning on off`, `--randomize-tasks`). |
| **Pruning removes wrong skills** | Old `pruning.py` still present | Ensure `pruning.py` implements `prune_fr04(library)` as described in the methodology. |
| **Agent exits with NameError** | Missing import of `Tuple` (or other typing objects) | Verify `agent.py` imports `Tuple` from `typing`; the updated version does so. |
| **Metrics CSV not generated** | Integration test failure in `test_full_experiment.py` | Run the integration test directly to see the traceback; ensure all prior phases have passed. |
| **Analysis script crashes** | VIF > 5 or breakpoint optimizer fails to converge | The script now aborts with an informative error; adjust the predictor set or increase bootstrap iterations. |

---

