# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/synced.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.main --stage all`
- `python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/synced.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 (rc=1); python -m code.main --stage analyze --lags 0,1,2,3,6 (rc=1)

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1
_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_1998.txt

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 77, in main
    _run_fetch(start, end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 22, in _run_fetch
    fetch_ace(start, end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 113, in fetch_ace
    txt_p = _download_text(swepam_url)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 44, in _download_text
    raise ConnectionError(f"Unable to download {url}") from exc
ConnectionError: Unable to download https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_1998.txt

- python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
s
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_1998.txt

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 69, in main
    _run_fetch(args.start, args.end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 22, in _run_fetch
    fetch_ace(start, end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 113, in fetch_ace
    txt_p = _download_text(swepam_url)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 44, in _download_text
    raise ConnectionError(f"Unable to download {url}") from exc
ConnectionError: Unable to download https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_1998.txt

- python -m code.main --stage analyze --lags 0,1,2,3,6 -> rc=1

2026-10-17 15:08:53,631 INFO __main__: Running correlation analysis with lags [0, 1, 2, 3, 6]...
2026-10-17 15:08:53,631 ERROR __main__: Pipeline failed during stage analyze: run_correlation_analysis() missing 5 required positional arguments: 'df', 'composition_params', 'geomagnetic_indices', 'lags', and 'output_path'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 73, in main
    _run_analyze(lags_list)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 33, in _run_analyze
    run_correlation_analysis()
TypeError: run_correlation_analysis() missing 5 required positional arguments: 'df', 'composition_params', 'geomagnetic_indices', 'lags', and 'output_path'

- python -m code.main --stage validate -> rc=1

2026-10-17 15:08:54,343 INFO __main__: Running validation on held-out period...
2026-10-17 15:08:54,344 ERROR __main__: Pipeline failed during stage validate: run_validation_significance() missing 1 required positional argument: 'df_synced'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 75, in main
    _run_validate()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 37, in _run_validate
    run_validation_significance()
TypeError: run_validation_significance() missing 1 required positional argument: 'df_synced'

