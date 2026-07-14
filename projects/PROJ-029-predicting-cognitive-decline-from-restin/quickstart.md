# Quickstart – end‑to‑end execution

This run‑book executes the full pipeline in the correct order. All scripts
must succeed and write their declared artefacts.

```bash
# 1. Verify dataset availability
python code/00_data_gate.py

# 2. Download raw BIDS data and filter subjects
python code/01_download_and_filter.py

# 3. Compute graph metrics (connectivity matrices → metrics)
python code/03_compute_graph_metrics.py

# 4. Train the prediction model
python code/04_train_model.py

# 5. Evaluate the trained model
python code/05_evaluate_model.py

# 6. Run permutation test (optional – can be skipped in CI)
# python code/06_permutation_test.py

# 7. Sensitivity analysis (optional)
# python code/07_sensitivity_analysis.py

# 8. Generate final report
python code/09_generate_report.py

# 9. Verify success criteria
python code/10_verify_success_criteria.py
```