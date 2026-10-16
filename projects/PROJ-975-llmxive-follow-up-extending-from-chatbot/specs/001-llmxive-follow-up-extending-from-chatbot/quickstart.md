# Quickstart: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

## Prerequisites

* Python 3.11+  
* `pip` (≥ 23)  
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
*Creates* `data/raw/tasks.json`, `data/raw/skills.json`, and updates `state/...yaml` with checksums.

### Step 2 – Execute Agent (all library sizes, pruning enabled)
```bash
python code/agent.py \
    --library-sizes 10 30 50 100 \
    --pruning \
    --overlap high
```
*Produces* `data/results/metrics.csv`.

### Step 3 – Run Analysis
```bash
python code/analysis.py --input data/results/metrics.csv
```
*Outputs* `data/results/analysis_report.json` containing:
* Tipping‑point estimate (`breakpoint_estimate`)  
* VIF values (`vif_library_size`, `vif_total_redundancy`)  
* p‑values for pruning effect  
* Supplemental sensitivity sweep results (`sensitivity_analysis.json`).

### Step 4 – Validate Contracts
```bash
pytest tests/contract/
```
All JSON/CSV files must pass schema validation; any failure aborts the pipeline.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **MemoryError** during data generation | `--overlap` set to “high” with default embedding dimension on a very small runner | Reduce `--overlap` to “medium” or lower the embedding dimension in `generate_data.py`. |
| **Schema mismatch** when running `pytest` | Generated JSON does not respect the schema (e.g., missing fields) | Re‑run `generate_data.py` after fixing the seed or overlap argument; ensure the script completes without warnings. |
| **Missing `edge_case` column** in `metrics.csv` | `logging_config.py` not updated after a code change | Verify that `logging_config.py` defines `LOG_COLUMNS` including `"edge_case"` and that `agent.py` uses `get_logger()` to write rows. |

---
