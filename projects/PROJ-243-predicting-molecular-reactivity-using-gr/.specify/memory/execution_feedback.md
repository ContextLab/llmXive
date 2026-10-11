# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py --dataset qm9 --output data/raw`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/utils/checksums.py --dir data/raw --output data/raw/checksums.json; python code/train/trainer.py --epochs 50 --device cpu; python code/train/eval.py --model-path artifacts/models/ --output artifacts/; 2 command(s) failed: python code/data/download.py --dataset qm9 --output data/raw (rc=1); python code/02_preprocess_graphs.py --input data/raw/qm9_subset.parquet --output data/processed (rc=1); 3 declared deliverable(s) absent: data/raw/kinetic_dataset_raw.csv; data/raw/qm9_subset.parquet; data/raw/reference_substructures_raw.csv

## Failing / missing run-book commands

- python code/data/download.py --dataset qm9 --output data/raw -> rc=1
3-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/datasets/load.py", line 2587, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/datasets/load.py", line 2259, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/datasets/load.py", line 1904, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/lib/python3.11/site-packages/datasets/load.py", line 1850, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'qm9' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/qm9 to ask for access.

- python code/utils/checksums.py --dir data/raw --output data/raw/checksums.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/utils/checksums.py': [Errno 2] No such file or directory

- python code/02_preprocess_graphs.py --input data/raw/qm9_subset.parquet --output data/processed -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/02_preprocess_graphs.py", line 296, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/02_preprocess_graphs.py", line 185, in main
    logger = setup_script_logging()
             ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/02_preprocess_graphs.py", line 33, in setup_script_logging
    return setup_logging("02_preprocess_graphs")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/utils/logging_utils.py", line 33, in setup_logging
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
  File "<frozen os>", line 225, in makedirs
FileNotFoundError: [Errno 2] No such file or directory: ''

- python code/train/trainer.py --epochs 50 --device cpu -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/train/trainer.py': [Errno 2] No such file or directory

- python code/train/eval.py --model-path artifacts/models/ --output artifacts/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/train/eval.py': [Errno 2] No such file or directory

- python code/interpret/explainer.py --model-path artifacts/models/ --output artifacts/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/interpret/explainer.py': [Errno 2] No such file or directory

- python code/interpret/validate_proxy.py --predictions artifacts/predictions.parquet --kinetic data/raw/kinetic_dataset_raw.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/interpret/validate_proxy.py': [Errno 2] No such file or directory

- python code/utils/ssot.py --metrics artifacts/metrics.json --predictions artifacts/predictions.parquet -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/utils/ssot.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/kinetic_dataset_raw.csv
- data/raw/qm9_subset.parquet
- data/raw/reference_substructures_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/kinetic_dataset_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_verify_kinetic_checksum.py` — NOT invoked by the run-book
    - `code/010_populate_checksums.py` — NOT invoked by the run-book
    - `code/010_tag_kinetic_data.py` — NOT invoked by the run-book
    - `code/010_verify_kinetic_checksum.py` — NOT invoked by the run-book
    - `code/01_download_kinetic_data.py` — NOT invoked by the run-book
    - `code/02_ingest_kinetic_data.py` — NOT invoked by the run-book
    - `code/03_curate_reference_sets.py` — NOT invoked by the run-book
    - `code/utils/checksum_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/kinetic_dataset_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/qm9_subset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_data.py` — NOT invoked by the run-book
    - `code/02_preprocess_graphs.py` — IS a run-book command
    - `code/04_validate_data_availability.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/utils/loaders.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/qm9_subset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/reference_substructures_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_ingest_reference_substructures.py` — NOT invoked by the run-book
    - `code/00_verify_checksums.py` — NOT invoked by the run-book
    - `code/010_populate_checksums.py` — NOT invoked by the run-book
    - `code/010_verify_reference_checksum.py` — NOT invoked by the run-book
    - `code/02_ingest_reference_substructures.py` — NOT invoked by the run-book
    - `code/03_curate_reference_sets.py` — NOT invoked by the run-book
    - `code/data/generate_reference_substructures.py` — NOT invoked by the run-book
    - `code/utils/checksum_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/reference_substructures_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
