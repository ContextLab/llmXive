# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 (rc=1); 1 declared deliverable(s) absent: data/raw/τc_bench/tasks.json

## Failing / missing run-book commands

- python -m src.pipelines.run_all  --max_tasks 200  --penalty_threshold 2.0  --seed 42 -> rc=1
", line 116, in main
    dest_file = download_tasks_json()
                ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 93, in download_tasks_json
    merged_tasks = _fetch_via_hf()
                   ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/code/download_tau_c_bench.py", line 77, in _fetch_via_hf
    raise RuntimeError(f"Could not reach HuggingFace repository {HF_REPO}: {exc}") from exc
RuntimeError: Could not reach HuggingFace repository sierra-research/tau-bench: 401 Client Error. (Request ID: Root=1-6acd3e58-5b14025d2ba20a3116bd785b;5d7b42f0-ab90-4f97-924e-23590670a312)

Repository Not Found for url: https://huggingface.co/datasets/sierra-research/tau-bench/resolve/main/retail/test.json.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.


## Declared deliverables still missing

- data/raw/τc_bench/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/τc_bench/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_tau_c_bench.py` — NOT invoked by the run-book
    - `src/pipelines/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/τc_bench/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
