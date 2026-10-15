# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/main.py --stage preprocess (rc=1); python code/main.py --stage metrics (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1

2026-10-15 05:09:29,685 - INFO - Fetching subject 0, night 1...
2026-10-15 05:09:29,685 - ERROR - Failed to fetch subject 0, night 1: module 'mne.datasets.sleep_physionet' has no attribute 'fetch_data'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 171, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 167, in main
    download_sleep_edf(output_dir=raw_dir, n_subjects=n_subj)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 117, in download_sleep_edf
    edf_path = _download_one_record(subject, night, base_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 59, in _download_one_record
    fetched = sleep_physionet.fetch_data(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'mne.datasets.sleep_physionet' has no attribute 'fetch_data'

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

- python code/main.py --stage report -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 12, in <module>
    from metrics import main as run_metrics
ImportError: cannot import name 'main' from 'metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/metrics.py)

