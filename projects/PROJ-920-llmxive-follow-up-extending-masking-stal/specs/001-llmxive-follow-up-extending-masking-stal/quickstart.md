# Quickstart: llmXive follow-up – Masking Horizon & Semantic Density Study

## Prerequisites
- Python 3.11 or newer  
- `git` (to clone the repository)  

## Setup

```bash
# 1. Clone the repository (if not already)
git clone 
cd llmxive-follow-up/projects/PROJ-920-llmxive-follow-up-extending-masking-stal

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install exact dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

### Step 1 – Generate Synthetic Trajectories (FR‑001)
```bash
python code/generate_trajectories.py \
  --num-trajectories 500 \
  --output data/raw/trajectories.json \
  --seed 42
```
- Produces `data/raw/trajectories.json` (on the order of tens to hundreds of megabytes).  
- Generates trajectories in a balanced design: approximately equal numbers of low-density, medium-density, and high-density cases.
- Logs the distribution of density levels and confirms the target trajectory count.

### Step 2 – Validate Trajectories (US‑1 gate)
```bash
python code/validate_trajectories.py \
  --input data/raw/trajectories.json
```
- Exits with code 0 on success; any mismatch (entropy tolerance, count, density distribution) aborts the pipeline.

### Step 3 – Run Agent Simulation (FR‑002, FR‑009)
```bash
python code/simulate_agent.py \
  --input data/raw/trajectories.json \
  --output data/logs/simulation_results.csv \
  --seed 42
```
- Samples multiple random horizons per trajectory and writes results incrementally to CSV.
- Uses the density-dependent heuristic solver: P(retrieval) = sigmoid(α * (density - β)), where α and β are scaling parameters to be determined during implementation.
- Flags clamped-entropy cases in the `clamped_entropy` column for diagnostic tracking.

### Step 4 – Analyze Results (FR‑003, FR‑004, FR‑006)
```bash
python code/analyze_results.py \
  --input data/logs/simulation_results.csv \
  --output-dir results
```
- Fits logistic regression with tensor-product splines for the density × horizon interaction.
- Prints regression coefficients, p‑values, and a brief text summary.  
- Writes `results/regime_map.png` (multidimensional surface) and `results/regression_summary.json`.
- Reports diagnostic results for clamped-entropy cases.

### Optional Step 5 – Sensitivity Analysis (FR‑010)
```bash
python code/sensitivity.py \
  --input data/raw/trajectories.json \
  --output-dir results/sensitivity
```
- Re‑runs the full pipeline under alternative density weightings (0.5/0.5, 0.7/0.3) and α values (1.5, 2.5).
- Stores each configuration's regression summary and plots.

## Verification Checklist
- `[ ]` `data/raw/trajectories.json` exists, is valid JSON, and passes `validate_trajectories.py`.  
- `[ ]` `data/logs/simulation_results.csv` contains the required columns (including `clamped_entropy`) and validates against `contracts/simulation_log.schema.yaml`.  
- `[ ]` `results/regime_map.png` is a PNG ≤ 5 MB with correctly labeled axes.  
- `[ ]` `results/regression_summary.json` conforms to `contracts/regression_output.schema.yaml`.  
- `[ ]` CI run time < 6 h and peak RAM < 7 GB (monitor via GitHub Actions logs).

## Troubleshooting
- **MemoryError**: Reduce `--num-trajectories` for a quick test (e.g., 100) and increase later.  
- **Entropy validation failures**: Ensure `code/config.py` lists the technical terms correctly; the generator will retry until the tolerance is met.  
- **Runtime exceeds limit**: Verify that the `--seed` flag is set (ensures deterministic behavior) and that no stray debug prints are slowing the loop.
- **Clamped entropy diagnostics**: Check the regression summary for a `clamped_entropy_count` field; if high, review the impact on the interaction term in the diagnostics section.

---
