# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.run_fidelity --smoke (rc=1); python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity --smoke -> rc=1

2026-10-21 19:35:49,528 INFO __main__: Running smoke test: Adult, CTGAN, Seed 42
2026-10-21 19:35:49,529 INFO src.data.loader: loading adult from OpenML dataset 1590 (UCI Adult)
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 136, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 96, in main
    loader_main(["--datasets", "adult"])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/data/loader.py", line 391, in main
    df = loader()  # fails loudly on any fetch failure
         ^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/data/loader.py", line 75, in load_adult
    import openml
ModuleNotFoundError: No module named 'openml'

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def schema():
        if not SCHEMA_YAML.is_file():
>           pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
E           Failed: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-statistical-fidelity/contracts/metric_results.schema.yaml

tests/contract/test_metric_schema.py:39: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.26s


