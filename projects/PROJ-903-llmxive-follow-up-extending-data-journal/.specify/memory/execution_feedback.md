# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_loader.py --dataset uci_har --mode download`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data_loader.py --dataset uci_har --mode download (rc=1); python code/main.py --dataset uci_har --seed 42 (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py --dataset uci_har --mode download -> rc=1
    2026-09-22 10:41:35,071 - __main__ - INFO - Starting download for dataset: uci_har
2026-09-22 10:41:35,071 - __main__ - ERROR - Failed to download uci_har: fetch_and_save_dataset() got an unexpected keyword argument 'dataset_name'
2026-09-22 10:41:35,071 - __main__ - ERROR - DataFetchError: Download failed for uci_har: fetch_and_save_dataset() got an unexpected keyword argument 'dataset_name'
- python code/main.py --dataset uci_har --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/main.py", line 32, in <module>
    from narrative.synthesizer import run_synthesis_pipeline
ModuleNotFoundError: No module named 'narrative.synthesizer'
