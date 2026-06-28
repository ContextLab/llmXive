# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/data_loader.py # Stage 1: Download data; python code/ast_cloner.py # Stage 2: Clone detection; python code/correlation_analysis.py # Stage 5: Correlation analysis; 7 command(s) failed: python code/quickstart_validation.py validate_directory_structure (rc=1); python code/main.py (rc=1); python code/pii_scanner.py # Stage 1: PII scan (rc=2); 4 declared deliverable(s) absent: data/analysis/correlation_results.csv; data/parse_failures.csv; data/processed/clone_metrics.csv

## Failing / missing run-book commands

- python code/quickstart_validation.py validate_directory_structure -> rc=1
    tart_validation.py", line 121, in validate_checksum_manifest
    save_manifest(manifest_path, manifest)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/checksum_manifest.py", line 127, in save_manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'parent'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/main.py", line 11, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/data_loader.py # Stage 1: Download data -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/data_loader.py': [Errno 2] No such file or directory
- python code/pii_scanner.py # Stage 1: PII scan -> rc=2
    ==========================================================
2026-06-28 03:53:28,422 - INFO - Scanning subdirectory: analysis
2026-06-28 03:53:28,422 - INFO - Starting PII scan of directory: /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/data/analysis
2026-06-28 03:53:28,422 - ERROR - PII scan failed with error: 'PosixPath' object has no attribute 'walk'
- python code/ast_cloner.py # Stage 2: Clone detection -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/ast_cloner.py': [Errno 2] No such file or directory
- python code/model_metrics.py # Stage 3: Perplexity computation -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/model_metrics.py", line 15, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/bug_detection.py # Stage 4: Bug detection -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/bug_detection.py", line 21, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/correlation_analysis.py # Stage 5: Correlation analysis -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/correlation_analysis.py': [Errno 2] No such file or directory
- python code/visualization.py # Stage 6: Visualizations -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/visualization.py", line 22, in <module>
    import matplotlib
ModuleNotFoundError: No module named 'matplotlib'
- python code/correlation_analysis.py --threshold 0.7 & -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/correlation_analysis.py': [Errno 2] No such file or directory
- python code/correlation_analysis.py --threshold 0.8 & -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/correlation_analysis.py': [Errno 2] No such file or directory
- python code/correlation_analysis.py --threshold 0.9 & -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/correlation_analysis.py': [Errno 2] No such file or directory
- python code/quickstart_validation.py -> rc=1
    tart_validation.py", line 121, in validate_checksum_manifest
    save_manifest(manifest_path, manifest)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/checksum_manifest.py", line 127, in save_manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    ^^^^^^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'parent'

## Declared deliverables still missing

- data/analysis/correlation_results.csv
- data/parse_failures.csv
- data/processed/clone_metrics.csv
- data/raw/github-code-sample.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_manifest.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/checksum_correlation_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/parse_failures.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_manifest.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/parse_failure_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/parse_failures.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/clone_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_manifest.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/clone_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/github-code-sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_manifest.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/github-code-sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## Files your producers ACTUALLY wrote — reconcile consumers against THESE

A `missing columns` / `KeyError` / `FileNotFoundError: <file>` failure above is a cross-file DATA-contract mismatch: a consumer expects column names or a path the UPSTREAM producer did not write. The traceback shows only what the consumer EXPECTS — here is what actually landed on disk. Make the PRODUCER write the exact column names / path the consumers need (or make the consumers read these actual names). Fix the ROOT producer first: a script failing on a missing INPUT file is a CASCADE that clears once its producer is fixed — do not edit the cascade victim in isolation.

- `data/analysis/pii_scan.log` (902 bytes)
- `data/quickstart_validation_results.json` (1410 bytes)
