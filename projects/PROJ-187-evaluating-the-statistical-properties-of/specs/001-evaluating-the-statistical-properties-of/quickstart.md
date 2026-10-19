# Quickstart: Running the Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed.
- Internet access (to download datasets).

## Step‑by‑Step

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

3. **Run a Smoke Test (single dataset, model, seed)**
   ```bash
   python -m src.cli.run_fidelity --smoke
   ```
   Produces `outputs/metrics/metric_results_smoke.json` and a small synthetic CSV for inspection.

4. **Run the Full Study (multiple datasets × 3 models × 3 seeds)**
   ```bash
   python -m src.cli.run_fidelity --full \
       --seeds 42 123 2026 \
       --max-epochs 30 \
       --early-stopping-delta 0.001 \
       --early-stopping-patience 3
   ```
   Expected outputs:
   - Synthetic CSVs under `outputs/synthetic/`
   - Metric JSON at `outputs/metrics/metric_results.json`
   - Control‑perturbation datasets under `outputs/control/`
   - Final report (`outputs/report/fidelity_report.pdf` and `.json`).

5. **Validate Outputs**
   ```bash
   pytest -q tests/contract
   ```
   The contract test checks that `metric_results.json` conforms to `contracts/metric_results.schema.yaml`.

## Expected Runtime & Resources
- **Total wall‑clock time** ≤ 360 minutes.  
- **Peak RAM** ≤ 7 GB (monitored; down‑sampling/drop‑column actions triggered automatically if exceeded).  

---


