# Quickstart – Running the full research pipeline

This document lists the commands that constitute the end‑to‑end execution
of the quantifying‑data‑cleaning‑impact pipeline. Run them sequentially from
the repository root.

```bash
# 1️⃣ Install dependencies (run once)
pip install -r requirements.txt

# 2️⃣ Set up logging & reproducibility
python -c "import utils; utils.setup_logging('INFO'); utils.pin_random_seed(42)"

# 3️⃣ Download raw datasets (if not already present)
python code/data_loader.py

# 4️⃣ Baseline analysis on raw data
python code/t012_run_baseline_analysis.py

# 5️⃣ Apply cleaning strategies & save cleaned variants
python code/t022_save_cleaned_datasets.py

# 6️⃣ Re‑run analysis on cleaned data
python code/t023_reanalyze_cleaned_variants.py

# 7️⃣ Permutation‑based false‑positive‑rate estimation (T032)
python code/t032_permutation_null_fpr.py

# 8️⃣ Generate comparison reports & visualisations
python code/t027_run_comparison.py
python code/t034_generate_forest_plot.py
python code/t035_generate_ci_heatmap.py

# 9️⃣ Final aggregated report
python code/t041_generate_final_report.py
```

After the above steps complete, you should find the following artefacts
under `data/processed/`:

- `baseline_metrics.json`
- `cleaned_metrics.json`
- `null_fpr_metrics.json`

and visualisations under `output/`.