# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.pipelines.run_all  --max_tasks 150  --penalty_threshold 2.0  --seed 42 (rc=1); python -m pytest -q tests/contract (rc=1); 2 declared deliverable(s) absent: data/derived/task_definitions.csv; data/raw/τc_bench/tasks.json

## Failing / missing run-book commands

- python -m src.pipelines.run_all  --max_tasks 150  --penalty_threshold 2.0  --seed 42 -> rc=1
runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/src/pipelines/run_all.py", line 78, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/src/pipelines/run_all.py", line 58, in main
    download_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 158, in main
    dest_file = download_tasks_json()
                ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 139, in download_tasks_json
    merged_tasks = _load_tasks_via_hf_hub()
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 127, in _load_tasks_via_hf_hub
    raise RuntimeError("All huggingface_hub download attempts failed") from last_err
RuntimeError: All huggingface_hub download attempts failed

- python -m pytest -q tests/contract -> rc=1
/task_definitions.csv').is_file

tests/contract/test_task_schema.py:33: AssertionError
=============================== warnings summary ===============================
tests/contract/test_task_schema.py:15
tests/contract/test_task_schema.py:15
  /home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/tests/contract/test_task_schema.py:15: DeprecationWarning: jsonschema.RefResolver is deprecated as of v4.18.0, in favor of the https://github.com/python-jsonschema/referencing library, which provides more compliant referencing behavior as well as more flexible APIs for customization. A future release will remove RefResolver. Please file a feature request (on referencing) if you are missing an API for the kind of customization you need.
    from jsonschema import Draft7Validator, RefResolver

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/contract/test_task_schema.py::test_csv_exists - AssertionError: ...
ERROR tests/contract/test_task_schema.py::test_rows_conform_to_schema - json....
1 failed, 1 passed, 2 warnings, 1 error in 0.25s



## Declared deliverables still missing

- data/derived/task_definitions.csv
- data/raw/τc_bench/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/task_definitions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/parse_task_definitions.py` — NOT invoked by the run-book
    - `src/pipelines/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/task_definitions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/τc_bench/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_tau_c_bench.py` — NOT invoked by the run-book
    - `code/parse_task_definitions.py` — NOT invoked by the run-book
    - `src/pipelines/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/τc_bench/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
