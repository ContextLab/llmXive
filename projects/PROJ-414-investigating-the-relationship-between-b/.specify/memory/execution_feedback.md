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
ating-the-relationship-between-b/lib/python3.11/site-packages/datasets/load.py", line 1176, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-414-investigating-the-relationship-between-b/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'openneuro/ds000246' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-414-investigating-the-relationship-between-b/code/download_openneuro.py", line 94, in main
    raise RuntimeError(f"Failed to load dataset {dataset_id} from HuggingFace: {e}")
RuntimeError: Failed to load dataset ds000246 from HuggingFace: Dataset 'openneuro/ds000246' doesn't exist on the Hub or cannot be accessed.

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
