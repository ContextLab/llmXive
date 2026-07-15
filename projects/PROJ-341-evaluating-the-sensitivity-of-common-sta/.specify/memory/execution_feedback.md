# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/simulation_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --mode validation`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py (rc=1); python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 (rc=1); python code/main.py --mode validation (rc=1); 7 declared deliverable(s) absent: data/simulation/error_rates_summary.csv; data/simulation/p_values_raw.csv; data/simulation/real_data_power.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 22, in <module>
    from code.analysis.validator import main as validator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/validator.py", line 13, in <module>
    from ucimlrepo import fetch_dataset  # real data source (must be installed)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'fetch_dataset' from 'ucimlrepo' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/.venv/lib/python3.11/site-packages/ucimlrepo/__init__.py)
- python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 22, in <module>
    from code.analysis.validator import main as validator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/validator.py", line 13, in <module>
    from ucimlrepo import fetch_dataset  # real data source (must be installed)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'fetch_dataset' from 'ucimlrepo' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/.venv/lib/python3.11/site-packages/ucimlrepo/__init__.py)
- python code/main.py --mode validation -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/main.py", line 22, in <module>
    from code.analysis.validator import main as validator_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/analysis/validator.py", line 13, in <module>
    from ucimlrepo import fetch_dataset  # real data source (must be installed)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'fetch_dataset' from 'ucimlrepo' (/home/runner/work/llmXive/llmXive/projects/PROJ-341-evaluating-the-sensitivity-of-common-sta/code/.venv/lib/python3.11/site-packages/ucimlrepo/__init__.py)

## Declared deliverables still missing

- data/simulation/error_rates_summary.csv
- data/simulation/p_values_raw.csv
- data/simulation/real_data_power.json
- data/simulation/real_data_pvalues.csv
- data/simulation/thresholds.json
- data/simulation/validation_metrics.json
- data/simulation_metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/simulation/error_rates_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/comparative_plots.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/error_rates_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/p_values_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/simulation/output_writer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/p_values_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_power.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_power.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/real_data_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/validator.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
    - `code/analysis/real_data_runner.py` — NOT invoked by the run-book
    - `code/analysis/bootstrapper.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/real_data_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/thresholds.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/alpha_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/threshold_finder.py` — NOT invoked by the run-book
    - `code/visualization/plotter.py` — NOT invoked by the run-book
    - `code/visualization/saver.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/thresholds.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation/validation_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/validation_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation/validation_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/simulation_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/checksum_utils.py` — NOT invoked by the run-book
    - `code/utils/metadata_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/simulation_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
