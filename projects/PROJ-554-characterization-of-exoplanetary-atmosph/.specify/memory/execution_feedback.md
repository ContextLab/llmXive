# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis.py --input data/processed/analysis_dataset.csv --output results`
  - script usage: `analysis.py [-h] --retrieval-results RETRIEVAL_RESULTS --bootstrap-ci`
  - argparse error: `analysis.py: error: the following arguments are required: --retrieval-results, --bootstrap-ci`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 command(s) failed: python code/download.py --output data/raw (rc=1); python code/retrieval.py --input data/raw --output data/processed (rc=1); python code/analysis.py --input data/processed/analysis_dataset.csv --output results (rc=2); 7 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/bootstrap_ci.json; data/processed/correlation_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/main.py': [Errno 2] No such file or directory
- python code/download.py --output data/raw -> rc=1
    st recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 191, in main
    count = count_unique_planets()
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 57, in count_unique_planets
    if isinstance(config.data_dir, dict):
                  ^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'data_dir'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 206, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 191, in main
    count = count_unique_planets()
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/download.py", line 57, in count_unique_planets
    if isinstance(config.data_dir, dict):
                  ^^^^^^^^^^^^^^^
AttributeError: 'dict' object has no attribute 'data_dir'
- python code/retrieval.py --input data/raw --output data/processed -> rc=1
    Retrieval process failed: Input directory not found: data/raw
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 273, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 266, in main
    results = process_retrieval_results(args.input, args.output)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 227, in process_retrieval_results
    spectrum_files = load_spectrum_files(input_path)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-554-characterization-of-exoplanetary-atmosph/code/retrieval.py", line 146, in load_spectrum_files
    raise FileNotFoundError(f"Input directory not found: {input_dir}")
FileNotFoundError: Input directory not found: data/raw
- python code/analysis.py --input data/processed/analysis_dataset.csv --output results -> rc=2
    usage: analysis.py [-h] --retrieval-results RETRIEVAL_RESULTS --bootstrap-ci
                   BOOTSTRAP_CI --output OUTPUT
analysis.py: error: the following arguments are required: --retrieval-results, --bootstrap-ci

## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/bootstrap_ci.json
- data/processed/correlation_stats.json
- data/processed/mdc_stats.json
- data/processed/metadata.csv
- data/processed/regression_results.json
- data/processed/retrieval_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/uncertainty_reporting.py` — NOT invoked by the run-book
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/instrument_calibration.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/bootstrap_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/correlation_stats.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/bootstrap_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/correlation_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mdc_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_results.py` — NOT invoked by the run-book
    - `code/mdc_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mdc_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/noise_stability.py` — NOT invoked by the run-book
    - `code/retrieval.py` — IS a run-book command
    - `code/spectral_resolution_report.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/download.py` — IS a run-book command
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/regression_stats.py` — NOT invoked by the run-book
    - `code/analysis_tobit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/retrieval_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/plotting_residuals.py` — NOT invoked by the run-book
    - `code/robustness.py` — NOT invoked by the run-book
    - `code/retrieval.py` — IS a run-book command
    - `code/mdc_stats.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/detection_limit_analysis.py` — NOT invoked by the run-book
    - `code/plots_correlation.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/retrieval_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
