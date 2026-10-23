# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash code/run_pipeline.sh; 2 command(s) failed: python code/data_loader.py (rc=1); python -m pytest tests/ -v (rc=2); 3 declared deliverable(s) absent: data/processed/first_arrival_sweep.csv; data/raw/checksums.json; data/raw/ebd_subset.csv

## Failing / missing run-book commands

- python code/data_loader.py -> rc=1
 4024, in _iter_repo_tree_pages
    for page, finished in _paginate_pages(
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-126-predicting-avian-migration-patterns-from/lib/python3.11/site-packages/huggingface_hub/utils/_pagination.py", line 42, in _paginate_pages
    hf_raise_for_status(r)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-126-predicting-avian-migration-patterns-from/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 953, in hf_raise_for_status
    raise _format(RepositoryNotFoundError, message, response, repo_type=repo_type, repo_id=repo_id) from e
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6adb94aa-7f009d9d0a9e2660673f482e;25ba529f-f950-4ee3-8348-568c6c0f6888)

Repository Not Found for url: https://huggingface.co/api/models/vvud/eb-data/tree/main?recursive=true&expand=false.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- bash code/run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
- python -m pytest tests/ -v -> rc=2
866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_first_arrival_sweep.py
ERROR tests/unit/test_grid_aggregation.py
ERROR tests/unit/test_regional_map.py - NameError: name 'Optional' is not def...
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 23 warnings, 3 errors in 2.03s ========================



## Declared deliverables still missing

- data/processed/first_arrival_sweep.csv
- data/raw/checksums.json
- data/raw/ebd_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/first_arrival_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/first_arrival_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_loader.py` — IS a run-book command
    - `code/data_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ebd_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ebd_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
