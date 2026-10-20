# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv; python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42; python src/training/evaluate.py --metrics_out data/results_composition_only.json; 1 command(s) failed: python -m pytest -q tests/ (rc=4)

## Failing / missing run-book commands

- python src/data/loader.py --input data/raw/materials.csv --out data/processed/materials_processed.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/data/loader.py': [Errno 2] No such file or directory

- python src/training/train_gnn.py --data data/processed/materials_processed.csv --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/train_gnn.py': [Errno 2] No such file or directory

- python src/training/evaluate.py --metrics_out data/results_composition_only.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/training/evaluate.py': [Errno 2] No such file or directory

- python src/inference/predict.py --formula "Fe2O3" --out data/predictions.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py': [Errno 2] No such file or directory

- python src/interpret/extract_embeddings.py --out outputs/node_embeddings.npy -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py': [Errno 2] No such file or directory

- python src/interpret/pca_correlation.py --report_out interpretability_report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py': [Errno 2] No such file or directory

- python -m pytest -q tests/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/


