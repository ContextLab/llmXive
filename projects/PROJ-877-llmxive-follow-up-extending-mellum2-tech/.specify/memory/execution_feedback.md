# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/data/ngram.py --input data/processed/labeled.parquet --output data/models/ngram.arpa; python code/analysis/thresholds.py --input data/processed/inferred.parquet; python code/analysis/significance.py --input data/processed/inferred.parquet; 6 command(s) failed: python code/main.py --model mistral-7b --device cpu --timeout 60 (rc=1); python code/main.py --phase power-analysis (rc=1); python code/data/download.py --lang python --lang java --sample-size 500 (rc=1); 4 declared deliverable(s) absent: data/results/feasibility_report.json; data/results/us1_correlation_stats.json; data/results/us2_threshold_candidates.json

## Failing / missing run-book commands

- python code/main.py --model mistral-7b --device cpu --timeout 60 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/main.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --phase power-analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/main.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/data/download.py --lang python --lang java --sample-size 500 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/data/download.py", line 13, in <module>
    from config import get_project_root, get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/config.py", line 10, in <module>
    from dotenv import load_dotenv
ModuleNotFoundError: No module named 'dotenv'
- python code/data/preprocess.py --input data/raw/sample.parquet --output data/processed/labeled.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/data/preprocess.py", line 13, in <module>
    import tree_sitter_python as tspython
ModuleNotFoundError: No module named 'tree_sitter_python'
- python code/data/ngram.py --input data/processed/labeled.parquet --output data/models/ngram.arpa -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/data/ngram.py': [Errno 2] No such file or directory
- python code/inference/engine.py --model mistral-7b --input data/processed/labeled.parquet --output data/processed/inferred.parquet --device cpu --timeout 60 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/inference/engine.py", line 15, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/analysis/correlation.py --input data/processed/inferred.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/analysis/correlation.py", line 6, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analysis/thresholds.py --input data/processed/inferred.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/analysis/thresholds.py': [Errno 2] No such file or directory
- python code/analysis/significance.py --input data/processed/inferred.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/analysis/significance.py': [Errno 2] No such file or directory
- python code/viz/plots.py --input data/results/analysis_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/code/viz/plots.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/feasibility_report.json
- data/results/us1_correlation_stats.json
- data/results/us2_threshold_candidates.json
- data/results/variance_null_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/feasibility_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/power_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/feasibility.py` — NOT invoked by the run-book
    - `code/analysis/threshold.py` — NOT invoked by the run-book
    - `code/data/download.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/results/feasibility_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us1_correlation_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — IS a run-book command
    - `code/analysis/threshold.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us1_correlation_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/us2_threshold_candidates.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/us2_threshold_candidates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/variance_null_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/variance_check.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — IS a run-book command
  Make ONE of these WRITE `data/results/variance_null_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
