# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/scripts/generate_report.py; 4 command(s) failed: python code/scripts/fetch_data.py (rc=1); python code/scripts/preprocess.py (rc=1); python code/scripts/fit_distributions.py (rc=1); 5 declared deliverable(s) absent: data/processed/distribution_fits.csv; data/processed/game_metadata.csv; data/processed/model_results.csv

## Failing / missing run-book commands

- python code/scripts/fetch_data.py -> rc=1
    2026-10-02 23:22:24,878 - ERROR - No games specified in config.yaml
- python code/scripts/preprocess.py -> rc=1
    2026-10-02 23:22:24,923 - INFO - Starting preprocessing pipeline...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/preprocess.py", line 428, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/preprocess.py", line 386, in main
    config = load_config()
             ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/preprocess.py", line 36, in load_config
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/scripts/fit_distributions.py -> rc=1
    2026-10-02 23:22:24,966 - INFO - Starting distribution fitting with checkpointing.
2026-10-02 23:22:24,966 - WARNING - PyYAML not found, attempting manual parse. This may fail for complex YAML.
2026-10-02 23:22:24,966 - ERROR - No games defined in config.
- python code/scripts/fit_mixed_effects.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/fit_mixed_effects.py", line 23, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/scripts/generate_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/generate_report.py': [Errno 2] No such file or directory
- python -c "import pandas as pd; df = pd.read_csv('data/processed/run_records.csv'); print(f'Completeness: {df.notna().mean().mean():.2%}')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/distribution_fits.csv
- data/processed/game_metadata.csv
- data/processed/model_results.csv
- data/processed/run_records.csv
- data/processed/runner_profiles.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/distribution_fits.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — IS a run-book command
    - `code/scripts/validate_distribution_fits.py` — NOT invoked by the run-book
    - `code/scripts/utils/bonferroni.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_fits.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/game_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/load_game_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/game_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_mixed_effects.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/model_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/run_records.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/preprocess.py` — IS a run-book command
    - `code/scripts/fit_distributions.py` — IS a run-book command
    - `code/scripts/fit_mixed_effects.py` — IS a run-book command
    - `code/tests/test_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/run_records.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/runner_profiles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/runner_profiles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
