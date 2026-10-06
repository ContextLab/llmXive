# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data as a fallback.…”
- code/ingestion/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…gger.warning("Generating synthetic fallback data. This should not be used…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic WCST (Wisconsin Card Sor…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…e         DataFrame with synthetic WCST data.     """     np.random.s…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…(T010d)...")          # Generate synthetic data     df = generate_s…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…fo(f"Generated {len(df)} synthetic participant records")     log_info(f"Age ran…”
- code/task_t015_stimulus_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> None:     """     Generate synthetic nostalgia stimuli if rea…”
- code/task_t015_stimulus_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…mplementation: We do NOT generate synthetic stimuli here.     We rai…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data as a fallback.…”; code/ingestion/fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…gger.warning("Generating synthetic fallback data. This should not be used…”; code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic WCST (Wisconsin Card Sor…”; 2 command(s) failed: python code/main.py (rc=1); python code/analysis.py (rc=1); 12 declared deliverable(s) absent: data/processed/cleaned_age_filtered.csv; data/processed/cleaned_dataset.csv; data/processed/cleaned_dataset_no_mmse.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-10-06 12:55:53,574 - utils - INFO - Starting llmXive Pipeline Orchestration
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/main.py", line 106, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/main.py", line 103, in main
    return run_orchestration()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/main.py", line 32, in run_orchestration
    log_info(f"Project Root: {config['paths']['root']}")
                              ~~~~~~^^^^^^^^^
KeyError: 'paths'
- python code/analysis.py -> rc=1
    2026-10-06 12:55:54,728 - ERROR - Data Error: Cleaned dataset not found at ./data/processed/final_cleaned_dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/analysis.py", line 285, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/analysis.py", line 258, in main
    df = load_cleaned_dataset()
         ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/analysis.py", line 28, in load_cleaned_dataset
    raise DataNotFoundError(f"Cleaned dataset not found at {filepath}")
DataNotFoundError: Cleaned dataset not found at ./data/processed/final_cleaned_dataset.csv

## Declared deliverables still missing

- data/processed/cleaned_age_filtered.csv
- data/processed/cleaned_dataset.csv
- data/processed/cleaned_dataset_no_mmse.csv
- data/processed/exclusion_counts.json
- data/processed/exclusion_log.json
- data/processed/final_cleaned_dataset.csv
- data/processed/mmse_flag.json
- data/processed/validity_metrics.json
- data/raw/raw_dataset.csv
- data/results/robustness_report.json
- data/results/runtime_log.json
- data/results/sensitivity_comparison.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_age_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012a_age_exclusion.py` — NOT invoked by the run-book
    - `code/task_t012b_score_exclusion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_age_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t020_effect_sizes.py` — NOT invoked by the run-book
    - `code/task_t027b_mmse_robustness_analysis.py` — NOT invoked by the run-book
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t021_power_analysis.py` — NOT invoked by the run-book
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset_no_mmse.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t027b_mmse_robustness_analysis.py` — NOT invoked by the run-book
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
    - `code/generate_robustness_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset_no_mmse.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_counts.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t012a_age_exclusion.py` — NOT invoked by the run-book
    - `code/task_t012b_score_exclusion.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/task_t012c_generate_exclusion_log.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion/fetcher.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_counts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t014b_validity_metrics.py` — NOT invoked by the run-book
    - `code/task_t012d_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t015a_generate_metadata.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/task_t012c_generate_exclusion_log.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion/fetcher.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t021_power_analysis.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/task_t022_generate_report.py` — NOT invoked by the run-book
    - `code/assumption_checks.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mmse_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/task_t012d_mmse_flag.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mmse_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t014b_validity_metrics.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/raw_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t014b_validity_metrics.py` — NOT invoked by the run-book
    - `code/task_t010d_generate_simulation.py` — NOT invoked by the run-book
    - `code/run_t010b_fetch.py` — NOT invoked by the run-book
    - `code/task_t012a_age_exclusion.py` — NOT invoked by the run-book
    - `code/task_t012d_mmse_flag.py` — NOT invoked by the run-book
    - `code/task_t015a_generate_metadata.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/run_ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/raw_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t027b_mmse_robustness_analysis.py` — NOT invoked by the run-book
    - `code/task_t027c_compare_robustness.py` — NOT invoked by the run-book
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/generate_robustness_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/task_t015b_stimulus_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/task_t030_final_report.py` — NOT invoked by the run-book
    - `code/task_t027c_compare_robustness.py` — NOT invoked by the run-book
    - `code/task_t028_sensitivity_report.py` — NOT invoked by the run-book
    - `code/generate_robustness_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `runtime_log.json`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[paths]`
- PRODUCER(s) to edit: `code/main.py`
- CONSUMER(s) that read it: `code/main.py`, `code/task_t015b_stimulus_validation.py`
  → Edit the producer so every required name [paths] is in `runtime_log.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
