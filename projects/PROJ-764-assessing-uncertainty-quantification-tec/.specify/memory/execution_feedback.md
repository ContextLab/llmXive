# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/main.py (rc=1); python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); 6 declared deliverable(s) absent: data/processed/features_test_20pca.csv; data/processed/features_train_20pca.csv; data/processed/features_val_20pca.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-10-03 15:16:38,630 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: Non-scalable fonts are not supported
2026-10-03 15:16:38,700 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-03 15:16:38 - pipeline - INFO - Starting main pipeline with timeout=5.0 hours
2026-10-03 15:16:38,902 - pipeline - INFO - Starting main pipeline with timeout=5.0 hours
2026-10-03 15:16:38 - pipeline - INFO - --- PIPELINE START ---
2026-10-03 15:16:38,902 - pipeline - INFO - --- PIPELINE START ---
2026-10-03 15:16:38 - pipeline - INFO - CONFIG: "Assessing Uncertainty Quantification Pipeline"
2026-10-03 15:16:38,902 - pipeline - INFO - CONFIG: "Assessing Uncertainty Quantification Pipeline"
2026-10-03 15:16:38 - pipeline - INFO - Phase 1: Downloading OQMD Dataset...
2026-10-03 15:16:38,902 - pipeline - INFO - Phase 1: Downloading OQMD Dataset...
2026-10-03 15:16:38,902 - data.download - ERROR - Data file not found: data/raw/oqmd.parquet. Run T005a first.
- python code/data/download.py -> rc=1
    2026-10-03 15:16:40,335 - __main__ - ERROR - Data file not found: data/raw/oqmd.parquet. Run T005a first.
- python code/data/preprocess.py -> rc=1
    [0.8, 0.1, 0.1], 'split_type': 'stratified', 'timeout_hours': 5.0, 'data': {'raw_dir': 'data/raw', 'processed_dir': 'data/processed', 'download_url': 'https://huggingface.co/datasets/materials-toolkits/oqmd'}, 'model': {'hidden_dims': [64, 32], 'dropout_rate': 0.2}, 'training': {'epochs': 100, 'lr': 0.001, 'batch_size': 64}, 'uq': {'mc_dropout_passes': 30, 'mc_dropout_dropout_rate': 0.2, 'ensemble_size': 5, 'gp_inducing_points': 500}, 'paths': {'results_dir': 'results', 'logs_dir': 'logs'}}
Loading data...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 157, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 143, in main
    df = load_data()
         ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 28, in load_data
    raise FileNotFoundError(
FileNotFoundError: Data file not found: data/raw/oqmd.parquet. Please run T005 (download.py) to materialize the dataset first.
- python code/models/deep_ensemble.py --seed <random_seed> -> rc=1
    132, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/models/deep_ensemble.py", line 115, in main
    models = train_ensemble(input_dim, n_models=n_models, base_seed=seed)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/models/deep_ensemble.py", line 85, in train_ensemble
    model = train_single_model(input_dim, seed, epochs=100)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/models/deep_ensemble.py", line 57, in train_single_model
    X, y = load_data("train")
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/models/deep_ensemble.py", line 41, in load_data
    raise FileNotFoundError(f"Required data file not found: {path}. Ensure T006b3 has completed.")
FileNotFoundError: Required data file not found: data/processed/features_train_20pca.csv. Ensure T006b3 has completed.
- python code/models/sparse_gp.py --seed -> rc=1
    2026-10-03 15:16:44,943 - ERROR - Required artifact missing: data/processed/pca_transformer.pkl
2026-10-03 15:16:44,943 - sparse_gp - CRITICAL - CRITICAL: Missing required artifacts: ['data/processed/features_train_20pca.csv', 'data/processed/features_test_20pca.csv', 'data/processed/pca_transformer.pkl']. T015a verification failed. Cannot proceed to training (T015b).
2026-10-03 15:16:44,943 - CRITICAL - CRITICAL: Missing required artifacts: ['data/processed/features_train_20pca.csv', 'data/processed/features_test_20pca.csv', 'data/processed/pca_transformer.pkl']. T015a verification failed. Cannot proceed to training (T015b).
2026-10-03 15:16:44,943 - sparse_gp - ERROR - Fitting FAILED: CRITICAL: Missing required artifacts: ['data/processed/features_train_20pca.csv', 'data/processed/features_test_20pca.csv', 'data/processed/pca_transformer.pkl']. T015a verification failed. Cannot proceed to training (T015b).
2026-10-03 15:16:44,943 - ERROR - Fitting FAILED: CRITICAL: Missing required artifacts: ['data/processed/features_train_20pca.csv', 'data/processed/features_test_20pca.csv', 'data/processed/pca_transformer.pkl']. T015a verification failed. Cannot proceed to training (T015b).
- python code/uq/compute_calibration_report.py -> rc=1
    pute_calibration_report.py", line 148, in main
    df = load_predictions(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/uq/compute_calibration_report.py", line 34, in load_predictions
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: results/uq_predictions_decomposed.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/uq/compute_calibration_report.py", line 184, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/uq/compute_calibration_report.py", line 148, in main
    df = load_predictions(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/uq/compute_calibration_report.py", line 34, in load_predictions
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: results/uq_predictions_decomposed.csv
- python code/uq/screening.py -> rc=1
    2026-10-03 15:16:46,369 - __main__ - INFO - Starting screening process
2026-10-03 15:16:46,370 - __main__ - INFO - Input file: results/uq_predictions.csv
2026-10-03 15:16:46,370 - __main__ - INFO - Methods: ['deep_ensemble', 'mc_dropout']
2026-10-03 15:16:46,370 - __main__ - INFO - Risk aversion: 1.0
2026-10-03 15:16:46,370 - __main__ - ERROR - File not found: Input file not found: results/uq_predictions.csv

## Declared deliverables still missing

- data/processed/features_test_20pca.csv
- data/processed/features_train_20pca.csv
- data/processed/features_val_20pca.csv
- data/processed/raw_test.csv
- data/raw/oqmd.parquet
- data/validation_report.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **561881** real records with fields: name, formula, spacegroup, nelements, nsites, energy_per_atom, formation_energy_per_atom, band_gap, volume_per_atom, magnetization_per_atom, atomic_volume_per_atom, volume_deviation, split, __index_level_0__.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset, concatenate_datasets

# Load the dataset using a config that contains the full records
ds_dict = load_dataset("jablonkagroup/oqmd", "raw_data")

# Combine all splits into a single Dataset
if isinstance(ds_dict, dict):
    ds = concatenate_datasets(list(ds_dict.values()))
else:
    ds = ds_dict

# Count and print total records
print(f"RECORDS={len(ds)}")

# Print field names from the first record (if any)
if len(ds) > 0:
    print("FIELDS=" + ",".join(ds[0].keys()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features_test_20pca.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline_nn.py` — NOT invoked by the run-book
    - `code/models/run_single_seed.py` — NOT invoked by the run-book
    - `code/models/sparse_gp.py` — IS a run-book command
    - `code/models/sparse_gp_runner.py` — NOT invoked by the run-book
    - `code/models/mc_dropout.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_test_20pca.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_train_20pca.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline_nn.py` — NOT invoked by the run-book
    - `code/models/sparse_gp.py` — IS a run-book command
    - `code/models/mc_dropout.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_train_20pca.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_val_20pca.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/baseline_nn.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_val_20pca.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_ece_seeds.py` — NOT invoked by the run-book
    - `code/uq/compute_calibration_report.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/raw_test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/oqmd.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/oqmd.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — IS a run-book command
    - `code/data/generate_validation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/features_train_20pca.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/baseline_nn.py`, `code/models/sparse_gp.py`, `code/models/mc_dropout.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/features_train_20pca.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/baseline_nn.py`, `code/models/sparse_gp.py`, `code/models/mc_dropout.py`.

### `data/raw/oqmd.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/preprocess.py`, `code/data/download.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/oqmd.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/preprocess.py`, `code/data/download.py`.

### `results/uq_predictions.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/uq/apply_decomposition.py`, `code/uq/screening.py`, `code/uq/uncertainty_decomposition.py`, `code/uq/decompose_and_update_predictions.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/uq_predictions.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/uq/apply_decomposition.py`, `code/uq/validate_uq.py`, `code/uq/screening.py`, `code/uq/uncertainty_decomposition.py`, `code/uq/decompose_and_update_predictions.py`.

### `results/uq_predictions_decomposed.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/uq/metrics.py`, `code/uq/compute_calibration_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/uq_predictions_decomposed.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/uq/metrics.py`, `code/uq/compute_calibration_report.py`, `code/uq/plot_reliability.py`.
