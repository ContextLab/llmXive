# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_checksums.py; python code/_prune_model.py --retention-pct 50; 2 command(s) failed: python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head (rc=1); python code/04_statistical_validation.py (rc=1); 4 declared deliverable(s) absent: data/processed/original_faithfulness_scores.csv; data/processed/pruned_faithfulness_scores.csv; data/processed/sensitivity_results.csv

## Failing / missing run-book commands

- python code/utils/verify_checksums.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/utils/verify_checksums.py': [Errno 2] No such file or directory

- python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/01_sensitivity_analysis.py", line 11, in <module>
    from utils.masking import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/utils/masking.py", line 13, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python code/_prune_model.py --retention-pct 50 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/_prune_model.py': [Errno 2] No such file or directory

- python code/04_statistical_validation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 18, in <module>
    from code_00_config import Config, validate_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/code_00_config.py", line 7, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'


## Declared deliverables still missing

- data/processed/original_faithfulness_scores.csv
- data/processed/pruned_faithfulness_scores.csv
- data/processed/sensitivity_results.csv
- data/processed/statistical_validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/original_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
    - `code/run_original_faithfulness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/original_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pruned_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/pruned_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_sensitivity_analysis.py` — IS a run-book command
    - `code/02_prune_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/statistical_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
