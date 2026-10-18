# Quickstart: Running the Fidelity Evaluation Pipeline

## Prerequisites
- Python 3.11 installed (GitHub Actions runner provides it).  
- Internet access (to download datasets).  

## Step‑by‑Step

1. **Clone the repository and navigate to the project root**  
   ```bash
   git clone 
   cd yourrepo
   ```

2. **Create a fresh virtual environment and install exact dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # pins sdv==1.12.0, torch==2.2.0+cpu, etc.
   ```

3. **Run the end‑to‑end pipeline**  
   ```bash
   python -m src.cli.run_fidelity \
       --seeds 42 123 2026 \
       --max-epochs 30 \
       --early-stopping-delta 0.001 \
       --early-stopping-patience 3
   ```
   - The script will download the three verified datasets, preprocess them, train the three generators, compute all metrics, and finally emit:
     - `outputs/synthetic/…/*.csv`
     - `outputs/metrics/metric_results.json`
     - `outputs/report/fidelity_report.pdf`
     - `outputs/report/fidelity_report.json`

4. **Validate outputs** (optional)  
   ```bash
   pytest -q tests/contract
   ```
   The contract test checks that `metric_results.json` conforms to `contracts/metric_results.schema.yaml`.

5. **Inspect the report**  
   Open `outputs/report/fidelity_report.pdf` in any PDF viewer. The JSON version can be inspected programmatically.

## Expected Runtime & Resources
- Total wall‑clock time ≤ 360 minutes on the GitHub Actions free tier.  
- Peak RAM ≤ 7 GB (the script aborts with a logged mitigation if exceeded).  

## Re‑producibility Checklist
- Random seeds are fixed (default: 42, 123, 2026).  
- All dataset URLs are hard‑coded and verified.  
- All generated files are checksum‑verified and version‑hashed.  

---

