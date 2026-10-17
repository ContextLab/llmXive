# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: overall deadline 300s exceeded; 1 command(s) failed: python -m code.main --thin (rc=1); 4 declared deliverable(s) absent: data/results/cost_metrics.csv; data/results/metrics_raw.csv; data/results/pipeline_log.csv

## Failing / missing run-book commands

- python -m code.main --thin -> rc=1
_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/huggingface_hub/file_download.py", line 1194, in _hf_hub_download_to_cache_dir
    _raise_on_head_call_error(head_call_error, force_download, local_files_only)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/huggingface_hub/file_download.py", line 1953, in _raise_on_head_call_error
    raise head_call_error
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6ad3c84f-126faaa722173c1648f03364;e0148756-350c-4b75-bbfc-5dd47dadbb0f)

Repository Not Found for url: https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.


## Declared deliverables still missing

- data/results/cost_metrics.csv
- data/results/metrics_raw.csv
- data/results/pipeline_log.csv
- data/results/uq_methods.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/cost_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/metrics/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pipeline_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pipeline_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/uq_methods.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/uq_methods.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
