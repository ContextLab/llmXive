# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_openneuro.py (rc=1); python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 (rc=1); python -m pytest -q tests/contract (rc=4)

## Failing / missing run-book commands

- python code/download_openneuro.py -> rc=1
(most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 83, in main
    response.raise_for_status()
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/lib/python3.11/site-packages/requests/models.py", line 1167, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://openneuro.org/api/datasets/ds000246/files

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 199, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 86, in main
    raise RuntimeError(f"Failed to fetch file list from OpenNeuro API: {e}")
RuntimeError: Failed to fetch file list from OpenNeuro API: 404 Client Error: Not Found for url: https://openneuro.org/api/datasets/ds000246/files

- python -m src.pipeline.run_all  --seed 42  --output_dir data/output  --min_subjects 20  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.pipeline.run_all  --window_size 30  --step_size 5  --seed 123  --output_dir data/output/window30_step5  --permutations 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/bin/python: Error while finding module specification for 'src.pipeline.run_all' (ModuleNotFoundError: No module named 'src')

