# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/fdr_correction.py: self-declared fabricated metric — “…# If not, we construct a mock results set based on the task requir…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ability.     Prioritizes synthetic data if marker exists, otherw…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…h):         logger.info("Synthetic data marker found. Loading sy…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ta marker found. Loading synthetic data.")         if not os.pat…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…hetic marker. Generating synthetic data.")             df = gene…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for the habit…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…: int = 42):     """     Generate synthetic longitudinal dataset.…”
- code/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with synthetic data     """     set_random_s…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50`
  - script usage: `synthetic_generator.py [-h] [--seed SEED] [--n_users N_USERS]`
  - argparse error: `synthetic_generator.py: error: argument --seed: invalid int value: '[RANDOM_SEED]'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 22 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/fdr_correction.py: self-declared fabricated metric — “…# If not, we construct a mock results set based on the task requir…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ability.     Prioritizes synthetic data if marker exists, otherw…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…h):         logger.info("Synthetic data marker found. Loading sy…”; 2 command(s) failed: python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50 (rc=2); python code/main.py (rc=1); 4 declared deliverable(s) absent: data/processed/merged_data.csv; data/processed/psychometrics.json; data/raw/synthetic_data.csv

## Failing / missing run-book commands

- python code/data/synthetic_generator.py --seed [RANDOM_SEED] --n_users --weeks 50 -> rc=2
    usage: synthetic_generator.py [-h] [--seed SEED] [--n_users N_USERS]
                              [--weeks WEEKS]
synthetic_generator.py: error: argument --seed: invalid int value: '[RANDOM_SEED]'
- python code/main.py -> rc=1
    mified-habit-tracking-o/code/data/synthetic_generator.py", line 119, in main
    df.to_csv(output_path, index=False)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/pandas/core/generic.py", line 3976, in to_csv
    return DataFrameRenderer(formatter).to_csv(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/pandas/io/formats/format.py", line 1025, in to_csv
    csv_formatter.save()
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/pandas/io/formats/csvs.py", line 251, in save
    with get_handle(
         ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/pandas/io/common.py", line 797, in get_handle
    check_parent_directory(str(handle))
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/site-packages/pandas/io/common.py", line 656, in check_parent_directory
    raise OSError(rf"Cannot save file into a non-existent directory: '{parent}'")
OSError: Cannot save file into a non-existent directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-138-the-effects-of-gamified-habit-tracking-o/code/data/raw'

## Declared deliverables still missing

- data/processed/merged_data.csv
- data/processed/psychometrics.json
- data/raw/synthetic_data.csv
- data/raw/synthetic_data_marker.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/versioning_runner.py` — NOT invoked by the run-book
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
    - `code/analysis/modeling.py` — NOT invoked by the run-book
    - `code/analysis/survival.py` — NOT invoked by the run-book
    - `code/tests/test_report.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/psychometrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/report_utils.py` — NOT invoked by the run-book
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
    - `code/scripts/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/psychometrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/user_traits.py` — NOT invoked by the run-book
    - `code/data/synthetic_generator.py` — IS a run-book command
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_data_marker.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/synthetic_generator.py` — IS a run-book command
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_data_marker.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
