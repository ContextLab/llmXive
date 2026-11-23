# code/

This directory contains the analysis pipeline scripts for the project
"Predicting Cognitive Decline from Resting-State fMRI Network Topology".

Expected scripts (per tasks.md):
- 00_data_gate.py
- 01_download_and_filter.py
- 02_preprocess_and_parcellate.py
- 03_compute_graph_metrics.py
- 04_train_model*.py
- 05_evaluate_model.py
- 06_permutation_test.py
- 07_sensitivity_analysis.py
- 08_collinearity_check.py
- 09_generate_report.py
- 10_verify_success_criteria.py
- 11_external_outcome_check.py
- utils/ (io, graph, stats, logger)
- requirements.txt

Run order is defined in the repository quickstart.md.
