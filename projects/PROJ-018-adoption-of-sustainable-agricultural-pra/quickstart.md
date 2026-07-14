# Quickstart – end‑to‑end run‑book

The following commands constitute the reproducible research pipeline.
They must all exit with status ``0`` and produce the declared artifacts.

```bash
# 1. Acquire (or fall back to) raw survey data
python code/01_download_data.py --synthetic

# 2. Clean the raw data
python code/02_clean_data.py

# 3. Engineer features and compute validity metrics
python code/03_engineer_features.py

# 4. Fit the logistic regression model
python code/04_model_analysis.py

# 5. Generate the PDF report
python code/05_generate_report.py
```