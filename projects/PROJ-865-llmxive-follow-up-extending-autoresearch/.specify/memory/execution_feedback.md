# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -c "from datasets import load_dataset; ds = load_dataset('claw-ai-lab/arc-bench', streaming=True); print(next(iter(ds)))"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py --stage ingest_and_distill; python code/main.py --stage execute_and_compare; python code/main.py --stage analyze; 13 declared deliverable(s) absent: data/artifacts/quantization_verification.json; data/artifacts/rule_validation_report.json; data/derived/baseline_resource_metrics.json

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; ds = load_dataset('claw-ai-lab/arc-bench', streaming=True); print(next(iter(ds)))" -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1698, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1325, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1211, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1168, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'claw-ai-lab/arc-bench' doesn't exist on the Hub or cannot be accessed.
- python code/main.py --stage ingest_and_distill -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/main.py': [Errno 2] No such file or directory
- python code/main.py --stage execute_and_compare -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/main.py': [Errno 2] No such file or directory
- python code/main.py --stage analyze -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/artifacts/quantization_verification.json
- data/artifacts/rule_validation_report.json
- data/derived/baseline_resource_metrics.json
- data/derived/baseline_results.json
- data/derived/error_taxonomy_results.json
- data/derived/experiment_manifest.csv
- data/derived/failure_cases.json
- data/derived/regression_results.json
- data/derived/results.csv
- data/derived/results_rule_engine.csv
- data/derived/rules_library.json
- data/derived/stratified_success_rates.csv
- data/derived/time_diff_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/quantization_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_annotation_distillation/verify_quantization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/quantization_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/rule_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_annotation_distillation/validate_rules.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/rule_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/baseline_resource_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/instrument_baseline.py` — NOT invoked by the run-book
    - `code/03_execution/run_baseline_external.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/baseline_resource_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/04_analysis/audit_resource_usage.py` — NOT invoked by the run-book
    - `code/03_execution/merge_results.py` — NOT invoked by the run-book
    - `code/03_execution/run_baseline_external.py` — NOT invoked by the run-book
    - `code/03_execution/run_experiments.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/error_taxonomy_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/04_analysis/error_taxonomy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/error_taxonomy_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/experiment_manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/03_execution/instrument_baseline.py` — NOT invoked by the run-book
    - `code/03_execution/generate_manifest.py` — NOT invoked by the run-book
    - `code/03_execution/merge_results.py` — NOT invoked by the run-book
    - `code/03_execution/run_experiments_test_runner.py` — NOT invoked by the run-book
    - `code/03_execution/run_baseline_external.py` — NOT invoked by the run-book
    - `code/03_execution/run_experiments.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/experiment_manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/failure_cases.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/annotate_failures.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/distill_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/log_metrics.py` — NOT invoked by the run-book
    - `code/04_analysis/error_taxonomy.py` — NOT invoked by the run-book
    - `code/04_analysis/validate_coverage.py` — NOT invoked by the run-book
    - `code/03_execution/generate_manifest.py` — NOT invoked by the run-book
    - `code/03_execution/rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/failure_cases.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/statistical_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/update_state.py` — NOT invoked by the run-book
    - `code/tests/test_rule_engine.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/04_analysis/error_taxonomy.py` — NOT invoked by the run-book
    - `code/04_analysis/calculate_stratified_rates.py` — NOT invoked by the run-book
    - `code/04_analysis/stratify_metrics.py` — NOT invoked by the run-book
    - `code/04_analysis/validate_results_schema.py` — NOT invoked by the run-book
    - `code/04_analysis/audit_resource_usage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/results_rule_engine.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/merge_results.py` — NOT invoked by the run-book
    - `code/03_execution/rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/results_rule_engine.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rules_library.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_rule_engine.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/validate_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/distill_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/retry_distill_loop.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/log_metrics.py` — NOT invoked by the run-book
    - `code/04_analysis/validate_coverage.py` — NOT invoked by the run-book
    - `code/03_execution/rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/rules_library.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/stratified_success_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/calculate_stratified_rates.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/stratified_success_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/time_diff_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/time_diff_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/time_diff_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
