# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/visualize.py; python code/run_pipeline.py; 3 command(s) failed: python code/download_data.py (rc=1); python code/preprocess.py (rc=1); python code/model_fit.py (rc=1); 1 declared deliverable(s) absent: data/processed/analysis.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    {"timestamp": "2026-09-02T16:00:53.187430", "level": "INFO", "logger": "download_data", "message": "Starting download for dataset: openneuro/ds001435"}
{"timestamp": "2026-09-02T16:00:53.187611", "level": "INFO", "logger": "download_data", "message": "Attempting to connect to HuggingFace Hub for openneuro/ds001435..."}
{"timestamp": "2026-09-02T16:00:53.287264", "level": "ERROR", "logger": "download_data", "message": "Failed to download dataset: 401 Client Error. (Request ID: Root=1-6a984835-603e0f2713242b1b1f35ee09;e59fba24-f8b0-4363-8d67-014178c19722)\n\nRepository Not Found for url: https://huggingface.co/datasets/openneuro/ds001435/resolve/main/dataset_description.json.\nPlease make sure you specified the correct `repo_id` and `repo_type`.\nIf you are trying to access a private or gated repo, make sure you are authenticated.\nInvalid username or password."}
{"timestamp": "2026-09-02T16:00:53.287346", "level": "ERROR", "logger": "download_data", "message": "Fatal error during download: Dataset download failed. Verify internet access and dataset ID openneuro/ds001435."}
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py", line 14, in <module>
    from config import get_config, get_data_path, get_random_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/config.py", line 9, in <module>
    from dotenv import load_dotenv
ModuleNotFoundError: No module named 'dotenv'
- python code/model_fit.py -> rc=1
    76, in <module>
    from . import datasets, distributions, iolib, regression, robust, tools
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/lib/python3.11/site-packages/statsmodels/distributions/__init__.py", line 7, in <module>
    from .discrete import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/lib/python3.11/site-packages/statsmodels/distributions/discrete.py", line 5, in <module>
    from scipy._lib._util import _lazywhere
ImportError: cannot import name '_lazywhere' from 'scipy._lib._util' (/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/lib/python3.11/site-packages/scipy/_lib/_util.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py", line 18, in <module>
    raise ImportError("statsmodels is required. Install via: pip install statsmodels")
ImportError: statsmodels is required. Install via: pip install statsmodels
- python code/visualize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py': [Errno 2] No such file or directory
- python code/run_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_fit.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
