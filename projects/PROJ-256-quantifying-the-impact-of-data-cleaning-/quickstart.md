# Quickstart – end‑to‑end pipeline execution

The quickstart script runs the minimal set of tasks required to generate the
primary research artifacts for this feature. All paths are relative to the
repository root.

```bash
# 1️⃣ Install dependencies (once)
python -m pip install -r requirements.txt

# 2️⃣ Download raw datasets (if not already present)
python code/data_loader.py # this script handles downloading & checksum validation

# 3️⃣ Record baseline metrics (Task T013)
python code/t013_record_baseline_metrics.py

# 4️⃣ Apply cleaning strategies and re‑run analysis (Task T023 – cleaned metrics)
python code/t023_reanalyze_cleaned_variants.py

# 5️⃣ Generate comparison report and visualisations (Task T041)
python code/t041_generate_final_report.py

# 6️⃣ Verify that the expected artifacts exist
python code/run_quickstart_validation.py
```

After the above commands complete you should find the following files:

- `data/processed/baseline_metrics.json`
- `data/processed/cleaned_metrics.json`
- `data/processed/null_fpr_metrics.json`

These files are the core deliverables for the quantitative impact study.