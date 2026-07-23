# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- data/results/harmonized_vs_synthetic_comparison.json: self-declared fabricated metric — “…ts detected. (Note: This is a placeholder result until the full pipeline is ex…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic metagenomic count data.…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic sleep architecture metri…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “….DataFrame]:     """     Generate a complete synthetic dataset with metagenomic…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…e ) -> Dict:     """     Generate a synthetic data manifest log (NOT a…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…titution Principle I for synthetic data validation only.      Ar…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…"note": "This is a synthetic dataset for pipeline validation.…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…try point for generating synthetic data.     Parses command line…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 28 fabricated/simulated-result signal(s) — results are not real measurements: data/results/harmonized_vs_synthetic_comparison.json: self-declared fabricated metric — “…ts detected. (Note: This is a placeholder result until the full pipeline is ex…”; code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic metagenomic count data.…”; code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic sleep architecture metri…”; 2 command(s) failed: python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv (rc=1); python code/main.py --input data/raw/synthetic_data.csv --output data/results/ (rc=1); 7 declared deliverable(s) absent: data/metadata/synthetic_data_manifest.json; data/processed/filtered_data.parquet; data/raw/large_proxy.csv

## Failing / missing run-book commands

- python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-340-investigating-the-correlation-between-gu/code/ingest.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --input data/raw/synthetic_data.csv --output data/results/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-340-investigating-the-correlation-between-gu/code/main.py", line 14, in <module>
    from ingest import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-340-investigating-the-correlation-between-gu/code/ingest.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/metadata/synthetic_data_manifest.json
- data/processed/filtered_data.parquet
- data/raw/large_proxy.csv
- data/results/collinearity_report.json
- data/results/correlation_matrix.json
- data/results/sensitivity_analysis.json
- data/results/variable_load_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/synthetic_data_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/audit_fabrication.py` — NOT invoked by the run-book
    - `code/data_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/synthetic_data_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/run_real_data_pipeline.py` — NOT invoked by the run-book
    - `code/run_streaming_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/large_proxy.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/run_6_hour_stress_test.py` — NOT invoked by the run-book
    - `code/run_streaming_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/large_proxy.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/collinearity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — NOT invoked by the run-book
    - `code/run_real_data_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/collinearity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/validate_harmonized_results.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
    - `code/run_real_data_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/validate_harmonized_results.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
    - `code/run_real_data_pipeline.py` — NOT invoked by the run-book
    - `code/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/variable_load_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/variable_load_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
