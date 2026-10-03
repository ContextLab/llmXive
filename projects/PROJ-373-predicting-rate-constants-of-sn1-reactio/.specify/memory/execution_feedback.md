# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data/clean.py --input data/processed/intermediate_sn1.csv --output data/processed/cleaned_intermediate.csv --exclusion-log data/processed/exclusion_raw.log`
- `python code/data/descriptors.py --input data/processed/cleaned_intermediate.csv --output data/processed/descriptors.csv --exclusion-log data/processed/exclusion_raw.log`
- `python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet`
- `python code/data/exclusion_report.py --aggregate --clean-log data/processed/clean.log --raw-log data/processed/exclusion_raw.log --output data/processed/exclusion_report.csv`
- `python code/data/exclusion_report.py --input data/processed/exclusion_raw.log --schema specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml --output data/processed/exclusion_validation.log`
- `python code/data/finalize_dataset.py  --input-path data/processed/cleaned_intermediate.csv  --intermediate-path data/processed/intermediate_sn1.csv  --output-path data/processed/cleaned_sn1.csv  --exclusion-path data/processed/exclusion_report.csv  --success-rate-path data/processed/success_rate.json  --checksum-path data/processed/cleaned_sn1.csv.sha256`
- `python code/data/init_exclusion_log.py --output data/processed/exclusion_raw.log`
- `python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log`
- `python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log`
- `python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log`
  - script usage: `schema_check.py [-h] [--dataset DATASET] [--output OUTPUT]`
  - argparse error: `schema_check.py: error: unrecognized arguments: --dataset-name author/DTS-SN1-15-01-2024`
- run-book command: `python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet`
  - script usage: `download.py [-h] [--dataset DATASET] [--output OUTPUT]`
  - argparse error: `download.py: error: unrecognized arguments: --schema-pass`
- run-book command: `python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/`
  - script usage: `split.py [-h] [--input INPUT] [--train-output TRAIN_OUTPUT]`
  - argparse error: `split.py: error: unrecognized arguments: --output-dir data/processed/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log (rc=2); python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet (rc=2); python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log (rc=1); 11 declared deliverable(s) absent: data/processed/cleaned_intermediate.csv; data/processed/cleaned_sn1.csv; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log -> rc=2
    usage: schema_check.py [-h] [--dataset DATASET] [--output OUTPUT]
                       [--required-columns REQUIRED_COLUMNS [REQUIRED_COLUMNS ...]]
schema_check.py: error: unrecognized arguments: --dataset-name author/DTS-SN1-15-01-2024
- python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet -> rc=2
    usage: download.py [-h] [--dataset DATASET] [--output OUTPUT]
                   [--schema-log SCHEMA_LOG]
download.py: error: unrecognized arguments: --schema-pass
- python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1
    2026-10-03 04:16:33,508 - __main__ - ERROR - Mapping failed: Raw data file not found: data/raw/sn1_raw.parquet
- python code/data/init_exclusion_log.py --output data/processed/exclusion_raw.log -> rc=1
    2026-10-03 04:16:33,587 - init_exclusion_log - INFO - Starting exclusion log initialization...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/init_exclusion_log.py", line 56, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/init_exclusion_log.py", line 46, in main
    success = initialize_exclusion_log()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/init_exclusion_log.py", line 14, in initialize_exclusion_log
    output_path = Path(config.processed_dir) / "exclusion_raw.log"
                       ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'DataConfig' object has no attribute 'processed_dir'
- python code/data/clean.py --input data/processed/intermediate_sn1.csv --output data/processed/cleaned_intermediate.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 27, in <module>
    from rdkit.Chem import CanonicalSmiles
ImportError: cannot import name 'CanonicalSmiles' from 'rdkit.Chem' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/.venv/lib/python3.11/site-packages/rdkit/Chem/__init__.py)
- python code/data/descriptors.py --input data/processed/cleaned_intermediate.csv --output data/processed/descriptors.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1
    2026-10-03 04:16:34,237 - __main__ - ERROR - Descriptor computation failed: Input file not found: data/processed/cleaned_intermediate.csv
- python code/data/exclusion_report.py --input data/processed/exclusion_raw.log --schema specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml --output data/processed/exclusion_validation.log -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 229, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 205, in main
    logger = setup_exclusion_logging(Path("data/processed/exclusion_aggregation.log"))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 25, in setup_exclusion_logging
    ensure_dirs(log_path.parent)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given
- python code/data/exclusion_report.py --aggregate --clean-log data/processed/clean.log --raw-log data/processed/exclusion_raw.log --output data/processed/exclusion_report.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 229, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 205, in main
    logger = setup_exclusion_logging(Path("data/processed/exclusion_aggregation.log"))
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/exclusion_report.py", line 25, in setup_exclusion_logging
    ensure_dirs(log_path.parent)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given
- python code/data/finalize_dataset.py  --input-path data/processed/cleaned_intermediate.csv  --intermediate-path data/processed/intermediate_sn1.csv  --output-path data/processed/cleaned_sn1.csv  --exclusion-path data/processed/exclusion_report.csv  --success-rate-path data/processed/success_rate.json  --checksum-path data/processed/cleaned_sn1.csv.sha256 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/finalize_dataset.py", line 208, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/finalize_dataset.py", line 118, in main
    logger = setup_finalize_logger()
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/finalize_dataset.py", line 17, in setup_finalize_logger
    ensure_dirs(log_path)
TypeError: ensure_dirs() takes 0 positional arguments but 1 was given
- python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/ -> rc=2
    usage: split.py [-h] [--input INPUT] [--train-output TRAIN_OUTPUT]
                [--val-output VAL_OUTPUT] [--test-output TEST_OUTPUT]
                [--report REPORT] [--column COLUMN]
split.py: error: unrecognized arguments: --output-dir data/processed/

## Declared deliverables still missing

- data/processed/cleaned_intermediate.csv
- data/processed/cleaned_sn1.csv
- data/processed/descriptors.csv
- data/processed/exclusion_report.csv
- data/processed/intermediate_sn1.csv
- data/processed/split_report.json
- data/processed/split_test.csv
- data/processed/split_train.csv
- data/processed/split_val.csv
- data/processed/success_rate.json
- data/raw/sn1_raw.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_dirs` — defined in `code/config.py`; called 25 way(s):

- code/main.py: ensure_dirs()
- code/models/evaluate.py: ensure_dirs()
- code/models/save_artifacts.py: ensure_dirs([ARTIFACTS_DIR])
- code/models/train.py: ensure_dirs()
- code/data/split.py: ensure_dirs()
- code/data/ingest.py: ensure_dirs()
- code/data/init_exclusion_log.py: ensure_dirs()
- code/data/download.py: ensure_dirs()
- code/data/finalize_dataset.py: ensure_dirs(log_path)
- code/data/finalize_dataset.py: ensure_dirs(output_path)
- code/data/finalize_dataset.py: ensure_dirs(success_report_path)
- code/data/exclusion_report.py: ensure_dirs(log_path.parent)
- code/data/exclusion_report.py: ensure_dirs(output_csv_path.parent)
- code/data/exclusion_report.py: ensure_dirs(output_json_path.parent)
- code/data/mapping.py: ensure_dirs()
- code/data/final_validation.py: ensure_dirs()
- code/data/clean.py: ensure_dirs()
- code/data/schema_check.py: ensure_dirs()
- code/data/descriptors.py: ensure_dirs()
- code/tests/integration/test_full_pipeline.py: ensure_dirs()
- code/tests/integration/test_full_pipeline.py: ensure_dirs() # Ensure artifacts dir exists
- code/analysis/consistency.py: ensure_dirs()
- code/analysis/sensitivity_runner.py: ensure_dirs()
- code/analysis/final_report.py: ensure_dirs()
- code/analysis/hyperparameter_sensitivity.py: ensure_dirs([output_path.parent])

Make `ensure_dirs` in `code/config.py` accept ALL of the above.

### class `DataConfig` (in `code/config.py`) — accessed via method/attribute names this round: `processed_dir`

`DataConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `DataConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`DataConfig.processed_dir` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_intermediate.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/clean.py` — IS a run-book command
    - `code/data/descriptors.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_intermediate.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_sn1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_quickstart.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/final_validation.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
    - `code/data/split.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_sn1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/models/evaluate.py` — NOT invoked by the run-book
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/descriptors.py` — IS a run-book command
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/consistency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/final_validation.py` — NOT invoked by the run-book
    - `code/validation/validate_quickstart.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/exclusion_report.py` — IS a run-book command
    - `code/data/validate_exclusion_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/intermediate_sn1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/mapping.py` — IS a run-book command
    - `code/data/clean.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/intermediate_sn1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_val.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/split.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_val.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/success_rate.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_quickstart.py` — NOT invoked by the run-book
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/success_rate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sn1_raw.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — IS a run-book command
    - `code/data/mapping.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/sn1_raw.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/cleaned_intermediate.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/finalize_dataset.py`, `code/data/clean.py`, `code/data/descriptors.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_intermediate.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/config.py`, `code/data/finalize_dataset.py`, `code/data/clean.py`, `code/data/descriptors.py`.

### `data/raw/sn1_raw.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/download.py`, `code/data/finalize_dataset.py`, `code/data/mapping.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/sn1_raw.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/config.py`, `code/data/download.py`, `code/data/finalize_dataset.py`, `code/data/mapping.py`.
