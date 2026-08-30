# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/confound_analysis.py`
- `python code/descriptor_pipeline.py`
- `python code/dft_calculator.py`
- `python code/evaluate_models.py`
- `python code/fetch_data.py`
- `python code/sensitivity_analysis.py`
- `python code/train_models.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python code/fetch_data.py (rc=1); python code/confound_analysis.py (rc=1); python code/descriptor_pipeline.py (rc=1); 4 declared deliverable(s) absent: data/confounds.csv; data/descriptors_dft.csv; data/descriptors_semi.csv

## Failing / missing run-book commands

- python code/fetch_data.py -> rc=1
    2026-08-30 22:13:03,091 - fetch_data - INFO - Starting data fetch and verification process.
2026-08-30 22:13:03,091 - fetch_data - ERROR - Could not resolve Zenodo ID from idea file.
2026-08-30 22:13:03,091 - fetch_data - ERROR - Data fetch and verification failed.
- python code/confound_analysis.py -> rc=1
    Error: No CSV files found in data/raw/
- python code/descriptor_pipeline.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/descriptor_pipeline.py", line 207, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/descriptor_pipeline.py", line 175, in main
    parser = argparse.ArgumentParser(description="Run descriptor pipeline on barrier dataset")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/dft_calculator.py -> rc=1
    -qua/code/dft_calculator.py", line 332, in main
    logger = log_setup()
             ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/dft_calculator.py", line 35, in log_setup
    logger = setup_logger("dft_calculator", LOG_FILE)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/utils/logging_utils.py", line 47, in setup_logger
    file_handler = logging.FileHandler(log_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/logs/logs/dft_execution.log'
- python code/train_models.py -> rc=1
    
- python code/evaluate_models.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/evaluate_models.py", line 38, in <module>
    logger = setup_logger("evaluate_models", "logs/evaluation.log")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/utils/logging_utils.py", line 47, in setup_logger
    file_handler = logging.FileHandler(log_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/logs/logs/evaluation.log'
- python code/sensitivity_analysis.py -> rc=1
    2026-08-30 22:13:06,816 - sensitivity_analysis - INFO - Loading model and data...
2026-08-30 22:13:06,816 - sensitivity_analysis - ERROR - Error during sensitivity analysis: Model file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/sensitivity_analysis.py", line 275, in main
    model = load_model(args.model_path)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/sensitivity_analysis.py", line 59, in load_model
    raise FileNotFoundError(f"Model file not found: {path}")
FileNotFoundError: Model file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl

## Declared deliverables still missing

- data/confounds.csv
- data/descriptors_dft.csv
- data/descriptors_semi.csv
- data/raw/barrier_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/confounds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/confound_analysis.py` — IS a run-book command
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
  Make ONE of these WRITE `data/confounds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_dft.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — IS a run-book command
    - `code/evaluate_models.py` — IS a run-book command
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/dft_calculator.py` — IS a run-book command
    - `code/validate_subset_alignment.py` — NOT invoked by the run-book
    - `code/track_compute_resources.py` — NOT invoked by the run-book
    - `code/evaluators/missing_dof_analyzer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_dft.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors_semi.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — IS a run-book command
    - `code/physical_validator.py` — NOT invoked by the run-book
    - `code/evaluate_models.py` — IS a run-book command
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — IS a run-book command
    - `code/sensitivity_analysis.py` — IS a run-book command
    - `code/noise_injection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors_semi.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/barrier_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train_models.py` — IS a run-book command
    - `code/missing_dof_analysis.py` — NOT invoked by the run-book
    - `code/confounds.py` — NOT invoked by the run-book
    - `code/fetch_data.py` — IS a run-book command
    - `code/descriptor_pipeline.py` — IS a run-book command
    - `code/generate_summary_report.py` — IS a run-book command
    - `code/dft_calculator.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/barrier_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-546-predicting-molecular-properties-from-qua/code/models/rf_semi.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/sensitivity_analysis.py`.
