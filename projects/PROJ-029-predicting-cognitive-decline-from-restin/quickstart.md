# Quickstart – end‑to‑end run‑book

The following commands execute the full analysis pipeline in the correct order.
They are safe to run on a fresh checkout; each step writes its declared
artefacts under the ``data/`` hierarchy.

```bash
# 1️⃣ Verify that the OpenNeuro dataset is reachable
python code/00_data_gate.py

# 2️⃣ Download raw BIDS data and filter for eligible subjects
python code/01_download_and_filter.py

# 3️⃣ Compute functional connectivity graphs and graph metrics
python code/03_compute_graph_metrics.py

# 4️⃣ Check feature collinearity (new script)
python code/08_collinearity_check.py

# 5️⃣ Train the Random Forest model with nested CV
python code/04_train_model.py

# 6️⃣ Evaluate the trained model and write performance report
python code/05_evaluate_model.py

# 7️⃣ Run the permutation significance test
python code/06_permutation_test.py

# 8️⃣ Generate the final human‑readable report
python code/09_generate_report.py

# 9️⃣ Verify that success criteria are met
python code/10_verify_success_criteria.py
```

After the pipeline finishes, you will find the following key artefacts:

- `data/processed/graph_metrics.csv` – node‑wise graph‑theoretic measures
- `data/processed/collinearity_report.json` – list of highly correlated features
- `data/processed/model.pkl` – serialized trained Random Forest
- `data/processed/performance_report.json` – nested‑CV performance metrics
- `data/processed/permutation_results.json` – permutation‑test ROC‑AUC distribution
- `data/artifacts/final_report.md` – narrative summary for end‑users

The scripts are deliberately lightweight and respect the resource limits
(≤ 2 CPU cores, ≤ 7 GB RAM) imposed by the CI environment. If any step
fails, consult the corresponding ``*.log`` files in ``data/artifacts/``.