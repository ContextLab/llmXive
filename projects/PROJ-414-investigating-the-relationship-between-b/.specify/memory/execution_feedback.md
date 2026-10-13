# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_openneuro.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_openneuro.py (rc=1); python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 (rc=1); python -m pytest -q tests/contract (rc=4); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/download_openneuro.py -> rc=1
mpj9071578/ds000246_download.tar.gz
2026-10-13 16:09:31,923 WARNING __main__: Failed to download from https://openneuro.org/crn/datasets/ds000246/versions/latest/download?downloadType=zip: 404 Client Error: Not Found for url: https://openneuro.org/crn/datasets/ds000246/versions/latest/download?downloadType=zip
2026-10-13 16:09:31,924 INFO __main__: Downloading https://openneuro.org/crn/datasets/ds000246/versions/1.0.0/download → /tmp/tmptsjou02x/ds000246_download.tar.gz
2026-10-13 16:09:32,031 WARNING __main__: Failed to download from https://openneuro.org/crn/datasets/ds000246/versions/1.0.0/download: 404 Client Error: Not Found for url: https://openneuro.org/crn/datasets/ds000246/versions/1.0.0/download
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 289, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 165, in main
    raise RuntimeError(
RuntimeError: All attempts to download dataset ds000246 failed. Check internet connectivity and the OpenNeuro URL.

- python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.pipeline.run_all  --window_size 30  --step_size 5  --seed 123  --output_dir data/output/window30_step5  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_openneuro.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
