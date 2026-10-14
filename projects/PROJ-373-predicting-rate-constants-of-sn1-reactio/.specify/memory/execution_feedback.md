# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/exclusion_report.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/exclusion_report.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 10 command(s) failed: python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log (rc=1); python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet (rc=1); python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log (rc=1); 3 declared deliverable(s) absent: data/processed/cleaned_intermediate.csv; data/processed/descriptors.csv; data/raw/sn1_raw_merged.parquet

## Failing / missing run-book commands

- python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/schema_check.py", line 12, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/__init__.py", line 1, in <module>
    from .logger import setup_logging, get_logger
ImportError: cannot import name 'setup_logging' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/logger.py)

- python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/download.py", line 18, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/__init__.py", line 1, in <module>
    from .logger import setup_logging, get_logger
ImportError: cannot import name 'setup_logging' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/logger.py)

- python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1

2026-10-14 10:26:48,426 - mapping - INFO - Starting mapping and cleaning process...
2026-10-14 10:26:48,426 - mapping - INFO - Starting mapping and cleaning process...
2026-10-14 10:26:48,426 - mapping - INFO - Loading raw data from data/raw/sn1_raw.parquet
2026-10-14 10:26:48,426 - mapping - INFO - Loading raw data from data/raw/sn1_raw.parquet
2026-10-14 10:26:48,426 - mapping - ERROR - Raw data file not found: data/raw/sn1_raw.parquet
2026-10-14 10:26:48,426 - mapping - ERROR - Raw data file not found: data/raw/sn1_raw.parquet
2026-10-14 10:26:48,426 - mapping - ERROR - Fatal error: Raw data file not found: data/raw/sn1_raw.parquet
2026-10-14 10:26:48,426 - mapping - ERROR - Fatal error: Raw data file not found: data/raw/sn1_raw.parquet

- python code/data/init_exclusion_log.py --output data/processed/exclusion_raw.log -> rc=1

2026-10-14 10:26:48,507 - __main__ - INFO - Starting exclusion log initialization...
2026-10-14 10:26:48,507 - __main__ - ERROR - Error reading pipeline status: [Errno 21] Is a directory: 'data/processed/.pipeline_status'
2026-10-14 10:26:48,507 - __main__ - ERROR - Exclusion log initialization failed or was aborted.

- python code/data/clean.py --input data/processed/intermediate_sn1.csv --output data/processed/cleaned_intermediate.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 252, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 243, in main
    success = clean_and_filter_data(input_path, output_path, exclusion_log_path, clean_log_path, status_path)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 146, in clean_and_filter_data
    write_aborted_status(status_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/clean.py", line 68, in write_aborted_status
    with open(status_path, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^
IsADirectoryError: [Errno 21] Is a directory: 'data/processed/.pipeline_status'

- python code/data/descriptors.py --input data/processed/cleaned_intermediate.csv --output data/processed/descriptors.csv --exclusion-log data/processed/exclusion_raw.log -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/descriptors.py", line 13, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/__init__.py", line 1, in <module>
    from .logger import setup_logging, get_logger
ImportError: cannot import name 'setup_logging' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/logger.py)

- python code/data/exclusion_report.py --input data/processed/exclusion_raw.log --schema specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml --output data/processed/exclusion_validation.log -> rc=1

2026-10-14 10:26:48,937 - INFO - Starting exclusion report aggregation...
2026-10-14 10:26:48,937 - ERROR - Input file not found: data/processed/exclusion_raw.log

- python code/data/exclusion_report.py --aggregate --clean-log data/processed/clean.log --raw-log data/processed/exclusion_raw.log --output data/processed/exclusion_report.csv -> rc=1

2026-10-14 10:26:48,986 - INFO - Starting exclusion report aggregation...
2026-10-14 10:26:48,986 - ERROR - Upstream files missing. Writing blocked status.

- python code/data/finalize_dataset.py  --input-path data/processed/cleaned_intermediate.csv  --intermediate-path data/processed/intermediate_sn1.csv  --output-path data/processed/cleaned_sn1.csv  --exclusion-path data/processed/exclusion_report.csv  --success-rate-path data/processed/success_rate.json  --checksum-path data/processed/cleaned_sn1.csv.sha256 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/finalize_dataset.py", line 12, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/__init__.py", line 1, in <module>
    from .logger import setup_logging, get_logger
ImportError: cannot import name 'setup_logging' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/logger.py)

- python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/data/split.py", line 14, in <module>
    from utils.logger import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/__init__.py", line 1, in <module>
    from .logger import setup_logging, get_logger
ImportError: cannot import name 'setup_logging' from 'utils.logger' (/home/runner/work/llmXive/llmXive/projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code/utils/logger.py)


## Declared deliverables still missing

- data/processed/cleaned_intermediate.csv
- data/processed/descriptors.csv
- data/raw/sn1_raw_merged.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_intermediate.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_intermediate.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/collinearity.py` — NOT invoked by the run-book
    - `code/analysis/consistency.py` — NOT invoked by the run-book
    - `code/analysis/interpret.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_runner.py` — NOT invoked by the run-book
    - `code/data/__init__.py` — NOT invoked by the run-book
    - `code/data/descriptors.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sn1_raw_merged.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/atomic_gate.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/data/finalize_dataset.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/sn1_raw_merged.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
