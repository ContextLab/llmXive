# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_openneuro.py (rc=1); python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 (rc=1); python -m pytest -q tests/contract (rc=4); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/download_openneuro.py -> rc=1

2026-10-13 15:15:48,743 INFO __main__: Fetching dataset archive from https://openneuro.org/crn/datasets/ds000246/versions/latest/download
2026-10-13 15:15:48,744 INFO __main__: Downloading https://openneuro.org/crn/datasets/ds000246/versions/latest/download → /tmp/tmpq_6xfsu4/ds000246.tar.gz
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 231, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 106, in main
    download_file(archive_url, archive_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 46, in download_file
    r.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://openneuro.org/crn/datasets/ds000246/versions/latest/download

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
