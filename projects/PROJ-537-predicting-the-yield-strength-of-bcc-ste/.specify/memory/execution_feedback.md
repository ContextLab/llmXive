# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 4 declared deliverable(s) absent: data/intermediate/merged.csv; data/results/output.json; data/results/shap_summary.png

## Failing / missing run-book commands

- python code/main.py -> rc=1

Failed to download data from https://matnavi.nims.go.jp/api/v1/datasets/bcc_steel_yield_strength: HTTPSConnectionPool(host='matnavi.nims.go.jp', port=443): Max retries exceeded with url: /api/v1/datasets/bcc_steel_yield_strength (Caused by NameResolutionError("HTTPSConnection(host='matnavi.nims.go.jp', port=443): Failed to resolve 'matnavi.nims.go.jp' ([Errno -2] Name or service not known)"))
MP_API_KEY environment variable not set.
Ingestion pipeline failed: Materials Project API key missing; cannot fetch DFT data.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/code/main.py", line 69, in run_ingestion_pipeline
    fetch_dft_data()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/code/ingestion/fetch_dft.py", line 105, in fetch_dft_data
    raise RuntimeError("Materials Project API key missing; cannot fetch DFT data.")
RuntimeError: Materials Project API key missing; cannot fetch DFT data.


## Declared deliverables still missing

- data/intermediate/merged.csv
- data/results/output.json
- data/results/shap_summary.png
- data/results/stability_distribution.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/intermediate/merged.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/finalize_dataset.py` — NOT invoked by the run-book
    - `code/ingestion/merge_and_filter.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/modeling/calculate_correlation.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/features.py` — NOT invoked by the run-book
    - `code/modeling/first_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/intermediate/merged.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/output.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_dft.py` — NOT invoked by the run-book
    - `code/ingestion/fetch_experimental.py` — NOT invoked by the run-book
    - `code/ingestion/finalize_dataset.py` — NOT invoked by the run-book
    - `code/ingestion/generate_checksums.py` — NOT invoked by the run-book
    - `code/ingestion/merge_and_filter.py` — NOT invoked by the run-book
    - `code/ingestion/update_state.py` — NOT invoked by the run-book
    - `code/interpretability/bootstrap_stability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/output.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_summary.png` is declared but was NOT written. Scripts referencing it:
    - `code/interpretability/plot_results.py` — NOT invoked by the run-book
    - `code/interpretability/shap_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/shap_summary.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_distribution.png` is declared but was NOT written. Scripts referencing it:
    - `code/interpretability/plot_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_distribution.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
