# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/data/download.py; 1 command(s) failed: python -m pytest tests/ (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-356-predicting-molecular-toxicity-from-struc/src/data/download.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=1
___________

    def test_docs_directory_exists():
        """Verify the docs directory exists."""
>       expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "docs"
                        ^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: unsupported operand type(s) for /: 'FixtureFunctionDefinition' and 'str'

tests/test_setup.py:59: TypeError
=========================== short test summary info ============================
FAILED tests/test_setup.py::test_code_directory_exists - TypeError: unsupport...
FAILED tests/test_setup.py::test_src_directory_exists - TypeError: unsupporte...
FAILED tests/test_setup.py::test_tests_directory_exists - TypeError: unsuppor...
FAILED tests/test_setup.py::test_data_directory_exists - TypeError: unsupport...
FAILED tests/test_setup.py::test_results_directory_exists - TypeError: unsupp...
FAILED tests/test_setup.py::test_models_directory_exists - TypeError: unsuppo...
FAILED tests/test_setup.py::test_config_directory_exists - TypeError: unsuppo...
FAILED tests/test_setup.py::test_docs_directory_exists - TypeError: unsupport...
============================== 8 failed in 0.20s ===============================


