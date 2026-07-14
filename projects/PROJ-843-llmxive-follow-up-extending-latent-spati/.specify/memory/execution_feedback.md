# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase data_prepare (rc=1); python code/main.py --phase extract_features (rc=1); python code/main.py --phase compute_geometry (rc=1); 2 declared deliverable(s) absent: data/raw/dense_baseline_frames.npy; data/results/sparse_warped_frames.npy

## Failing / missing run-book commands

- python code/main.py --phase data_prepare -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 30, in <module>
    from data import download as download_mod
ImportError: cannot import name 'download' from 'data' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/__init__.py)
- python code/main.py --phase extract_features -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 30, in <module>
    from data import download as download_mod
ImportError: cannot import name 'download' from 'data' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/__init__.py)
- python code/main.py --phase compute_geometry -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 30, in <module>
    from data import download as download_mod
ImportError: cannot import name 'download' from 'data' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/__init__.py)
- python code/main.py --phase evaluate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 30, in <module>
    from data import download as download_mod
ImportError: cannot import name 'download' from 'data' (/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/__init__.py)

## Declared deliverables still missing

- data/raw/dense_baseline_frames.npy
- data/results/sparse_warped_frames.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dense_baseline_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/data/schemas.py` — NOT invoked by the run-book
    - `code/eval/download_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/sensitivity.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dense_baseline_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sparse_warped_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/geometry/aggregate_warps.py` — NOT invoked by the run-book
    - `code/data/schemas.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sparse_warped_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
