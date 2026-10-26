# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.cli.run_diagnostic (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -m src.cli.run_diagnostic -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/src/cli/run_diagnostic.py", line 19, in <module>
    from src.lib.config import ensure_directories, RANDOM_SEED
ModuleNotFoundError: No module named 'src.lib.config'

- python -m pytest tests/ -> rc=2
config import DATA_DIR
E   ModuleNotFoundError: No module named 'lib'
_ ERROR collecting projects/PROJ-849-llmxive-follow-up-extending-agent-explor/tests/unit/test_tool_mapper.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-849-llmxive-follow-up-extending-agent-explor/tests/unit/test_tool_mapper.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_tool_mapper.py:7: in <module>
    from lib.tool_mapper import ToolMapper
E   ModuleNotFoundError: No module named 'lib'
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_analysis.py
ERROR tests/unit/test_analysis_service.py
ERROR tests/unit/test_metrics.py
ERROR tests/unit/test_retrieval_service.py
ERROR tests/unit/test_tool_mapper.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 5.41s ===============================


