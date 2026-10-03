# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/descriptors/compute_descriptors.py: self-declared fabricated metric — “…ceholder implementation using dummy values if ionic radii not available…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/src/main.py --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/descriptors/compute_descriptors.py: self-declared fabricated metric — “…ceholder implementation using dummy values if ionic radii not available…”; 1 command(s) failed: python code/src/main.py --seed 42 (rc=1); 7 declared deliverable(s) absent: data/cleaned/merged_perovskite.csv; data/cleaned/normalized_thermal.csv; data/cleaned/provenance_report.json

## Failing / missing run-book commands

- python code/src/main.py --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-035-exploring-the-correlation-between-crysta/code/src/main.py", line 15, in <module>
    from src.ingest.fetch_thermal import main as fetch_thermal_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-035-exploring-the-correlation-between-crysta/src/ingest/fetch_thermal.py", line 29, in <module>
    from src.config.env import load_api_key, setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-035-exploring-the-correlation-between-crysta/src/config/__init__.py", line 3, in <module>
    from .env import (
ModuleNotFoundError: No module named 'src.config.env'

## Declared deliverables still missing

- data/cleaned/merged_perovskite.csv
- data/cleaned/normalized_thermal.csv
- data/cleaned/provenance_report.json
- data/descriptors.csv
- data/raw/thermal_raw.csv
- data/results/correlation_matrix.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/cleaned/merged_perovskite.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/contract/test_schema.py` — NOT invoked by the run-book
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/src/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/src/descriptors/compute_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/cleaned/merged_perovskite.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/cleaned/normalized_thermal.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_temperature_normalize.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/cleaned/normalized_thermal.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/cleaned/provenance_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_provenance_validator.py` — NOT invoked by the run-book
    - `code/src/cleaning/provenance_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/cleaned/provenance_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/unit/test_descriptors.py` — NOT invoked by the run-book
    - `code/src/main.py` — IS a run-book command
    - `code/src/analysis/stratify.py` — NOT invoked by the run-book
    - `code/src/analysis/run_vif_check.py` — NOT invoked by the run-book
    - `code/src/descriptors/compute_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/thermal_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_provenance_validator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_temperature_normalize.py` — NOT invoked by the run-book
    - `code/src/cleaning/clean_merge.py` — NOT invoked by the run-book
    - `code/src/cleaning/provenance_validator.py` — NOT invoked by the run-book
    - `code/src/ingest/fetch_thermal.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/thermal_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_matrix.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_correlation.py` — NOT invoked by the run-book
    - `code/src/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_matrix.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_sensitivity.py` — NOT invoked by the run-book
    - `code/src/utils/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/src/analysis/run_sensitivity_exec.py` — NOT invoked by the run-book
    - `code/src/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
