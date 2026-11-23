# Quickstart – End‑to‑end pipeline

This run‑book executes the full analysis pipeline in the correct order.
Each command writes its declared artifacts to the `data/` tree.

```bash
# Phase 1 – data gate & download
python code/00_data_gate.py
python code/01_download_and_filter.py

# Phase 2 – preprocessing & graph construction
python code/02_preprocess_and_parcellate.py
python code/03_compute_graph_metrics.py

# Phase 3 – modeling
python code/04_train_model.py
python code/05_evaluate_model.py

# Phase 4 – permutation test & sensitivity
python code/06_permutation_test.py
python code/07_sensitivity_analysis.py

# Reporting
python code/09_generate_report.py
python code/10_verify_success_criteria.py
```
The quickstart will abort with a non‑zero exit code if any step fails,
ensuring that all required artifacts are produced.