# Quickstart – Running the full research pipeline

This document lists the commands that constitute a full end‑to‑end run of the
research pipeline.

```bash
# 1. Ensure reproducibility
python -c "import utils; utils.pin_random_seed(42)"

# 2. Download raw datasets (if not already present)
python code/data_loader.py

# 3. Baseline analysis on raw data
python code/t012_run_baseline_analysis.py

# 4. Apply cleaning strategies and save cleaned variants
python code/t022_save_cleaned_datasets.py

# 5. Re‑run analysis on cleaned variants (Task T023)
python code/t023_reanalyze_cleaned_variants.py

# 6. Generate comparison report
python code/t027_run_comparison.py

# 7. Produce final figures and summary
python code/t041_generate_final_report.py
```
