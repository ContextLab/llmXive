# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.ingest.load_illusions  --download  --output-dir data/raw`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.ingest.load_illusions  --download  --output-dir data/raw (rc=1); python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean (rc=1); python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 (rc=1); 11 declared deliverable(s) absent: data/clean/aligned_subjects.csv; data/clean/clean_muller_lyer.csv; data/clean/clean_ponzo.csv

## Failing / missing run-book commands

- python -m src.ingest.load_illusions  --download  --output-dir data/raw -> rc=1
di/src/ingest/load_illusions.py", line 670, in <module>
    main(sys.argv[1:])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 654, in main
    _process_one("muller")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 616, in _process_one
    _download_parquet(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 440, in _download_parquet
    raise RuntimeError(
RuntimeError: Failed to download parquet from any known REAL sources: ['openneuro/muller-lyer', 'OpenNeuro/muller-lyer', 'openneuro/muller_lyer', 'OpenNeuro/muller_lyer', 'psychology/muller_lyer']. Also attempted ``datasets`` fallback for psychology/muller_lyer and a HuggingFace Hub search for datasets matching the required schema ['subject_id', 'trial_id', 'stimulus_length', 'response_length', 'stimulus_parameters']. No real, publicly-reachable dataset with these columns was found; refusing to fabricate data. Please verify dataset availability or provide a direct URL.

- python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 670, in <module>
    main(sys.argv[1:])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 654, in main
    _process_one("muller")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-406-investigating-neural-signatures-of-predi/src/ingest/load_illusions.py", line 647, in _process_one
    raise RuntimeError(f"Raw parquet not found at {raw_path}. Run --download first.")
RuntimeError: Raw parquet not found at data/raw/muller_lyer.parquet. Run --download first.

- python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.model.predictive_coding

- python -m src.analysis.null_model  --input data/clean/clean_ponzo.csv  --output data/derived/ponzo_susceptibility.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.analysis.null_model

- python -m src.analysis.correlation  --precision data/derived/precision_parameters.csv  --susceptibility data/derived/ponzo_susceptibility.csv  --results outputs/correlation_results.json  --fig-dir outputs/figures  --bootstrap 1000  --permute 1000  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: No module named src.analysis.correlation


## Declared deliverables still missing

- data/clean/aligned_subjects.csv
- data/clean/clean_muller_lyer.csv
- data/clean/clean_ponzo.csv
- data/derived/beta_residuals.csv
- data/derived/lambda_residuals.csv
- data/derived/ponzo_null_parameters.csv
- data/derived/ponzo_susceptibility.csv
- data/derived/precision_parameters.csv
- data/merged/merged_results.csv
- data/raw/muller_lyer.parquet
- data/raw/ponzo.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/clean/aligned_subjects.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/clean/clean_muller_lyer.csv` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/clean/clean_muller_lyer.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/clean/clean_ponzo.csv` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/clean/clean_ponzo.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/beta_residuals.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/lambda_residuals.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_null_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_susceptibility.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/precision_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/merged/merged_results.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/raw/muller_lyer.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/muller_lyer.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ponzo.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ponzo.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
