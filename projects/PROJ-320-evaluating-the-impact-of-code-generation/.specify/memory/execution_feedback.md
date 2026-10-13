# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/generate_results_report.py: self-declared fabricated metric — “…hat your reported numbers are NOT real measurements"         # and "Make the PRO…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/prs_labeled.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/fetch_github.py --output data/raw/prs_raw.json`
  - script usage: `fetch_github.py [-h] [--limit LIMIT] [--target-llm TARGET_LLM]`
  - argparse error: `fetch_github.py: error: unrecognized arguments: --output data/raw/prs_raw.json`
- run-book command: `python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv`
  - script usage: `extract_metrics.py [-h] [--labeled-input LABELED_INPUT]`
  - argparse error: `extract_metrics.py: error: unrecognized arguments: --input data/processed/prs_labeled.csv`
- run-book command: `python code/analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json`
  - script usage: `sensitivity_analysis.py [-h] --metrics-path METRICS_PATH --labeled-path`
  - argparse error: `sensitivity_analysis.py: error: the following arguments are required: --metrics-path, --labeled-path`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/generate_results_report.py: self-declared fabricated metric — “…hat your reported numbers are NOT real measurements"         # and "Make the PRO…”; every produced artifact is gitignored (data/processed/prs_labeled.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/data/fetch_github.py --output data/raw/prs_raw.json (rc=2); python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv (rc=2); python code/analysis/statistical_tests.py --input data/processed/prs_metrics.csv --output reports/results.json (rc=1); 5 declared deliverable(s) absent: data/audit/error_rate.json; data/processed/complexity_scores.csv; data/processed/gate_status.json

## Failing / missing run-book commands

- python code/data/fetch_github.py --output data/raw/prs_raw.json -> rc=2

usage: fetch_github.py [-h] [--limit LIMIT] [--target-llm TARGET_LLM]
                       [--batch-size BATCH_SIZE] [--max-retries MAX_RETRIES]
                       [--raw-dir RAW_DIR]
fetch_github.py: error: unrecognized arguments: --output data/raw/prs_raw.json

- python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv -> rc=2

usage: extract_metrics.py [-h] [--labeled-input LABELED_INPUT]
                          [--complexity-input COMPLEXITY_INPUT]
                          [--output OUTPUT]
extract_metrics.py: error: unrecognized arguments: --input data/processed/prs_labeled.csv

- python code/analysis/statistical_tests.py --input data/processed/prs_metrics.csv --output reports/results.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 319, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 273, in main
    logger, config = setup_logging_and_config()
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 37, in setup_logging_and_config
    logger.log("setup_logging_and_config", script_name=script_name, config_keys=list(config.keys()))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/logging.py", line 72, in log
    logging.LogRecord(
    ^^^^^^^
NameError: name 'logging' is not defined

- python code/analysis/visualizations.py --input data/processed/prs_metrics.csv --output reports/figures/ -> rc=1
Starting visualization pipeline with input: data/processed/prs_metrics.csv
Error: Metrics file not found: data/processed/prs_metrics.csv


- python code/analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json -> rc=2

usage: sensitivity_analysis.py [-h] --metrics-path METRICS_PATH --labeled-path
                               LABELED_PATH --output-path OUTPUT_PATH
                               [--detector-threshold DETECTOR_THRESHOLD]
sensitivity_analysis.py: error: the following arguments are required: --metrics-path, --labeled-path

- python code/audit/manual_validation.py --input data/processed/prs_metrics.csv --output data/processed/audit_log.csv -> rc=1
tion.py", line 329, in main
    run_manual_validation(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/audit/manual_validation.py", line 227, in run_manual_validation
    logger.log("audit_start", input=input_csv, output_dir=output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/logging.py", line 72, in log
    logging.LogRecord(
    ^^^^^^^
NameError: name 'logging' is not defined

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/audit/manual_validation.py", line 347, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/audit/manual_validation.py", line 342, in main
    logger.log("audit_failed", error=str(e))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/logging.py", line 72, in log
    logging.LogRecord(
    ^^^^^^^
NameError: name 'logging' is not defined


## Declared deliverables still missing

- data/audit/error_rate.json
- data/processed/complexity_scores.csv
- data/processed/gate_status.json
- data/processed/prs_metrics.csv
- data/processed/results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/audit/error_rate.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/audit/error_rate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/complexity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/optimize_complexity_processing.py` — NOT invoked by the run-book
    - `code/analysis/save_complexity_scores.py` — NOT invoked by the run-book
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/complexity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gate_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gate_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prs_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/visualizations.py` — IS a run-book command
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/data/save_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prs_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/visualizations.py` — IS a run-book command
    - `code/audit/manual_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
