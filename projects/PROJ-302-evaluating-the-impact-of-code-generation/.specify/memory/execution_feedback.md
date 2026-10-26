# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_acquisition/prompt_cohort_generator.py: synthetic/fake INPUT data not authorized by the spec — “…all back to filtering or synthetic data.  Output: data/processed…”
- code/data_acquisition/prompt_generator.py: synthetic/fake INPUT data not authorized by the spec — “…load)  Implements T014b: Generate a small synthetic cohort of code snippets…”
- code/data_acquisition/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…llback: Create a minimal synthetic input for demonstration if no…”
- code/feature_extraction/syntax_validator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Syntax Validator for Generated Synthetic Code.  This module valid…”
- code/synthetic_generation.py: synthetic/fake INPUT data not authorized by the spec — “…n pipeline.  This script generates two synthetic LLM cohorts (context‑bas…”
- code/synthetic_generation.py: synthetic/fake INPUT data not authorized by the spec — “…n() -> None:     """     Generate the two synthetic cohorts and write the re…”
- code/synthetic_generation.py: synthetic/fake INPUT data not authorized by the spec — “…log.info(f"Context‑based synthetic data written to {ctx_path}")…”
- code/synthetic_generation.py: synthetic/fake INPUT data not authorized by the spec — “…log.info(f"Prompt‑based synthetic data written to {prm_path}")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/data_acquisition/prompt_cohort_generator.py: synthetic/fake INPUT data not authorized by the spec — “…all back to filtering or synthetic data.  Output: data/processed…”; code/data_acquisition/prompt_generator.py: synthetic/fake INPUT data not authorized by the spec — “…load)  Implements T014b: Generate a small synthetic cohort of code snippets…”; code/data_acquisition/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…llback: Create a minimal synthetic input for demonstration if no…”; 1 command(s) failed: python code/main.py --full-run (rc=-1); 8 declared deliverable(s) absent: data/processed/analysis_results.json; data/processed/covariate_config.json; data/processed/intent_prompts.parquet

## Failing / missing run-book commands

- python code/main.py --full-run -> rc=-1

2026-10-26 01:27:40,608 INFO __main__: Running main() of 'code.data_acquisition' for stage 'data_acquisition'.
2026-10-26 01:27:40,608 INFO code.data_acquisition.data_acquisition: Fetching PRs for tensorflow/tensorflow
2026-10-26 01:28:07,216 WARNING code.data_acquisition.data_acquisition: Rate limit exceeded, sleeping for 785s before retry.

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/processed/analysis_results.json
- data/processed/covariate_config.json
- data/processed/intent_prompts.parquet
- data/processed/merged_features.parquet
- data/processed/runtime_report.json
- data/processed/sensitivity_summary.json
- data/synthetic/context_based.parquet
- data/synthetic/validation.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/significance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/covariate_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/feature_extraction.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/covariate_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/intent_prompts.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/prompt_engineering.py` — NOT invoked by the run-book
    - `code/synthetic_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/intent_prompts.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_features.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/feature_extraction.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/timestamp_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/runtime_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/runtime.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/runtime_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/synthetic/context_based.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_acquisition/cohort_analyzer.py` — NOT invoked by the run-book
    - `code/synthetic_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/synthetic/context_based.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/synthetic/validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/data_acquisition/prompt_cohort_generator.py` — NOT invoked by the run-book
    - `code/data_acquisition/prompt_generator.py` — NOT invoked by the run-book
    - `code/data_acquisition/synthetic_generator.py` — NOT invoked by the run-book
    - `code/feature_extraction/prompt_cohort_validator.py` — NOT invoked by the run-book
    - `code/feature_extraction/syntax_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/synthetic_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/synthetic/validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
