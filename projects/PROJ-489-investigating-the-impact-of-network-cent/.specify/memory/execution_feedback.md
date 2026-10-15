# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/main.py --stage preprocess (rc=1); python code/main.py --stage metrics (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1

2026-10-15 00:32:39,114 - INFO - Fetching subject 0, night 1...
2026-10-15 00:32:39,114 - ERROR - Failed to fetch subject 0, night 1: fetch_data() got an unexpected keyword argument 'recordings'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 196, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 192, in main
    download_sleep_edf(output_dir=raw_dir, n_subjects=n_subj)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 132, in download_sleep_edf
    fetched_files = _fetch_sleep_data(
                    ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 82, in _fetch_sleep_data
    return fetch_func(
           ^^^^^^^^^^^
TypeError: fetch_data() got an unexpected keyword argument 'recordings'

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py", line 24, in <module>
    from scipy.signal import welch, coherency
ImportError: cannot import name 'coherency' from 'scipy.signal' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/scipy/signal/__init__.py)

- python code/main.py --stage metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py", line 24, in <module>
    from scipy.signal import welch, coherency
ImportError: cannot import name 'coherency' from 'scipy.signal' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/scipy/signal/__init__.py)

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py", line 24, in <module>
    from scipy.signal import welch, coherency
ImportError: cannot import name 'coherency' from 'scipy.signal' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/scipy/signal/__init__.py)

- python code/main.py --stage report -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py", line 24, in <module>
    from scipy.signal import welch, coherency
ImportError: cannot import name 'coherency' from 'scipy.signal' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/scipy/signal/__init__.py)

