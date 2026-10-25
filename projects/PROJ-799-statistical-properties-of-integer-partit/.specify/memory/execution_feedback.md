# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python -m pytest tests/ -v (rc=2); 3 declared deliverable(s) absent: data/processed/features.csv; data/processed/model_results.json; data/raw/partition_counts.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-799-statistical-properties-of-integer-partit/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=2
-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

tests/test_pipeline.py:25
  /home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/tests/test_pipeline.py:25: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(3600)  # 1 hour = 3600 seconds

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_asymptotic_formula.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 15 warnings, 1 error in 1.05s =========================



## Declared deliverables still missing

- data/processed/features.csv
- data/processed/model_results.json
- data/raw/partition_counts.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/regression_model.py` — NOT invoked by the run-book
    - `code/visualize_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/regression_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/partition_counts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_partitions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/partition_counts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
