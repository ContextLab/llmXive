# Quickstart: Running the Network‑Proximity Epidemic Study

## Prerequisites
- **Python 3.11** (pre‑installed on GitHub Actions runners).  
- Internet access (to download the OpenFlights dataset).  
- No GPU required.

## 1. Install Dependencies
```bash
# From the repository root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Data Integrity (optional)
```bash
python -m src.pipeline.check_data_hashes
```
Computes SHA‑256 checksums of raw files under `data/raw/` and compares them to the hashes recorded in `state/projects/PROJ-263-...yaml`.

## 3. Run the Full Pipeline
```bash
python -m src.pipeline.run \
    --beta-values 0.01 0.06 0.11 0.16 0.21 0.26 0.31 0.36 0.41 0.46 0.51 \
    --lambdas 0.05 0.1 0.2 \
    --mc-runs 50 \
    --null-runs 10 \
    --max-runtime-hours 6 \
    --max-nodes 10000 \
    --seed 42
```
Key arguments:
- `--beta-values` now includes the upper bound **0.51** (FR‑013, plan_consistency‑27dca202).  
- `--mc-runs` is set to **50** to satisfy Constitution VII and improve statistical power (methodology‑bf8fe1c4, scientific_soundness‑134cd63e).  
- `--null-runs` remains at 10 as required by FR‑004 (synthetic‑null generation).  
- `--max-runtime-hours` activates the dynamic reduction logic (FR‑007).  
- `--max-nodes` caps the graph size; larger inputs are down‑sampled with a **degree‑preserving random node removal** scheme and logged (methodology‑cf6324a6).

The command writes:
- `data/derived/nodes.csv`, `edges.csv` (network).  
- `data/derived/simulation_results.csv` (primary runs).  
- `data/derived/null_results.csv` (null runs).  
- `data/derived/summary_stats.csv` (aggregated metrics).  
- Figures under `outputs/figures/`.

## 4. Validate Output Contracts
```bash
python -m src.pipeline.validate_contracts \
    --schema contracts/simulation_output.schema.yaml \
    --data data/derived/simulation_results.csv
```
Raises an error if any column violates the JSON‑Schema.

## 5. Inspect Results
```bash
# Quick summary
head data/derived/summary_stats.csv

# View figures (already generated)
display outputs/figures/threshold_curve.png
display outputs/figures/infection_trajectory.png
display outputs/figures/spatial_heatmap.png
```

## 6. Re‑run with Different Settings
All parameters are exposed via CLI flags; for a fast sanity check on a tiny graph:
```bash
python -m src.pipeline.run \
    --max-nodes 500 \
    --mc-runs 5 \
    --null-runs 5 \
    --seed 123
```
Useful during development (fits comfortably in < 1 min).  

---



