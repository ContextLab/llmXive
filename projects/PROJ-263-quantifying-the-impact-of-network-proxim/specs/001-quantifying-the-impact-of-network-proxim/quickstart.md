# Quickstart: Running the Network‑Proximity Epidemic Study

## Prerequisites
- **Python 3.11** (available on GitHub Actions runners).  
- Internet access (to download the verified MDS JSON files).  
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
This command computes SHA‑256 checksums of raw files under `data/raw/` and compares them to the hashes recorded in `state/projects/PROJ-263-...yaml`.

## 3. Run the Full Pipeline
```bash
python -m src.pipeline.run \
    --beta-min 0.01 \
    --beta-max 0.5 \
    --beta-step 0.01 \
    --lambdas 0.05 0.1 0.2 \
    --mc-runs 50 \
    --null-runs 100 \
    --max-runtime-hours 6 \
    --max-nodes 10000 \
    --seed 42
```
Key arguments:
- `--beta-*` control the sweep (FR‑013).  
- `--lambdas` sets the spatial decay values (FR‑006).  
- `--mc-runs` and `--null-runs` enforce FR‑003 and FR‑004.  
- `--max-runtime-hours` triggers the dynamic reduction logic (FR‑007).  
- `--max-nodes` caps the graph size; larger inputs are down‑sampled (FR‑008).  

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
The script raises an error if any column violates the schema.

## 5. Inspect Results
```bash
# Quick summary
head data/derived/summary_stats.csv

# Plot figures (already generated)
display outputs/figures/threshold_curve.png
display outputs/figures/infection_trajectory.png
display outputs/figures/spatial_heatmap.png
```

## 6. Re‑run with Different Settings
All parameters are exposed via CLI flags; for a quick sanity check on a tiny graph:
```bash
python -m src.pipeline.run \
    --max-nodes 500 \
    --mc-runs 10 \
    --null-runs 20 \
    --seed 123
```
This is useful during development (fits comfortably in < 1 min).

---
