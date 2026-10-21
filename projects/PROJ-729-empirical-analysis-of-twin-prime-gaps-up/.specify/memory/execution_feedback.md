# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/analyze_local.py; python code/verify_citations.py; python code/report.py; 2 command(s) failed: python code/validate_schema.py (rc=1); python -m pytest tests/ (rc=1)

## Failing / missing run-book commands

- python code/validate_schema.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/validate_schema.py", line 163, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/validate_schema.py", line 137, in main
    logger = setup_logging("validate_schema")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/utils.py", line 18, in setup_logging
    logging.basicConfig(
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 2062, in basicConfig
    root.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'validate_schema'

- python code/analyze_local.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/analyze_local.py': [Errno 2] No such file or directory

- python code/verify_citations.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/verify_citations.py': [Errno 2] No such file or directory

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=1
figures/
    
        This script is idempotent; it will create directories if they do not exist
        and exit successfully if they already exist.
        """
        logger = setup_logging()
>       logger.info("Initializing data directory structure for twin prime gap analysis.")
E       AttributeError: 'NoneType' object has no attribute 'info'

code/setup_data_dirs.py:17: AttributeError
=========================== short test summary info ============================
FAILED tests/integration/test_analysis.py::test_analyze_gaps_pipeline_execution
FAILED tests/integration/test_analysis.py::test_parametric_bootstrap_reproducibility
FAILED tests/integration/test_generation.py::test_generation_pipeline - KeyEr...
FAILED tests/unit/test_setup_data_dirs.py::TestSetupDataDirs::test_ensure_directories_creates_new
FAILED tests/unit/test_setup_data_dirs.py::TestSetupDataDirs::test_ensure_directories_existing
FAILED tests/unit/test_setup_data_dirs.py::TestSetupDataDirs::test_setup_data_dirs_creates_expected_dirs
FAILED tests/unit/test_setup_data_dirs.py::TestSetupDataDirs::test_setup_data_dirs_handles_errors
========================= 7 failed, 18 passed in 1.40s =========================


