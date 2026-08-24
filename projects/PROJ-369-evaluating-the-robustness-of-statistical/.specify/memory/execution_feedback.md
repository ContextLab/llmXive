# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/main.py --stage ingestion; python src/main.py --stage preprocessing; python src/main.py --stage synthesis; 5 declared deliverable(s) absent: data/processed/metrics.json; data/results/baseline_status.json; data/results/filtered_features.json

## Failing / missing run-book commands

- python src/main.py --stage ingestion -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage preprocessing -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage synthesis -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage hypothesis_testing -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage regression -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory
- python src/main.py --stage viz -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-369-evaluating-the-robustness-of-statistical/src/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/metrics.json
- data/results/baseline_status.json
- data/results/filtered_features.json
- data/results/null_distribution_gate.json
- data/results/regression_model.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/schemas.py` — NOT invoked by the run-book
    - `code/src/data/metrics.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/contract/test_schemas.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_stability.py` — NOT invoked by the run-book
    - `code/tests/unit/test_integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t010a_metrics_real.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/filtered_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_stability.py` — NOT invoked by the run-book
    - `code/tests/unit/test_integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_inputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/filtered_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/null_distribution_gate.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/null_distribution_gate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_model.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/utils/integrity_checker.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression_stability.py` — NOT invoked by the run-book
    - `code/tests/unit/test_integrity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_model.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
