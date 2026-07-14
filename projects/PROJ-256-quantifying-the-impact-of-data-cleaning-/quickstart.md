# Quickstart for the Quantifying Data Cleaning Impact Project

This document describes the commands required to run the full research
pipeline from end‑to‑end. All paths are relative to the repository root.

```bash
# 1️⃣ Ensure the virtual environment is active (the CI creates one automatically)
# If you are running locally, create it with:
# python -m venv.venv && source.venv/bin/activate && pip install -r requirements.txt

# 2️⃣ Download and verify raw datasets
python code/t011_ensure_data.py

# 3️⃣ Run the baseline statistical analysis on raw data
python code/t012_run_baseline_analysis.py

# 4️⃣ Record baseline metrics (produces data/processed/baseline_metrics.json)
python code/t013_record_baseline_metrics.py

# 5️⃣ Apply cleaning strategies and save cleaned variants
python code/t022_save_cleaned_datasets.py

# 6️⃣ Re‑analyse cleaned variants (produces data/processed/cleaned_metrics.json)
python code/t023_reanalyze_cleaned_variants.py

# 7️⃣ Generate permutation‑null datasets and compute false‑positive rate
python code/t032_permutation_null_fpr.py

# 8️⃣ Perform outlier‑threshold sweep and compute FPR / inconsistency rates
python code/t033_outlier_threshold_sweep.py

# 9️⃣ Run sensitivity analyses (dataset size, bootstrap, etc.)
python code/t030_dataset_size_sensitivity.py
python code/t031_bootstrap_variance.py

# 🔟 Create the comparison report (JSON)
python code/t040_create_comparison_report.py

# 1️⃣1️⃣ Generate visualisations
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py

# 1️⃣2️⃣ Assemble the final report (text + figures)
python code/t041_generate_final_report.py

# 1️⃣3️⃣ Verify that all expected artifacts exist
python code/run_quickstart_validation.py
```

After the above steps complete without error, you should find the following
artefacts in the repository:

* `data/processed/baseline_metrics.json`
* `data/processed/cleaned_metrics.json`
* `data/processed/null_fpr_metrics.json`
* `output/forest_plot.png`
* `output/ci_heatmap.png`
* `output/final_report.txt`

Feel free to explore the `data/processed/` directory for the intermediate
JSON files that contain the detailed statistical results.