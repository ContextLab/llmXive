# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `bash data/download.sh`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 run-book script(s) missing (plan/impl path mismatch): python analysis/baseline/align.py; python analysis/baseline/metrics.py; python analysis/baseline/plots.py   # creates reliability_diagram_raw.png, pit_histogram_raw.png; 5 command(s) failed: bash data/download.sh (rc=1); bash data/verify.sh   # exits with code 1 if `probability_value` missing (rc=1); python -m pytest tests/unit/ (rc=4)

## Failing / missing run-book commands

- bash data/download.sh -> rc=1
026-10-19 19:32:52,155 ERROR __main__: Failed to download dataset: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/subseasonal_rodeo/resolve/main/subseasonal_rodeo.tar.gz
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/src/download.py", line 205, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/src/download.py", line 199, in main
    download_dataset(url=args.url, out_path=out_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/code/src/download.py", line 135, in download_dataset
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/subseasonal_rodeo/resolve/main/subseasonal_rodeo.tar.gz

- bash data/verify.sh   # exits with code 1 if `probability_value` missing -> rc=1

2026-10-19 19:32:52,483 ERROR __main__: No parquet files found under /home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/data/raw
2026-10-19 19:32:52,483 ERROR __main__: Data Availability Gate Failed: no parquet files to inspect.

- python analysis/baseline/align.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/align.py': [Errno 2] No such file or directory

- python analysis/baseline/metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/metrics.py': [Errno 2] No such file or directory

- python analysis/baseline/plots.py   # creates reliability_diagram_raw.png, pit_histogram_raw.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/baseline/plots.py': [Errno 2] No such file or directory

- python analysis/isotonic/train.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/train.py': [Errno 2] No such file or directory

- python analysis/isotonic/evaluate.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/evaluate.py': [Errno 2] No such file or directory

- python analysis/isotonic/sensitivity.py   # runs 60/40 and 80/20 splits -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/isotonic/sensitivity.py': [Errno 2] No such file or directory

- python analysis/bayesian/model.py          # may fall back to isotonic -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/model.py': [Errno 2] No such file or directory

- python analysis/bayesian/prior_sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/prior_sensitivity.py': [Errno 2] No such file or directory

- python analysis/bayesian/diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/bayesian/diagnostics.py': [Errno 2] No such file or directory

- python analysis/comparison/diebold_mariano.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/comparison/diebold_mariano.py': [Errno 2] No such file or directory

- python analysis/comparison/summary.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-763-evaluating-calibration-of-probabilistic-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-763-evaluating-calibration-of-probabilistic-/analysis/comparison/summary.py': [Errno 2] No such file or directory

- python -m pytest tests/unit/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/


- python -m pytest tests/integration/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/


- python -m pytest tests/contract/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 0 items

============================ no tests ran in 0.01s =============================

ERROR: file or directory not found: tests/contract/


