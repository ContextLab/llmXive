# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/utils/validate_metrics.py; 5 command(s) failed: python code/main.py --step preprocess --subjects all (rc=1); python code/main.py --step graph --atlas Schaefer_200 --density 0.20 (rc=1); python code/main.py --step stats --permutations 1000 (rc=1)

## Failing / missing run-book commands

- python code/main.py --step preprocess --subjects all -> rc=1
{"timestamp": "2026-10-12T16:18:51.049690", "level": "INFO", "logger": "__main__", "message": "Starting Brain Network Efficiency pipeline", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.049753", "level": "INFO", "logger": "__main__", "message": "Configuration validated", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.049792", "level": "ERROR", "logger": "__main__", "message": "Pipeline failed: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-190-investigating-the-relationship-between-b/data/raw'", "module": "logging", "function": "log_with_context", "line": 114}


- python code/main.py --step graph --atlas Schaefer_200 --density 0.20 -> rc=1
{"timestamp": "2026-10-12T16:18:51.252882", "level": "INFO", "logger": "__main__", "message": "Starting Brain Network Efficiency pipeline", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.252942", "level": "INFO", "logger": "__main__", "message": "Configuration validated", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.252992", "level": "ERROR", "logger": "__main__", "message": "Pipeline failed: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-190-investigating-the-relationship-between-b/data/raw'", "module": "logging", "function": "log_with_context", "line": 114}


- python code/main.py --step stats --permutations 1000 -> rc=1
{"timestamp": "2026-10-12T16:18:51.453245", "level": "INFO", "logger": "__main__", "message": "Starting Brain Network Efficiency pipeline", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.453307", "level": "INFO", "logger": "__main__", "message": "Configuration validated", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.453345", "level": "ERROR", "logger": "__main__", "message": "Pipeline failed: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-190-investigating-the-relationship-between-b/data/raw'", "module": "logging", "function": "log_with_context", "line": 114}


- python code/main.py --step report -> rc=1
{"timestamp": "2026-10-12T16:18:51.654991", "level": "INFO", "logger": "__main__", "message": "Starting Brain Network Efficiency pipeline", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.655052", "level": "INFO", "logger": "__main__", "message": "Configuration validated", "module": "logging", "function": "log_with_context", "line": 114}
{"timestamp": "2026-10-12T16:18:51.655091", "level": "ERROR", "logger": "__main__", "message": "Pipeline failed: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-190-investigating-the-relationship-between-b/data/raw'", "module": "logging", "function": "log_with_context", "line": 114}


- python code/utils/validate_metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-190-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-190-investigating-the-relationship-between-b/code/utils/validate_metrics.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=2
/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_verify_quality.py:18: in <module>
    from data.verify_quality import calculate_mean_fd_from_processed_data, verify_quality
code/data/__init__.py:4: in <module>
    from .download_hcp import download_with_retry, download_hcp_data, main
code/data/download_hcp.py:14: in <module>
    from ..utils.logging import get_logger, info, warning, error
E   ImportError: attempted relative import beyond top-level package
=========================== short test summary info ============================
ERROR tests/unit/test_connectivity.py
ERROR tests/unit/test_exclusion_filter.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_save_processed.py
ERROR tests/unit/test_save_processed_data.py
ERROR tests/unit/test_setup_data_dirs.py
ERROR tests/unit/test_thresholding.py
ERROR tests/unit/test_verify_quality.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 0.86s ===============================


