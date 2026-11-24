# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess.py: self-declared fabricated metric — “…the file exists and return a mock value     that triggers the exclusi…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess.py: self-declared fabricated metric — “…the file exists and return a mock value     that triggers the exclusi…”; 5 command(s) failed: python code/main.py --stage validate_download --n-subjects 50 (rc=1); python code/main.py --stage preprocess (rc=1); python code/main.py --stage extract_metrics (rc=1); 3 declared deliverable(s) absent: data/atlas/network_label_map.csv; data/metrics/subject_metrics.csv; data/raw/valid_subjects.json

## Failing / missing run-book commands

- python code/main.py --stage validate_download --n-subjects 50 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/main.py", line 13, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/data/download.py", line 28, in <module>
    logging.FileHandler(project_root / 'logs' / 'download.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/logs/download.log'

- python code/main.py --stage preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/main.py", line 13, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/data/download.py", line 28, in <module>
    logging.FileHandler(project_root / 'logs' / 'download.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/logs/download.log'

- python code/main.py --stage extract_metrics -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/main.py", line 13, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/data/download.py", line 28, in <module>
    logging.FileHandler(project_root / 'logs' / 'download.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/logs/download.log'

- python code/main.py --stage statistical_analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/main.py", line 13, in <module>
    from data.download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/data/download.py", line 28, in <module>
    logging.FileHandler(project_root / 'logs' / 'download.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/logs/download.log'

- python -m pytest tests/ -> rc=2
on names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_verify_atlas_labels.py:13: in <module>
    from analysis.verify_atlas_labels import (
code/analysis/__init__.py:4: in <module>
    from .metrics import (
E   ImportError: cannot import name 'load_atlas_labels' from 'analysis.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-067-exploring-the-relationship-between-brain/code/analysis/metrics.py)
=========================== short test summary info ============================
ERROR tests/contract/test_metrics_schema.py
ERROR tests/unit/test_download.py - FileNotFoundError: [Errno 2] No such file...
ERROR tests/unit/test_metrics_parcellation.py
ERROR tests/unit/test_output_metrics.py
ERROR tests/unit/test_permutation.py
ERROR tests/unit/test_plot_results.py
ERROR tests/unit/test_power_analysis.py
ERROR tests/unit/test_stats.py
ERROR tests/unit/test_verify_atlas_labels.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.99s ===============================



## Declared deliverables still missing

- data/atlas/network_label_map.csv
- data/metrics/subject_metrics.csv
- data/raw/valid_subjects.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/atlas/network_label_map.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/verify_atlas_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/atlas/network_label_map.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/subject_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_stats_json.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/output_metrics.py` — NOT invoked by the run-book
    - `code/analysis/plot_results.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/subject_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/valid_subjects.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/output_metrics.py` — NOT invoked by the run-book
    - `code/data/cleanup.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/filter_subjects.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/valid_subjects.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
