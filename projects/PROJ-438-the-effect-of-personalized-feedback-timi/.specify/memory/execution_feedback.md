# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python -m pytest tests/ -v (rc=4); 4 declared deliverable(s) absent: data/processed/learners_binned.csv; data/processed/learners_raw.csv; data/processed/results_metrics.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-438-the-effect-of-personalized-feedback-timi/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v -> rc=4

ImportError while loading conftest '/home/runner/work/llmXive/llmXive/projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/conftest.py'.
tests/conftest.py:9: in <module>
    @pytest.fixture(autouse=True)
E   NameError: name 'pytest' is not defined


## Declared deliverables still missing

- data/processed/learners_binned.csv
- data/processed/learners_raw.csv
- data/processed/results_metrics.csv
- data/processed/significance_stability_report.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/learners_binned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/bin_feedback_groups.py` — NOT invoked by the run-book
    - `code/generate_binned_learners.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/posthoc_tukey.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/verify_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/learners_binned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/learners_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/apply_exclusions.py` — NOT invoked by the run-book
    - `code/compute_intervals.py` — NOT invoked by the run-book
    - `code/generate_learners_raw.py` — NOT invoked by the run-book
    - `code/preprocess.py` — NOT invoked by the run-book
    - `code/schema.py` — NOT invoked by the run-book
    - `code/verify_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/learners_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/calculate_flip_rate.py` — NOT invoked by the run-book
    - `code/evaluate_effect_sizes.py` — NOT invoked by the run-book
    - `code/generate_results_metrics.py` — NOT invoked by the run-book
    - `code/generate_stability_report.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/significance_stability_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/calculate_stability.py` — NOT invoked by the run-book
    - `code/generate_results_metrics.py` — NOT invoked by the run-book
    - `code/generate_stability_report.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
    - `code/verify_flip_rate.py` — NOT invoked by the run-book
    - `code/verify_performance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/significance_stability_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
