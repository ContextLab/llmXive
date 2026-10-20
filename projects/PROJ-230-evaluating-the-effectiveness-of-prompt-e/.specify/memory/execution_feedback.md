# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python src/evaluation/extract_io_pairs.py; python src/evaluation/run_js_validation.py; 5 command(s) failed: python src/ingestion/download_datasets.py (rc=1); python src/ingestion/preprocess_corpus.py (rc=1); python src/execution/run_inference.py (rc=1); 4 declared deliverable(s) absent: data/evaluation/metadata_log.csv; data/evaluation/quality_metrics.csv; data/processed/corpus.csv

## Failing / missing run-book commands

- python src/ingestion/download_datasets.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/ingestion/download_datasets.py", line 12, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/ingestion/preprocess_corpus.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/ingestion/preprocess_corpus.py", line 20, in <module>
    from src.ingestion.download_datasets import ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/code/src/ingestion/download_datasets.py", line 24, in <module>
    from huggingface_hub import hf_hub_download, RepositoryNotFoundError, HfHubHTTPError
ImportError: cannot import name 'RepositoryNotFoundError' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python src/execution/run_inference.py -> rc=1
{"timestamp": "2026-10-20T02:25:51.100908Z", "level": "INFO", "logger": "__main__", "message": "Starting inference run."}
{"timestamp": "2026-10-20T02:25:51.101067Z", "level": "INFO", "logger": "__main__", "message": "Loaded 4 prompt conditions."}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/execution/run_inference.py", line 212, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/execution/run_inference.py", line 158, in main
    corpus = load_corpus()
             ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/execution/run_inference.py", line 54, in load_corpus
    raise FileNotFoundError(f"Corpus file {CORPUS_PATH} does not exist.")
FileNotFoundError: Corpus file data/processed/corpus.csv does not exist.

- python src/evaluation/extract_io_pairs.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/evaluation/extract_io_pairs.py': [Errno 2] No such file or directory

- python src/evaluation/run_js_validation.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-230-evaluating-the-effectiveness-of-prompt-e/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/src/evaluation/run_js_validation.py': [Errno 2] No such file or directory

- python code/src/evaluation/compute_quality.py -> rc=1

2026-10-20 02:25:51,204 - __main__ - INFO - Starting quality metric computation...
2026-10-20 02:25:51,204 - __main__ - WARNING - Translations directory not found: data/evaluation/raw_translations
2026-10-20 02:25:51,204 - __main__ - ERROR - No JavaScript files found to analyze. Aborting.

- python code/src/evaluation/statistical_analysis.py -> rc=1
026-10-20T02:25:51.531703Z", "level": "INFO", "logger": "__main__", "message": "Loading quality metrics from /home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/data/evaluation/quality_metrics.csv"}
{"timestamp": "2026-10-20T02:25:51.531746Z", "level": "ERROR", "logger": "__main__", "message": "Quality metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/data/evaluation/quality_metrics.csv"}
{"timestamp": "2026-10-20T02:25:51.531775Z", "level": "INFO", "logger": "__main__", "message": "Loading correctness results from /home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/data/evaluation/correctness_results.csv"}
{"timestamp": "2026-10-20T02:25:51.531806Z", "level": "ERROR", "logger": "__main__", "message": "Correctness results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e/data/evaluation/correctness_results.csv"}
{"timestamp": "2026-10-20T02:25:51.531836Z", "level": "ERROR", "logger": "__main__", "message": "Statistical analysis failed: No data found for statistical analysis"}



## Declared deliverables still missing

- data/evaluation/metadata_log.csv
- data/evaluation/quality_metrics.csv
- data/processed/corpus.csv
- data/raw/ingestion_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/evaluation/metadata_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/generate_metadata_log.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_metadata_log.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evaluation/metadata_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/evaluation/quality_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/compute_quality.py` — IS a run-book command
    - `code/src/evaluation/generate_statistical_summary.py` — NOT invoked by the run-book
    - `code/src/evaluation/statistical_analysis.py` — IS a run-book command
    - `code/tests/unit/test_compute_quality.py` — NOT invoked by the run-book
    - `code/tests/unit/test_statistical_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evaluation/quality_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corpus.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/evaluation/run_node_tests.py` — NOT invoked by the run-book
    - `code/src/evaluation/translate_tests.py` — NOT invoked by the run-book
    - `code/src/execution/run_inference.py` — NOT invoked by the run-book
    - `code/src/ingestion/preprocess_corpus.py` — NOT invoked by the run-book
    - `code/src/ingestion/sampling_logic.py` — NOT invoked by the run-book
    - `code/src/ingestion/validate_corpus_size.py` — NOT invoked by the run-book
    - `code/src/ingestion/validate_dataset.py` — NOT invoked by the run-book
    - `code/tests/integration/test_run_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corpus.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ingestion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/download_datasets.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ingestion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
