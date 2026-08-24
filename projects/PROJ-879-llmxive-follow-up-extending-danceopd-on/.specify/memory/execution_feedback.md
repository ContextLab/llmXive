# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/weights_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/weights_manifest.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 run-book script(s) missing (plan/impl path mismatch): python code/data/generate_teacher.py  --source imagenet  --samples a substantial cohort of participants  --batch-size  --output data/processed/teacher_routing_dataset.parquet; python code/models/train_tree.py  --input data/processed/teacher_routing_dataset.parquet  --depths 2,4,6,8,10,12,14,16,18,20  --output models/trained_trees/; python code/utils/stats.py  --input data/results/inference_results.parquet  --output data/results/statistical_tests.json; 1 command(s) failed: python code/utils/check_weights.py --path <path-to-weights> (rc=1); 8 declared deliverable(s) absent: data/processed/teacher_routing_dataset.parquet; data/processed/test_split.parquet; data/processed/train_split.parquet

## Failing / missing run-book commands

- python code/utils/check_weights.py --path <path-to-weights> -> rc=1
    WARNING: Manifest file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/data/raw/weights_manifest.json
Initializing manifest with placeholder entries...
WARNING: teacher_weights.pth not found. Please update manifest manually.
Manifest initialized at /home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/data/raw/weights_manifest.json
ERROR: No weight files found and unable to initialize manifest with valid hashes.
- python code/data/generate_teacher.py  --source imagenet  --samples a substantial cohort of participants  --batch-size  --output data/processed/teacher_routing_dataset.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/data/generate_teacher.py': [Errno 2] No such file or directory
- python code/models/train_tree.py  --input data/processed/teacher_routing_dataset.parquet  --depths 2,4,6,8,10,12,14,16,18,20  --output models/trained_trees/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/models/train_tree.py': [Errno 2] No such file or directory
- python code/utils/stats.py  --input data/results/inference_results.parquet  --output data/results/statistical_tests.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/stats.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/teacher_routing_dataset.parquet
- data/processed/test_split.parquet
- data/processed/train_split.parquet
- data/raw/checksums.json
- data/raw/imagenet_samples.parquet
- data/raw/laion_samples.parquet
- data/results/data_fetch_validation.json
- data/results/fidelity_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/teacher_routing_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/validate_sources.py` — NOT invoked by the run-book
    - `code/00_validate_sources.py` — NOT invoked by the run-book
    - `code/01_train_trees.py` — NOT invoked by the run-book
    - `code/02_evaluate_fidelity_parallel.py` — NOT invoked by the run-book
    - `code/00_data_extraction.py` — NOT invoked by the run-book
    - `code/00_check_dataset_sources.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/teacher_routing_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_split.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_evaluate_fidelity.py` — NOT invoked by the run-book
    - `code/01_train_trees.py` — NOT invoked by the run-book
    - `code/030_sample_size_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_split.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_split.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_train_trees.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_split.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_fetch.py` — NOT invoked by the run-book
    - `code/utils/check_weights.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/imagenet_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_stream.py` — NOT invoked by the run-book
    - `code/00_data_fetch.py` — NOT invoked by the run-book
    - `code/_data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/imagenet_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/laion_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_stream.py` — NOT invoked by the run-book
    - `code/00_data_fetch.py` — NOT invoked by the run-book
    - `code/_data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/laion_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/data_fetch_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_fetch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_fetch_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_evaluate_fidelity.py` — NOT invoked by the run-book
    - `code/030_compute_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/statistics_runner.py` — NOT invoked by the run-book
    - `code/utils/import_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fidelity_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/data/raw/weights_manifest.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/00_teacher_inference.py`, `code/utils/check_weights.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/data/raw/weights_manifest.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/00_teacher_inference.py`, `code/utils/check_weights.py`.
