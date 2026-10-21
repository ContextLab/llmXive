# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.main --stage all`
- `python -m code.main --stage all --resume --run-id your_run_id`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage all --resume --run-id your_run_id (rc=1)

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1
2026-10-21 14:08:36,788 - pipeline - INFO - Executing full pipeline: download -> checksum
2026-10-21 14:08:36,788 - download - INFO - Downloading OpenML dataset 61 from https://www.openml.org/d/61
2026-10-21 14:08:36,789 - download - ERROR - Failed to download OpenML dataset 61: The 'data_id' parameter of fetch_openml must be an int in the range [1, inf) or None. Got '61' instead.


- python -m code.main --stage all --resume --run-id your_run_id -> rc=1
2026-10-21 14:08:37,373 - pipeline - INFO - Attempting to resume from checkpoint: your_run_id
2026-10-21 14:08:37,373 - pipeline - WARNING - No checkpoint found for run_id. Starting from scratch.
2026-10-21 14:08:37,373 - pipeline - INFO - Executing full pipeline: download -> checksum
2026-10-21 14:08:37,374 - download - INFO - Downloading OpenML dataset 61 from https://www.openml.org/d/61
2026-10-21 14:08:37,374 - download - ERROR - Failed to download OpenML dataset 61: The 'data_id' parameter of fetch_openml must be an int in the range [1, inf) or None. Got '61' instead.


