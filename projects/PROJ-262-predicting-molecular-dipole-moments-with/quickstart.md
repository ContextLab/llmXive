# Quick‑start Guide

This document drives the end‑to‑end run‑book executed by the CI pipeline.
It sequentially invokes the scripts that generate data, train models,
evaluate performance and finally produce the summary report.

```bash
# 1️⃣ Download the QM9 dataset (with retry logic)
python code/data/download_qm9.py

# 2️⃣ Create a reproducible 10 k subset
python code/data/create_subset.py

# 3️⃣ Generate processed data artefacts (the missing step that caused T020 to fail)
python code/data/generate_processed_data.py

# 4️⃣ Train the SchNet‑style GNN (seeded, early‑stopping)
python code/training/train_gnn.py

# 5️⃣ Train the Random Forest baseline
python code/training/train_rf.py

# 6️⃣ Produce performance plots
python code/analysis/generate_performance_plots.py

# 7️⃣ Produce statistical significance report
python code/analysis/generate_significance.py

# 8️⃣ Generate the final markdown summary
python code/generate_summary.py

# 9️⃣ Validate that all required artefacts exist and are well‑formed
python code/quickstart_validation.py
```

Follow the steps in order. The scripts are deliberately lightweight and
designed to run on a CPU‑only environment within the resource limits
defined by the ``utils`` decorators.