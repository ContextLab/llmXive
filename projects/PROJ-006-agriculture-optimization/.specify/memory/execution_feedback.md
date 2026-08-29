# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/validate_dataset_schema.py: self-declared fabricated metric — “…n required}         # Provide dummy values for required fields to avoid…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/cli/run_pipeline.py --stage ingest`
  - script usage: `run_pipeline.py [-h] [--no-synthetic] [--dry-run]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --stage ingest`
- run-book command: `python src/cli/run_pipeline.py --stage ingest --use-synthetic`
  - script usage: `run_pipeline.py [-h] [--no-synthetic] [--dry-run]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --stage ingest --use-synthetic`
- run-book command: `python src/cli/run_pipeline.py --stage full`
  - script usage: `run_pipeline.py [-h] [--no-synthetic] [--dry-run]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --stage full`
- run-book command: `python src/cli/validate.py --input data/processed/analysis_dataset.csv --contract contracts/dataset.schema.yaml`
  - script usage: `validate.py [-h] [--schema-type {dataset,regression,sensitivity}]`
  - argparse error: `validate.py: error: unrecognized arguments: --input --contract contracts/dataset.schema.yaml`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/validate_dataset_schema.py: self-declared fabricated metric — “…n required}         # Provide dummy values for required fields to avoid…”; 4 command(s) failed: python src/cli/run_pipeline.py --stage ingest (rc=2); python src/cli/run_pipeline.py --stage ingest --use-synthetic (rc=2); python src/cli/run_pipeline.py --stage full (rc=2); 2 declared deliverable(s) absent: data/processed/analysis_dataset.csv; data/processed/regression_results.json

## Failing / missing run-book commands

- python src/cli/run_pipeline.py --stage ingest -> rc=2
    usage: run_pipeline.py [-h] [--no-synthetic] [--dry-run]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
run_pipeline.py: error: unrecognized arguments: --stage ingest
- python src/cli/run_pipeline.py --stage ingest --use-synthetic -> rc=2
    usage: run_pipeline.py [-h] [--no-synthetic] [--dry-run]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
run_pipeline.py: error: unrecognized arguments: --stage ingest --use-synthetic
- python src/cli/run_pipeline.py --stage full -> rc=2
    usage: run_pipeline.py [-h] [--no-synthetic] [--dry-run]
                       [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
run_pipeline.py: error: unrecognized arguments: --stage full
- python src/cli/validate.py --input data/processed/analysis_dataset.csv --contract contracts/dataset.schema.yaml -> rc=2
    usage: validate.py [-h] [--schema-type {dataset,regression,sensitivity}]
                   [--no-strict]
                   file_path
validate.py: error: unrecognized arguments: --input --contract contracts/dataset.schema.yaml

## Declared deliverables still missing

- data/processed/analysis_dataset.csv
- data/processed/regression_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/generators/synthetic_generator.py` — NOT invoked by the run-book
    - `code/src/cli/validate.py` — NOT invoked by the run-book
    - `code/src/cli/run_pipeline.py` — NOT invoked by the run-book
    - `code/tests/contract/test_validate_cli.py` — NOT invoked by the run-book
    - `code/tests/integration/test_ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/cli/validate.py` — NOT invoked by the run-book
    - `code/tests/contract/test_validate_cli.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
