# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/derived/pipeline_execution_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -c "from datasets import load_dataset; ds = load_dataset('claw-ai-lab/arc-bench', streaming=True); print(next(iter(ds)))"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/derived/pipeline_execution_log.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/main.py --stage ingest_and_distill (rc=1); python code/main.py --stage execute_and_compare (rc=1); python code/main.py --stage analyze (rc=1); 11 declared deliverable(s) absent: data/artifacts/final_constitution_check.json; data/derived/coverage_report.json; data/derived/error_taxonomy.json

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; ds = load_dataset('claw-ai-lab/arc-bench', streaming=True); print(next(iter(ds)))" -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1667, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1290, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1176, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'claw-ai-lab/arc-bench' doesn't exist on the Hub or cannot be accessed.

- python code/main.py --stage ingest_and_distill -> rc=1
OJ-865-llmxive-follow-up-extending-autoresearch/code/02_annotation_distillation/distill_rules.py", line 184, in run_distill_pipeline
    failures = load_annotated_failures(input_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/02_annotation_distillation/distill_rules.py", line 81, in load_annotated_failures
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/derived/failure_cases_consensus.json

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/02_annotation_distillation/distill_rules.py", line 249, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/02_annotation_distillation/distill_rules.py", line 245, in main
    log_stage_end("distill_rules", status="failed", error=str(e))
TypeError: log_stage_end() got an unexpected keyword argument 'status'

- python code/main.py --stage execute_and_compare -> rc=1
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/03_execution/run_baseline.py", line 166, in main
    log_stage_start(logger, 'run_baseline_pilot')
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/utils/logging.py", line 47, in log_stage_start
    logger.info(f"--- Starting Stage: {stage_name} ---")
    ^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'info'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/03_execution/merge_results.py", line 219, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/03_execution/merge_results.py", line 178, in main
    log_stage_start(logger, "merge_results")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/utils/logging.py", line 47, in log_stage_start
    logger.info(f"--- Starting Stage: {stage_name} ---")
    ^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'info'

- python code/main.py --stage analyze -> rc=1
nner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/04_analysis/calculate_stratified_rates.py", line 158, in main
    results = load_results_csv(results_csv_path)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/04_analysis/calculate_stratified_rates.py", line 31, in load_results_csv
    raise FileNotFoundError(f"Results file not found: {filepath}")
FileNotFoundError: Results file not found: data/derived/results.csv

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/04_analysis/calculate_stratified_rates.py", line 199, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch/code/04_analysis/calculate_stratified_rates.py", line 187, in main
    log_stage_end("calculate_stratified_rates", status="failed", error=str(e))
TypeError: log_stage_end() got an unexpected keyword argument 'status'

- python -m pytest tests/unit/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/


- python -m pytest tests/contract/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-865-llmxive-follow-up-extending-autoresearch
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/artifacts/final_constitution_check.json
- data/derived/coverage_report.json
- data/derived/error_taxonomy.json
- data/derived/full_regression_results.json
- data/derived/full_results.csv
- data/derived/pilot_baseline_results.json
- data/derived/pilot_results.csv
- data/derived/pilot_rules.json
- data/derived/results.csv
- data/derived/rules_library.json
- data/derived/stratified_success_rates.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/final_constitution_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/final_constitution_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/coverage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_annotation_distillation/distill_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/log_metrics.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/retry_distill_loop.py` — NOT invoked by the run-book
    - `code/04_analysis/validate_coverage.py` — NOT invoked by the run-book
    - `code/annotation/distill_rules.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/coverage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/error_taxonomy.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/error_taxonomy.py` — NOT invoked by the run-book
    - `code/04_analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/04_analysis/statistical_model.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
    - `code/utils/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/error_taxonomy.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/full_regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/full_regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/full_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/validate_constitution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/full_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/pilot_baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/run_baseline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pilot_baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/pilot_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/run_rule_engine.py` — NOT invoked by the run-book
    - `code/04_analysis/statistical_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pilot_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/pilot_rules.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/run_baseline.py` — NOT invoked by the run-book
    - `code/03_execution/run_rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/pilot_rules.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_execution/analyze_baseline_failures.py` — NOT invoked by the run-book
    - `code/03_execution/instrument_baseline.py` — NOT invoked by the run-book
    - `code/03_execution/merge_results.py` — NOT invoked by the run-book
    - `code/03_execution/rule_engine.py` — NOT invoked by the run-book
    - `code/03_execution/run_baseline.py` — NOT invoked by the run-book
    - `code/03_execution/run_baseline_external.py` — NOT invoked by the run-book
    - `code/03_execution/run_experiments.py` — NOT invoked by the run-book
    - `code/03_execution/run_rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rules_library.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_annotation_distillation/distill_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/log_metrics.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/retry_distill_loop.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/validate_rules.py` — NOT invoked by the run-book
    - `code/02_annotation_distillation/visualize_rule_coverage.py` — NOT invoked by the run-book
    - `code/03_execution/rule_engine.py` — NOT invoked by the run-book
    - `code/03_execution/run_experiments.py` — NOT invoked by the run-book
    - `code/03_execution/run_rule_engine.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/rules_library.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/stratified_success_rates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_analysis/calculate_stratified_rates.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/stratified_success_rates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
