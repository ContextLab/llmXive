# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/download.py --dataset <dataset-name> (rc=1); python code/data/validate.py (rc=1); python code/features/classification.py (rc=1); 3 declared deliverable(s) absent: data/processed/features.csv; data/processed/labels_k2.csv; data/processed/labels_k3.csv

## Failing / missing run-book commands

- python code/data/download.py --dataset <dataset-name> -> rc=1
.py", line 89, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-290-the-impact-of-visual-search-strategies-o/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 3285, in dataset_info
    hf_raise_for_status(r)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-290-the-impact-of-visual-search-strategies-o/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 953, in hf_raise_for_status
    raise _format(RepositoryNotFoundError, message, response, repo_type=repo_type, repo_id=repo_id) from e
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6ae506e3-39e53bf500fd4c871fbdd8f7;9e03715a-4268-4d31-b874-9d1e8bc6063d)

Repository Not Found for url: https://huggingface.co/api/datasets/eyetracking-emotion-face-search/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- python code/data/validate.py -> rc=1

Failed to load dataset: No module named 'datasets'

- python code/features/classification.py -> rc=1
ocessed_features(logger)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-290-the-impact-of-visual-search-strategies-o/code/features/classification.py", line 23, in load_processed_features
    features_path = config.PROCESSED_FEATURES_PATH
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'PROCESSED_FEATURES_PATH'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-290-the-impact-of-visual-search-strategies-o/code/features/classification.py", line 225, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-290-the-impact-of-visual-search-strategies-o/code/features/classification.py", line 173, in main
    df = load_processed_features(logger)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-290-the-impact-of-visual-search-strategies-o/code/features/classification.py", line 23, in load_processed_features
    features_path = config.PROCESSED_FEATURES_PATH
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'PROCESSED_FEATURES_PATH'

- python code/analysis/lmm.py -> rc=1

Processed features file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-290-the-impact-of-visual-search-strategies-o/data/processed/features.csv. Run feature extraction tasks first.


## Declared deliverables still missing

- data/processed/features.csv
- data/processed/labels_k2.csv
- data/processed/labels_k3.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/lmm.py` — IS a run-book command
    - `code/analysis/posthoc_power.py` — NOT invoked by the run-book
    - `code/analysis/results_table.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/data/exclusion.py` — NOT invoked by the run-book
    - `code/data/roi_fallback.py` — NOT invoked by the run-book
    - `code/features/__init__.py` — NOT invoked by the run-book
    - `code/features/classification.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels_k2.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features/sensitivity_clustering.py` — NOT invoked by the run-book
    - `code/run_t037b_hash_after_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels_k2.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels_k3.csv` is declared but was NOT written. Scripts referencing it:
    - `code/features/sensitivity_clustering.py` — NOT invoked by the run-book
    - `code/run_t037b_hash_after_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels_k3.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
