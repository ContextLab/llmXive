# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 4 command(s) failed: python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv (rc=1); python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv (rc=1); python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json (rc=1); 8 declared deliverable(s) absent: data/interim/cleaned_adress.csv; data/processed/checksums.json; data/processed/embeddings.npy

## Failing / missing run-book commands

- python code/ingestion.py --dataset adress --output data/interim/cleaned_transcripts.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/ingestion.py", line 14, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/features.py --input data/interim/cleaned_transcripts.csv --output data/processed/features.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/features.py", line 10, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/stats.py --input data/processed/features.csv --output data/processed/stats_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/stats.py", line 5, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/modeling.py --input data/processed/features.csv --output data/processed/model_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/modeling.py", line 14, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-272-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/interim/cleaned_adress.csv
- data/processed/checksums.json
- data/processed/embeddings.npy
- data/processed/features.csv
- data/raw/checksums.json
- data/results/metadata.json
- data/results/raw_record_count.json
- data/results/statistical_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/cleaned_adress.csv` is declared but was NOT written. Scripts referencing it:
    - `code/t016_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/derivation.py` — NOT invoked by the run-book
    - `code/t025_save_features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/cleaned_adress.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/checksums.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/t012f_checksum_record.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/embeddings.npy` is declared but was NOT written. Scripts referencing it:
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/t025_save_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/embeddings.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling.py` — IS a run-book command
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
    - `code/stats.py` — IS a run-book command
    - `code/t025_save_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/checksums.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/t012f_checksum_record.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/t016_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/t024c_checksum.py` — NOT invoked by the run-book
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/derivation.py` — NOT invoked by the run-book
    - `code/stats.py` — IS a run-book command
    - `code/t025_save_features.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/results/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/raw_record_count.json` is declared but was NOT written. Scripts referencing it:
    - `code/t012h_success_criterion.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/results/raw_record_count.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/statistical_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/results/statistical_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
