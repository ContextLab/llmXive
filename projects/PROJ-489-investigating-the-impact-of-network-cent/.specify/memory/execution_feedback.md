# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/main.py --stage preprocess (rc=1); python code/main.py --stage metrics (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 6, in <module>
    from mne.datasets.sleep_physionet import fetch_data
ImportError: cannot import name 'fetch_data' from 'mne.datasets.sleep_physionet' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/mne/datasets/sleep_physionet/__init__.py)

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 10, in <module>
    from download import main as run_download
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 6, in <module>
    from mne.datasets.sleep_physionet import fetch_data
ImportError: cannot import name 'fetch_data' from 'mne.datasets.sleep_physionet' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/mne/datasets/sleep_physionet/__init__.py)

- python code/main.py --stage metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 10, in <module>
    from download import main as run_download
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 6, in <module>
    from mne.datasets.sleep_physionet import fetch_data
ImportError: cannot import name 'fetch_data' from 'mne.datasets.sleep_physionet' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/mne/datasets/sleep_physionet/__init__.py)

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 10, in <module>
    from download import main as run_download
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 6, in <module>
    from mne.datasets.sleep_physionet import fetch_data
ImportError: cannot import name 'fetch_data' from 'mne.datasets.sleep_physionet' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/mne/datasets/sleep_physionet/__init__.py)

- python code/main.py --stage report -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/main.py", line 10, in <module>
    from download import main as run_download
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-489-investigating-the-impact-of-network-cent/code/download.py", line 6, in <module>
    from mne.datasets.sleep_physionet import fetch_data
ImportError: cannot import name 'fetch_data' from 'mne.datasets.sleep_physionet' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-489-investigating-the-impact-of-network-cent/lib/python3.11/site-packages/mne/datasets/sleep_physionet/__init__.py)

