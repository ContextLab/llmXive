# Quickstart: Running the Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.
- Internet access (to download datasets).

## Step-by-Step

1. **Clone the repository and navigate to the project root**
   ```bash
   git clone <repo_url>
   cd yourrepo
   ```

2. **Create a fresh virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run a Smoke Test (T004)**
   Verify the pipeline with a single dataset, model, and seed:
   ```bash
   python -m src.cli.run_fidelity --smoke
   ```
   This produces `outputs/metrics/metric_results_smoke.json`.

4. **Run the Full Study (T005)**
   Execute the full 3x3x3 grid:
   ```bash
   python -m src.cli.run_fidelity --full \
       --seeds 42 123 2026 \
       --max-epochs 30 \
       --early-stopping-delta 0.001 \
       --early-stopping-patience 3
   ```
   This produces `outputs/metrics/metric_results.json` and synthetic CSVs.

5. **Validate Outputs**
   ```bash
   pytest -q tests/contract
   ```

## Expected Runtime & Resources
- Total wall-clock time ≤ 360 minutes.
- Peak RAM ≤ 7 GB.