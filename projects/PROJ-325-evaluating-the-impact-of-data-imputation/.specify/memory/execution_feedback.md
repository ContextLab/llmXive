# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Imputation…”
- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generates synthetic data with specified para…”
- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic dataset for imputation s…”
- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic data to {args.output_csv}")…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar.parquet`
  - script usage: `synthetic_generator.py [-h] [--n-rows N_ROWS] [--mechanism {MCAR,MAR}]`
  - argparse error: `synthetic_generator.py: error: ambiguous option: --output could match --output-csv, --output-meta`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Imputation…”; code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generates synthetic data with specified para…”; code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic dataset for imputation s…”; 5 command(s) failed: python code/data/loader.py --source "gss"  --url "<GSS_URL>"  --output data/raw/gss_2018.parquet (rc=1); python code/data/loader.py --source "acs"  --url "<ACS_URL>"  --output data/raw/acs_income.parquet (rc=1); python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar.parquet (rc=2); 5 declared deliverable(s) absent: data/processed/baseline_results.json; data/processed/sensitivity_sweep_results.json; data/processed/synthetic_mar_v1.csv

## Failing / missing run-book commands

- python -c "import pandas; import sklearn; import statsmodels; import miceforest; print('Environment OK')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sklearn'
- python code/data/loader.py --source "gss"  --url "<GSS_URL>"  --output data/raw/gss_2018.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data/loader.py", line 18, in <module>
    from data_fetcher import fetch_and_save_data, compute_checksum, update_manifest_with_checksum, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data_fetcher.py", line 19, in <module>
    from data_ingestion import ingest_and_save
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data_ingestion.py", line 40, in <module>
    def detect_missingness(df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
                                                                        ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/data/loader.py --source "acs"  --url "<ACS_URL>"  --output data/raw/acs_income.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data/loader.py", line 18, in <module>
    from data_fetcher import fetch_and_save_data, compute_checksum, update_manifest_with_checksum, ensure_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data_fetcher.py", line 19, in <module>
    from data_ingestion import ingest_and_save
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data_ingestion.py", line 40, in <module>
    def detect_missingness(df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
                                                                        ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar.parquet -> rc=2
    usage: synthetic_generator.py [-h] [--n-rows N_ROWS] [--mechanism {MCAR,MAR}]
                              [--seed SEED] [--output-csv OUTPUT_CSV]
                              [--output-meta OUTPUT_META] [--schema SCHEMA]
synthetic_generator.py: error: ambiguous option: --output could match --output-csv, --output-meta
- python code/imputation/run_all.py  --input data/processed/synthetic_mar.parquet  --methods "cc,single,mice"  --mice-chains 4  --mice-iterations 1000  --burn-in 500  --output data/processed/imputation_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/imputation/run_all.py", line 24, in <module>
    from imputation_pipeline import perform_complete_case_analysis, run_complete_case_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/imputation_pipeline.py", line 16, in <module>
    from data_ingestion import detect_missingness
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data_ingestion.py", line 40, in <module>
    def detect_missingness(df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
                                                                        ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/metrics/bias.py  --results data/processed/imputation_results.json  --true-variance 150.5  --sweep-param "m"  --sweep-values "5,10,20"  --output data/reports/bias_analysis.json -> rc=1
    2026-07-28 21:30:55,985 - ERROR - Results file not found: data/processed/imputation_results.json

## Declared deliverables still missing

- data/processed/baseline_results.json
- data/processed/sensitivity_sweep_results.json
- data/processed/synthetic_mar_v1.csv
- data/processed/synthetic_mar_v1_meta.json
- data/raw/gss_2018_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/baseline_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_sweep_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/sensitivity_sweep_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_mar_v1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic_generator.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_mar_v1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_mar_v1_meta.json` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic_generator.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_mar_v1_meta.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gss_2018_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/variance_estimator.py` — NOT invoked by the run-book
    - `code/imputation_pipeline.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/data_fetcher.py` — NOT invoked by the run-book
    - `code/baseline_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gss_2018_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/imputation_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/imputation_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`.
