# Quickstart: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Prerequisites
- Python 3.11 or newer
- `git`
- Internet access (only to fetch Python packages)

## Installation
```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-866-llmxive-follow-up-extending-foundation-p

# 2️⃣ Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install exact dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
All commands are deterministic (seed = 42) and will produce the artifacts required by the contracts.

### 1️⃣ Generate synthetic workflows
```bash
python src/cli/run_simulation.py --generate \
    --seed 42 \
    --count 500
```
*Output*: `data/raw/workflows.json` (validated workflows).

### 2️⃣ Execute Full‑Context baseline
```bash
python src/cli/run_simulation.py --execute --mode full
```
*Output*: `data/processed/full_context_logs.json`.

### 3️⃣ Execute Compressed‑Context variants
```bash
python src/cli/run_simulation.py --execute --mode compressed \
    --depths 0,1,2,3,4,5,6,7,8,9,10
```
*Output*: `data/processed/compressed_context_logs.json`.

### 4️⃣ Verify Invalid‑Workflow Exclusion Report
```bash
python code/utils/verify_invalid_exclusion.py \
    --workflows data/raw/workflows.json \
    --report data/results/invalid_exclusion_report.json
```
*Output*: `invalid_exclusion_report.json` containing `invalid_workflow_count`, `excluded_count`, and `status`.

### 5️⃣ Prepare Step‑Level Outcome Data
```bash
python src/cli/run_simulation.py --prepare-step-data
```
*Output*: `data/processed/step_outcomes.json` (flat per‑step binary outcomes for GEE).

### 6️⃣ Run statistical analysis
```bash
python src/cli/run_simulation.py --analyze \
    --bootstraps 1000   # matches verified fact
```
*Outputs*:
- `data/results/tradeoff_curve.csv` (SSoT for the paper)  
- `data/results/threshold_report.json` (safe‑zone threshold, 95 % CI)  
- `data/results/run_metrics.json` (wall‑clock time, invalid‑workflow proportion, estimated power)  
- `data/results/analysis_results.json` (validated against `contracts/analysis_results.schema.yaml`)

### 7️⃣ Verify everything
```bash
pytest -v
```
Tests include:
- Schema validation against `contracts/*.schema.yaml`  
- Oracle independence (`test_oracle_independence.py`)  
- Edge‑case handling (`test_edge_cases.py`)  
- Analysis‑results schema validation (`test_analysis_results_schema.py`)  

## Interpreting the Results
- **Trade‑off curve**: Open `data/results/tradeoff_curve.csv` in a spreadsheet or run `python -c "import pandas as pd; print(pd.read_csv('data/results/tradeoff_curve.csv'))"` to see the relationship between context reduction and error rate.  
- **Safe operating zone**: `threshold_report.json` contains:
  ```json
  {
    "threshold_pct": "to be determined based on preliminary analysis",
    "confidence_interval": [estimated lower limit, estimated upper limit]
  }
  ```
  This means reducing context by up to **[deferred]** keeps policy‑violation error ≤ 1 % with 95 % confidence.

- **Reproducibility**: The SHA‑256 hashes of all generated files are recorded in `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`. Re‑run the pipeline on a fresh GitHub Actions runner; the hashes must match exactly.

## Clean‑up (optional)
```bash
rm -rf data/raw/* data/processed/* data/results/*
```
