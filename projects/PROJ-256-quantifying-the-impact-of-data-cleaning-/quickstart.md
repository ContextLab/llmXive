# Quickstart Run‑Book

This document lists the commands that constitute the end‑to‑end pipeline.
Run them in order from top to bottom. Each command should exit with status
``0`` and produce the artefacts declared in the specification.

```bash
# 1. Acquire raw datasets
python code/data_loader.py

# 2. Run baseline statistical analysis on the raw (un‑cleaned) data
python code/t012_run_baseline_analysis.py

# 3. Record baseline metrics to JSON
python code/t013_record_baseline_metrics.py

# 4. Apply cleaning strategies and save cleaned datasets
python code/t022_save_cleaned_datasets.py

# 5. Re‑run analysis on each cleaned variant
python code/t023_reanalyze_cleaned_variants.py

# 6. Generate null‑permutation datasets for false‑positive‑rate estimation
python code/t032_permutation_null_fpr.py

# 7. (Optional) Sensitivity analyses, visualisations and final report
python code/t030_dataset_size_sensitivity.py
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py
python code/t041_generate_final_report.py
```

After the pipeline finishes, you should find the following artefacts:

* `data/processed/baseline_metrics.json`
* `data/processed/cleaned_metrics.json`
* `data/processed/null_fpr_metrics.json`
* Visualisations under `output/` (forest plot, heatmap, …)