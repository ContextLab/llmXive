# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_data.py (rc=1); python code/preprocess.py (rc=1); python code/train_models.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_316L.csv; data/processed/degenerate_flag.json

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    2026-09-20 05:26:17,403 - INFO - Starting 316L LPBF dataset download
2026-09-20 05:26:17,403 - INFO - Fetching metadata from Zenodo record 6826006
2026-09-20 05:26:18,095 - INFO - Verifying material type is 316L
2026-09-20 05:26:18,096 - ERROR - Material verification failed: Dataset does not appear to be for 316L stainless steel. Title: 24. increased mobilization of toxic elements from permafrost areas in the eastern alps, Description: <p>poster presentation</p>...
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/preprocess.py", line 296, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/preprocess.py", line 284, in main
    raise FileNotFoundError(f"Input file not found: {input_file}")
FileNotFoundError: Input file not found: data/raw/316L_LPBF_dataset.csv
- python code/train_models.py -> rc=1
    2026-09-20 05:26:19,776 - llmXive_pipeline - INFO - Starting Model Training Pipeline (US2)

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/train_models.py", line 318, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/train_models.py", line 176, in main
    base_dir = Path(__file__).parent.parent
               ^^^^
NameError: name 'Path' is not defined
- python code/analyze_explainability.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/analyze_explainability.py", line 14, in <module>
    import seaborn as sns
ModuleNotFoundError: No module named 'seaborn'

## Declared deliverables still missing

- data/processed/cleaned_316L.csv
- data/processed/degenerate_flag.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_316L.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_processed_data.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/analyze_explainability.py` — IS a run-book command
    - `code/save_significance_report.py` — NOT invoked by the run-book
    - `code/train_models.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_316L.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/degenerate_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/orchestration_check.py` — NOT invoked by the run-book
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/degenerate_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/316L_LPBF_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/save_processed_data.py`, `code/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/316L_LPBF_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/save_processed_data.py`, `code/preprocess.py`.
