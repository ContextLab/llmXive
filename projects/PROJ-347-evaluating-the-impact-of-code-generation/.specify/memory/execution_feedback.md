# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.45 0.5 0.55`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.45 0.5 0.55 (rc=1); 1 declared deliverable(s) absent: data/checksums.json

## Failing / missing run-book commands

- python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.45 0.5 0.55 -> rc=1
uating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/load.py", line 2592, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/load.py", line 2264, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/load.py", line 1909, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-347-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/load.py", line 1855, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'devign' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/devign to ask for access.


## Declared deliverables still missing

- data/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_devign.py` — NOT invoked by the run-book
    - `code/download_juliet.py` — NOT invoked by the run-book
    - `src/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
