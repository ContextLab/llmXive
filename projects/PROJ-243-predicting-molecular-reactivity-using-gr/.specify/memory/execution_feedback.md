# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/checksums.json, data/raw/qm9_subset.parquet, data/raw/raw/gdb9.sdf.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/checksums.json, data/raw/qm9_subset.parquet, data/raw/raw/gdb9.sdf.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 run-book script(s) missing (plan/impl path mismatch): python code/utils/checksums.py --dir data/raw --output data/raw/checksums.json; python code/train/trainer.py  --epochs 50  --device cpu  --early-stop-patience 5  --hyperparam-search grid; python code/train/eval.py  --model-dir artifacts/models/  --output artifacts/; 1 command(s) failed: python code/02_preprocess_graphs.py --input data/raw/qm9_subset.parquet --output data/processed (rc=1); 2 declared deliverable(s) absent: data/raw/kinetic_dataset_raw.csv; data/raw/reference_substructures_raw.csv

## Failing / missing run-book commands

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

- python code/train/trainer.py  --epochs 50  --device cpu  --early-stop-patience 5  --hyperparam-search grid -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/train/trainer.py': [Errno 2] No such file or directory

- python code/train/eval.py  --model-dir artifacts/models/  --output artifacts/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/train/eval.py': [Errno 2] No such file or directory

- python code/interpret/explainer.py  --model-dir artifacts/models/  --output artifacts/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/interpret/explainer.py': [Errno 2] No such file or directory

- python code/interpret/validate_proxy.py  --predictions artifacts/predictions.json  --kinetic data/raw/kinetic_dataset_raw.csv  --output artifacts/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/interpret/validate_proxy.py': [Errno 2] No such file or directory

- python code/utils/ssot.py  --metrics artifacts/metrics.json  --predictions artifacts/predictions.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/utils/ssot.py': [Errno 2] No such file or directory

- python code/utils/aggregate.py  --metrics artifacts/metrics.json  --predictions artifacts/predictions.json  --attribution artifacts/attribution_maps.json  --output artifacts/final_output.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-243-predicting-molecular-reactivity-using-gr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-243-predicting-molecular-reactivity-using-gr/code/utils/aggregate.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/kinetic_dataset_raw.csv
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
- `data/raw/reference_substructures_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_ingest_reference_substructures.py` — NOT invoked by the run-book
    - `code/00_verify_checksums.py` — NOT invoked by the run-book
    - `code/010_populate_checksums.py` — NOT invoked by the run-book
    - `code/010_verify_reference_checksum.py` — NOT invoked by the run-book
    - `code/02_ingest_reference_substructures.py` — NOT invoked by the run-book
    - `code/03_curate_reference_sets.py` — NOT invoked by the run-book
    - `code/data/curate_reference_substructures.py` — NOT invoked by the run-book
    - `code/data/generate_reference_substructures.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/reference_substructures_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
