# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/regression_results_nonlinear.json, data/raw/wb_economic_data.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/regression_results_nonlinear.json, data/raw/wb_economic_data.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python code/data/clean.py (rc=1); python code/data/classify.py (rc=1); python code/analysis/visualization.py (rc=1); 7 declared deliverable(s) absent: data/processed/cbnrm_proxy_metadata.json; data/processed/merged_panel.csv; data/processed/metrics.json

## Failing / missing run-book commands

- python code/data/clean.py -> rc=1
    in__ - INFO - Starting T013: Data Merging and Cleaning
2026-10-07 03:43:55,308 - __main__ - INFO - Starting T013: Data Merging and Cleaning
2026-10-07 03:43:55,308 - __main__ - ERROR - FAO data file not found: data/raw/fao_land_use.csv
2026-10-07 03:43:55,308 - __main__ - ERROR - FAO data file not found: data/raw/fao_land_use.csv
2026-10-07 03:43:55,310 - __main__ - INFO - Loaded World Bank data: 0 rows
2026-10-07 03:43:55,310 - __main__ - INFO - Loaded World Bank data: 0 rows
2026-10-07 03:43:55,311 - __main__ - WARNING - CBNRM proxy data file not found: data/raw/cbnrm_proxy.csv. Proceeding without it for this merge.
2026-10-07 03:43:55,311 - __main__ - WARNING - CBNRM proxy data file not found: data/raw/cbnrm_proxy.csv. Proceeding without it for this merge.
2026-10-07 03:43:55,311 - __main__ - ERROR - Cannot proceed with merge: FAO or WB data missing.
2026-10-07 03:43:55,311 - __main__ - ERROR - Cannot proceed with merge: FAO or WB data missing.
2026-10-07 03:43:55,311 - __main__ - ERROR - Failed to complete T013: Required source data files are missing or empty.
2026-10-07 03:43:55,311 - __main__ - ERROR - Failed to complete T013: Required source data files are missing or empty.
- python code/data/classify.py -> rc=1
    2026-10-07 03:43:55,660 - __main__ - INFO - Starting T014: Regime Classification
2026-10-07 03:43:55,660 - __main__ - INFO - Starting T014: Regime Classification
2026-10-07 03:43:55,660 - __main__ - ERROR - CBNRM Proxy metadata missing: /home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/cbnrm_proxy_metadata.json. Cannot derive regime_type.
2026-10-07 03:43:55,660 - __main__ - ERROR - CBNRM Proxy metadata missing: /home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/cbnrm_proxy_metadata.json. Cannot derive regime_type.
2026-10-07 03:43:55,661 - __main__ - CRITICAL - CBNRM Proxy metadata missing. Cannot derive regime_type.
2026-10-07 03:43:55,661 - __main__ - CRITICAL - CBNRM Proxy metadata missing. Cannot derive regime_type.
- python code/analysis/visualization.py -> rc=1
    ession results file not found: {filepath}")
FileNotFoundError: Regression results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/regression_results_primary.json
2026-10-07 03:43:57,600 - __main__ - ERROR - Visualization generation failed: Regression results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/regression_results_primary.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/code/analysis/visualization.py", line 192, in main
    results = load_regression_results()
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/code/analysis/visualization.py", line 40, in load_regression_results
    raise FileNotFoundError(f"Regression results file not found: {filepath}")
FileNotFoundError: Regression results file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/regression_results_primary.json

## Declared deliverables still missing

- data/processed/cbnrm_proxy_metadata.json
- data/processed/merged_panel.csv
- data/processed/metrics.json
- data/processed/proxy_validation.json
- data/processed/regression_metadata.json
- data/processed/sensitivity_coefficients.json
- data/raw/fao_land_use.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cbnrm_proxy_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/classify.py` — IS a run-book command
    - `code/data/fetch_cbmrm_proxy.py` — NOT invoked by the run-book
    - `code/tests/test_data_clean.py` — NOT invoked by the run-book
    - `code/tests/test_data_fetch_cbmrm.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cbnrm_proxy_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_panel.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/classify.py` — IS a run-book command
    - `code/data/clean.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_panel.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/proxy_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/classify.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/proxy_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_coefficients.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_coefficients.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/fao_land_use.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fetch_merged_counts.py` — NOT invoked by the run-book
    - `code/data/clean.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/fao_land_use.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/cbnrm_proxy.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/fetch_cbmrm_proxy.py`, `code/data/fetch_merged_counts.py`, `code/data/download.py`, `code/data/clean.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/cbnrm_proxy.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/fetch_cbmrm_proxy.py`, `code/data/fetch_merged_counts.py`, `code/data/download.py`, `code/data/clean.py`, `code/tests/test_data_download.py`, `code/tests/test_data_fetch_cbmrm.py`.

### `data/raw/fao_land_use.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/fetch_merged_counts.py`, `code/data/clean.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/fao_land_use.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/fetch_merged_counts.py`, `code/data/clean.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/regression_results_primary.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/test_visualization.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-016-evaluating-the-effectiveness-of-communit/data/processed/regression_results_primary.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/tests/test_visualization.py`, `code/analysis/visualization.py`.
