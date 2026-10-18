# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.run_fidelity  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 (rc=1); python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 -> rc=1
main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/src/cli/run_fidelity.py", line 34, in <module>
    from sdv.tabular import CTGAN
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/__init__.py", line 17, in <module>
    from sdv import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/data_processing/__init__.py", line 3, in <module>
    from sdv.data_processing.data_processor import DataProcessor
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/data_processing/data_processor.py", line 12, in <module>
    from rdt.transformers import AnonymizedFaker, IDGenerator, get_default_transformers
ImportError: cannot import name 'IDGenerator' from 'rdt.transformers' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/rdt/transformers/__init__.py)

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def metric_data():
        if not METRIC_JSON.is_file():
>           pytest.fail(f"Metric results file not found: {METRIC_JSON}")
E           Failed: Metric results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/outputs/metrics/metric_results.json

tests/contract/test_metric_schema.py:34: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.26s


