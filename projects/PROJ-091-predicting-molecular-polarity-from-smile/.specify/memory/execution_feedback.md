# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/models/interpret.py`
  - script usage: `interpret.py [-h] --model MODEL --data DATA --clusters CLUSTERS`
  - argparse error: `interpret.py: error: the following arguments are required: --model, --data, --clusters`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download_qm9.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/data/download_qm9.py (rc=1); python code/main.py (rc=1); python code/data/preprocess_2d.py (rc=1); 1 declared deliverable(s) absent: data/processed/descriptors.parquet

## Failing / missing run-book commands

- python code/data/download_qm9.py -> rc=1
    Failed to download https://zenodo.org/record/7298654/files/qm9_smiles.csv.gz: 404 Client Error: NOT FOUND for url: https://zenodo.org/records/7298654/files/qm9_smiles.csv.gz
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/data/download_qm9.py", line 104, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/data/download_qm9.py", line 92, in main
    download_file(QM9_URL, output_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/data/download_qm9.py", line 36, in download_file
    response.raise_for_status()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/.venv/lib/python3.11/site-packages/requests/models.py", line 1167, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: NOT FOUND for url: https://zenodo.org/records/7298654/files/qm9_smiles.csv.gz
- python code/main.py -> rc=1
    cts/PROJ-091-predicting-molecular-polarity-from-smile/logs
2026-09-18 23:35:39,728 - __main__ - WARNING - Required file missing (may be downloaded later): /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/raw/qm9_smiles.csv
2026-09-18 23:35:39,728 - __main__ - INFO - Validating 2D-only compliance...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 149, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 144, in main
    success = run_pipeline()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 108, in run_pipeline
    if not validate_2d_compliance():
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 59, in validate_2d_compliance
    assert_no_3d_calls()
TypeError: assert_no_3d_calls() missing 1 required positional argument: 'code_str'
- python code/data/preprocess_2d.py -> rc=1
    Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/raw/qm9_smiles.csv.gz
- python code/data/feature_clustering.py -> rc=1
    uet(data_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/.venv/lib/python3.11/site-packages/pandas/io/parquet.py", line 671, in read_parquet
    return impl.read(
           ^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/.venv/lib/python3.11/site-packages/pandas/io/parquet.py", line 253, in read
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/.venv/lib/python3.11/site-packages/pandas/io/parquet.py", line 141, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 939, in get_handle
    handle = open(handle, ioargs.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/descriptors.parquet'
- python code/models/train_lightgbm.py -> rc=1
    Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/processed/descriptors.parquet
- python code/models/evaluate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/evaluate.py", line 62, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/evaluate.py", line 59, in main
    run_evaluation(model_path, data_path, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/evaluate.py", line 44, in run_evaluation
    with open(model_path, "rb") as f:
         ^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/model.pkl'
- python code/models/interpret.py -> rc=2
    usage: interpret.py [-h] --model MODEL --data DATA --clusters CLUSTERS
                    [--output OUTPUT]
interpret.py: error: the following arguments are required: --model, --data, --clusters

## Declared deliverables still missing

- data/processed/descriptors.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **133885** real records with fields: inchi, SMILES, rotational_constant_a, rotational_constant_b, rotational_constant_c, dipole_moment, polarizability, homo, lumo, gap, r2, zero_point_energy, u0, u298, h298, g298, heat_capacity, split, __index_level_0__.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset

# Load the QM9 dataset using a specific config that contains the full data
dataset_dict = load_dataset('jablonkagroup/qm9', 'raw_data')

# Compute total number of records across all splits
total_records = sum(len(split) for split in dataset_dict.values())
print(f"RECORDS={total_records}")

# Print the field names from the first split (all splits share the same schema)
first_split = next(iter(dataset_dict.values()))
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `assert_no_3d_calls` — defined in `code/utils/validators.py`; called 2 way(s):

- code/main.py: assert_no_3d_calls()
- code/tests/verification/test_quickstart_validation.py: assert_no_3d_calls(mock_3d_call)

Make `assert_no_3d_calls` in `code/utils/validators.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/tests/verification/test_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/save_descriptors.py` — NOT invoked by the run-book
    - `code/data/feature_clustering.py` — IS a run-book command
    - `code/data/preprocess_2d.py` — IS a run-book command
    - `code/data/split_data.py` — NOT invoked by the run-book
    - `code/models/train_lightgbm.py` — IS a run-book command
    - `code/models/generate_stability_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/descriptors.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/verification/test_quickstart_validation.py`, `code/data/save_descriptors.py`, `code/data/feature_clustering.py`, `code/data/preprocess_2d.py`, `code/data/split_data.py`, `code/models/train_lightgbm.py`, `code/models/generate_stability_report.py`, `code/models/generate_shap_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/descriptors.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/tests/verification/test_quickstart_validation.py`, `code/data/save_descriptors.py`, `code/data/feature_clustering.py`, `code/data/split_data.py`, `code/models/train_lightgbm.py`, `code/models/generate_stability_report.py`, `code/models/generate_shap_report.py`.

### `data/processed/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/train_lightgbm.py`, `code/models/train_final.py`, `code/models/generate_stability_report.py`, `code/models/evaluate.py`, `code/models/generate_shap_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/train_lightgbm.py`, `code/models/train_final.py`, `code/models/generate_stability_report.py`, `code/models/evaluate.py`, `code/models/generate_shap_report.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/processed/descriptors.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/verification/test_quickstart_validation.py`, `code/data/save_descriptors.py`, `code/data/feature_clustering.py`, `code/data/preprocess_2d.py`, `code/data/split_data.py`, `code/models/train_lightgbm.py`, `code/models/generate_stability_report.py`, `code/models/generate_shap_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/processed/descriptors.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/tests/verification/test_quickstart_validation.py`, `code/data/save_descriptors.py`, `code/data/feature_clustering.py`, `code/data/split_data.py`, `code/models/train_lightgbm.py`, `code/models/generate_stability_report.py`, `code/models/generate_shap_report.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/raw/qm9_smiles.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/preprocess_2d.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/raw/qm9_smiles.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/data/loader.py`, `code/data/download_qm9.py`.

### `zenodo.org/records/7298654/files/qm9_smiles.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/preprocess_2d.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `zenodo.org/records/7298654/files/qm9_smiles.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/data/loader.py`, `code/data/download_qm9.py`.
