# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/experiment/experiment.py --mode mock --participants 3; python code/generation/doc_pipeline.py  --repo  --commit abc123def456  --output data/processed/docs/repo_docs.md; python code/analysis/stats_runner.py  --input data/processed/task_logs_anon.json  --output data/processed/analysis_results.json; 6 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/validation_report.json; data/raw/participant_logs.json

## Failing / missing run-book commands

- python code/experiment/experiment.py --mode mock --participants 3 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/experiment/experiment.py': [Errno 2] No such file or directory
- python code/generation/doc_pipeline.py  --repo  --commit abc123def456  --output data/processed/docs/repo_docs.md -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/generation/doc_pipeline.py': [Errno 2] No such file or directory
- python code/analysis/stats_runner.py  --input data/processed/task_logs_anon.json  --output data/processed/analysis_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/analysis/stats_runner.py': [Errno 2] No such file or directory
- python code/utils/logging.py --track  --command "python code/analysis/stats_runner.py..." -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/code/utils/logging.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/cleaned_dataset.csv
- data/processed/validation_report.json
- data/raw/participant_logs.json
- data/raw/repo_covariates.json
- data/raw/repo_metrics.json
- data/raw/repo_selection_rubric.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participant_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_collection.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participant_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_covariates.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/run_covariate_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_covariates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_rubric_and_metrics.py` — NOT invoked by the run-book
    - `code/repo_metrics_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/repo_selection_rubric.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_rubric_and_metrics.py` — NOT invoked by the run-book
    - `code/repo_metrics_runner.py` — NOT invoked by the run-book
    - `code/run_covariate_collection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/repo_selection_rubric.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
