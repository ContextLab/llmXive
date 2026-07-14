# Quickstart Run‑Book

This document lists the commands that constitute the end‑to‑end pipeline.
Each command should exit with status 0 and produce the artefacts declared
in the task specifications.

```bash
# 1️⃣ Acquire raw data (already performed by earlier tasks)
# – no command needed here because the data lives in data/raw/

# 2️⃣ Baseline analysis on the raw dataset
python code/t012_run_baseline_analysis.py

# 3️⃣ Apply cleaning strategies and re‑analyse (already handled by other tasks)
python code/t023_reanalyze_cleaned_variants.py

# 4️⃣ Generate null‑FPR metrics and outlier‑threshold sweep (newly added)
python code/t033_outlier_threshold_sweep.py

# 5️⃣ Produce visualisations
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py

# 6️⃣ Final report assembly
python code/t041_generate_final_report.py
```

After running the above commands you should find the following files
under ``data/processed/``:

* ``baseline_metrics.json``
* ``cleaned_metrics.json``
* ``null_fpr_metrics.json``
* ``outlier_threshold_sweep.json``

And the visualisations under ``output/``.