# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/loader.py --input data/raw/materials.parquet --out data/processed/materials_processed.csv 2>&1 | tee outputs/test_logs/loader.log`
  - script usage: `loader.py [-h] --input INPUT --out OUT [--report REPORT]`
  - argparse error: `loader.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/loader.log`
- run-book command: `python -m src.training.train_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_gnn.log`
  - script usage: `train_gnn.py [-h] --data DATA [--seed SEED] [--max_epochs MAX_EPOCHS]`
  - argparse error: `train_gnn.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/train_gnn.log`
- run-book command: `python -m src.training.evaluate --metrics_out data/results_composition_only.json 2>&1 | tee outputs/test_logs/evaluate.log`
  - script usage: `evaluate.py [-h] --metrics_out METRICS_OUT [--seed SEED]`
  - argparse error: `evaluate.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/evaluate.log`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: python -m pytest tests/contract/ -q --junitxml=outputs/test_logs/contract.xml 2>&1 | tee outputs/test_logs/contract.log (rc=4); python src/data/loader.py --input data/raw/materials.parquet --out data/processed/materials_processed.csv 2>&1 | tee outputs/test_logs/loader.log (rc=2); python -m src.training.train_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_gnn.log (rc=2)

## Failing / missing run-book commands

- python -m pytest tests/contract/ -q --junitxml=outputs/test_logs/contract.xml 2>&1 | tee outputs/test_logs/contract.log -> rc=4

- generated xml file: /home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/outputs/test_logs/contract.xml -
no tests ran in 0.00s

ERROR: file or directory not found: 2>&1


- python src/data/loader.py --input data/raw/materials.parquet --out data/processed/materials_processed.csv 2>&1 | tee outputs/test_logs/loader.log -> rc=2

usage: loader.py [-h] --input INPUT --out OUT [--report REPORT]
loader.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/loader.log

- python -m src.training.train_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_gnn.log -> rc=2

usage: train_gnn.py [-h] --data DATA [--seed SEED] [--max_epochs MAX_EPOCHS]
                    [--patience PATIENCE] [--batch_size BATCH_SIZE]
train_gnn.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/train_gnn.log

- python -m src.training.train_structure_gnn --data data/processed/materials_processed.csv --seed 42 2>&1 | tee outputs/test_logs/train_structure_gnn.log -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: No module named src.training.train_structure_gnn

- python -m src.training.evaluate --metrics_out data/results_composition_only.json 2>&1 | tee outputs/test_logs/evaluate.log -> rc=2

usage: evaluate.py [-h] --metrics_out METRICS_OUT [--seed SEED]
                   [--max_epochs MAX_EPOCHS] [--batch_size BATCH_SIZE]
                   [--patience PATIENCE]
evaluate.py: error: unrecognized arguments: 2>&1 | tee outputs/test_logs/evaluate.log

- python -m src.training.evaluate_structure --metrics_out data/results_structure_aware.json --comparison_out data/comparison_summary.csv 2>&1 | tee outputs/test_logs/evaluate_structure.log -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-033-predicting-material-properties-from-comp/bin/python: No module named src.training.evaluate_structure

- python -m src.inference.predict --formula "Fe2O3" --out data/predictions.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 86, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 59, in main
    state = _load_latest_checkpoint()
            ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/inference/predict.py", line 35, in _load_latest_checkpoint
    raise FileNotFoundError("No GNN checkpoint files found in outputs/")
FileNotFoundError: No GNN checkpoint files found in outputs/

- python -m src.interpret.extract_embeddings --out outputs/node_embeddings.npy -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 89, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/extract_embeddings.py", line 36, in main
    raise FileNotFoundError(f"Processed data not found at {data_path}")
FileNotFoundError: Processed data not found at data/processed/materials_processed.csv

- python -m src.interpret.pca_correlation --report_out interpretability_report.md -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py", line 68, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/src/interpret/pca_correlation.py", line 36, in main
    raise FileNotFoundError(f"Embeddings file not found at {embeddings_path}")
FileNotFoundError: Embeddings file not found at outputs/node_embeddings.npy

- python -m pytest tests/ -q --junitxml=outputs/test_logs/full_suite.xml 2>&1 | tee outputs/test_logs/full_suite.log -> rc=4

- generated xml file: /home/runner/work/llmXive/llmXive/projects/PROJ-033-predicting-material-properties-from-comp/outputs/test_logs/full_suite.xml -
no tests ran in 0.00s

ERROR: file or directory not found: 2>&1


