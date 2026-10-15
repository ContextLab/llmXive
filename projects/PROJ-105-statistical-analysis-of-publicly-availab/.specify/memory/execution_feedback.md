# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --year 2022`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py --year 2022 (rc=1); 3 declared deliverable(s) absent: data/results/model_comparison.json; data/results/tail_index_estimate.json; data/results/tail_ks.json

## Failing / missing run-book commands

- python code/main.py --year 2022 -> rc=1
tats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:24:48,038 - WARNING - Download attempt 4 failed: 404 Client Error: Not Found for url: https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:24:48,038 - pipeline - INFO - Retrying in 40 seconds...
2026-10-15 08:24:48,038 - INFO - Retrying in 40 seconds...
2026-10-15 08:25:28,038 - pipeline - INFO - Attempting download (attempt 5/5): https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:25:28,038 - INFO - Attempting download (attempt 5/5): https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:25:28,251 - pipeline - WARNING - Download attempt 5 failed: 404 Client Error: Not Found for url: https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:25:28,251 - WARNING - Download attempt 5 failed: 404 Client Error: Not Found for url: https://transtats.bts.gov/OT_Delay/On_Time_Reporting_CSV.zip
2026-10-15 08:25:28,251 - pipeline - ERROR - All 5 download attempts failed.
2026-10-15 08:25:28,251 - ERROR - All 5 download attempts failed.
2026-10-15 08:25:28,251 - ERROR - Pipeline Error: Failed to download BTS ZIP archive for year 2022 after 5 attempts.


## Declared deliverables still missing

- data/results/model_comparison.json
- data/results/tail_index_estimate.json
- data/results/tail_ks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/model_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/visualization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/tail_index_estimate.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/tail_index_estimate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/tail_ks.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/tail_ks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
