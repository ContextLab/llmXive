# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- results/validation_correlations.csv: results file is EMPTY — the analysis produced no rows

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: results/validation_correlations.csv: results file is EMPTY — the analysis produced no rows; 2 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 (rc=1)

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1

2026-10-17 14:08:30,987 ERROR code: Both --start and --end are required for the full pipeline.

- python -m code.main --stage fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
le_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 179, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 153, in main
    _run_fetch(args.start, args.end)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/main.py", line 40, in _run_fetch
    ace_path = fetch_ace(start_date, end_date)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 113, in fetch_ace
    txt_p = _download_text(swepam_url)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-476-quantifying-correlations-between-solar-w/code/data/fetch_ace.py", line 44, in _download_text
    raise ConnectionError(f"Unable to download {url}") from exc
ConnectionError: Unable to download https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_1998.txt

