# Quickstart: llmXive follow-up – Masking Horizon & Semantic Density Study

## Prerequisites
- Python 3.11 or newer  
- `git` (to clone the repository)  

## Setup

```bash
# 1. Clone the repository (if not already)
git clone <repo-url>
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
  --num-trajectories <sufficient-number-of-trajectories> \
  --output data/raw/trajectories.jsonl \
  --seed 42
```
- Produces a **streamed JSON‑Lines** file (`trajectories.jsonl`) ≈ tens to hundreds of MB.  
- Balanced design across low, medium, and high density.  
- Logs the distribution of density levels and confirms the target count.

### Step 2 – Validate Trajectories (US‑1 gate)
```bash
python code/validate_trajectories.py \
  --input data/raw/trajectories.jsonl
```
- Exits with code 0 on success; any mismatch (entropy tolerance, count, density distribution) aborts the pipeline.

### Step 3 – Run Agent Simulation (FR‑002, FR‑009)
```bash
python code/simulate_agent.py \
  --input data/raw/trajectories.jsonl \
  --output data/logs/simulation_results.csv \
  --seed 42
```
- **Exhaustively** evaluates all horizons 1 → T (T = 20) for each trajectory.  
- Writes results **incrementally** to CSV with columns matching `contracts/simulation_log.schema.yaml`: `trajectory_id, density, horizon, evidence_age, success, retrieval_prob, clamped_entropy`.  
- Uses the stochastic success definition that includes independent task success probability.

### Step 4 – Validate Simulation Log (US‑2 gate)
```bash
python code/validate_simulation.py \
  --input data/logs/simulation_results.csv
```
- Streams the CSV and checks each row against the schema; exits with code 0 only if the file fully conforms.

### Step 5 – Analyze Results (FR‑003, FR‑004, FR‑006)
```bash
python code/analyze_results.py \
  --input data/logs/simulation_results.csv \
  --output-dir results
```
- Fits logistic regression with natural splines for density, horizon, evidence_age, and their interaction.  
- Prints regression coefficients, p‑values, and a brief text summary.  
- Writes `results/regime_map.png` (≤ 5 MB) and `results/regression_summary.json` (conforms to `contracts/regression_output.schema.yaml`).  
- Reports the count of `clamped_entropy` cases and their influence.

### Optional Step 6 – Sensitivity Analysis (FR‑010)
```bash
python code/sensitivity.py \
  --input data/raw/trajectories.jsonl \
  --output-dir results/sensitivity
```
- Re‑runs the full pipeline under alternative density weightings (0.5/0.5, 0.7/0.3) and α values (1.5, 2.5).  
- Stores each configuration's regression summary and surface plot.

## Verification Checklist
- `[ ]` `data/raw/trajectories.jsonl` exists, is valid JSONL, and passes `validate_trajectories.py`.  
- `[ ]` `data/logs/simulation_results.csv` contains the required columns (including `evidence_age`) and validates against `contracts/simulation_log.schema.yaml`.  
- `[ ]` `results/regime_map.png` is a PNG ≤ 5 MB with correctly labeled axes.  
- `[ ]` `results/regression_summary.json` conforms to `contracts/regression_output.schema.yaml`.  
- `[ ]` CI run time < 6 h and peak RAM < 7 GB (monitor via GitHub Actions logs).

## Troubleshooting
- **MemoryError**: Reduce `--num-trajectories` for a quick test (e.g., 100) and increase later.  
- **Entropy validation failures**: Ensure `code/config.py` lists the technical terms correctly; the generator will retry until the tolerance is met.  
- **Runtime exceeds limit**: Verify that the `--seed` flag is set (ensures deterministic behavior) and that no stray debug prints are slowing the loop.  
- **Clamped entropy diagnostics**: Check the `clamped_entropy_count` field in `regression_summary.json`; if high, review its impact in the regression diagnostics section.  
- **PNG validation failures**: Run `code/validate_regime_map.py --input results/regime_map.png` to ensure size ≤ 5 MB and that the file is a readable PNG.

---


