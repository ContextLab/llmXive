# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/utils/error_handlers.py: synthetic/fake INPUT data not authorized by the spec — “…nting silent failures or synthetic data generation. When a     M…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/test_full_pipeline.py --sample-size 100`
  - argparse error: `python -m pytest: error: unrecognized arguments: --sample-size 100`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/utils/error_handlers.py: synthetic/fake INPUT data not authorized by the spec — “…nting silent failures or synthetic data generation. When a     M…”; 7 command(s) failed: python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet (rc=1); python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet (rc=1); python code/modeling/split.py --input data/processed/crystal_molecules.parquet --output_dir data/splits (rc=1); 14 declared deliverable(s) absent: data/processed/crystal_dataset.csv; data/processed/grouped_dataset.csv; data/processed/split_indices.json

## Failing / missing run-book commands

- python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/ingestion/load_cod.py", line 18, in <module>
    from config import get_path_raw_data, ensure_directory
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/config.py", line 157, in <module>
    def create_parser() -> argparse.ArgumentParser:
                           ^^^^^^^^
NameError: name 'argparse' is not defined

- python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/ingestion/parse_cif.py", line 16, in <module>
    from config import get_path_raw_data, get_path_processed_data, ensure_directory
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/config.py", line 157, in <module>
    def create_parser() -> argparse.ArgumentParser:
                           ^^^^^^^^
NameError: name 'argparse' is not defined

- python code/modeling/split.py --input data/processed/crystal_molecules.parquet --output_dir data/splits -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/modeling/split.py", line 16, in <module>
    from config import get_path_processed_data, ensure_directory
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/config.py", line 157, in <module>
    def create_parser() -> argparse.ArgumentParser:
                           ^^^^^^^^
NameError: name 'argparse' is not defined

- python code/modeling/train.py --train data/splits/train.parquet --test data/splits/test.parquet --output data/results/model_metrics.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/modeling/train.py", line 18, in <module>
    from config import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/config.py", line 157, in <module>
    def create_parser() -> argparse.ArgumentParser:
                           ^^^^^^^^
NameError: name 'argparse' is not defined

- python code/analysis/interpret.py --model_path data/results/model_metrics.json --data data/splits/train.parquet --output data/results/feature_importance.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/analysis/interpret.py", line 19, in <module>
    from config import get_path_results, get_path_models, get_path_processed_data, ensure_directory
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/config.py", line 157, in <module>
    def create_parser() -> argparse.ArgumentParser:
                           ^^^^^^^^
NameError: name 'argparse' is not defined

- python -m pytest tests/unit/test_ingestion.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.12.4, cov-7.1.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_ingestion.py


- python -m pytest tests/integration/test_full_pipeline.py --sample-size 100 -> rc=4

ERROR: usage: python -m pytest [options] [file_or_dir] [file_or_dir] [...]
python -m pytest: error: unrecognized arguments: --sample-size 100
  inifile: /home/runner/work/llmXive/llmXive/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive



## Declared deliverables still missing

- data/processed/crystal_dataset.csv
- data/processed/grouped_dataset.csv
- data/processed/split_indices.json
- data/processing/streaming_metrics.json
- data/results/majority_class_baseline_metrics.json
- data/results/model_metrics.json
- data/results/mw_baseline_metrics.json
- data/results/polymorphism_metrics.json
- data/results/power_analysis.json
- data/results/power_analysis_threshold.json
- data/results/shap_analysis.json
- data/validation/fingerprint_check.json
- data/validation/report_check.json
- data/validation/success_criterion_check.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/crystal_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/interpret.py` — IS a run-book command
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/ingestion/run_pipeline.py` — NOT invoked by the run-book
    - `code/ingestion/validate_fingerprints.py` — NOT invoked by the run-book
    - `code/modeling/group_rare.py` — NOT invoked by the run-book
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/crystal_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/grouped_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/group_rare.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/validate_split.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/grouped_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/__init__.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/generate_overlap_gate_report.py` — NOT invoked by the run-book
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
    - `code/modeling/split.py` — IS a run-book command
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/validate_split.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processing/streaming_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/profiler.py` — NOT invoked by the run-book
    - `code/ingestion/run_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processing/streaming_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/majority_class_baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/majority_class_baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mw_baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
  Make ONE of these WRITE `data/results/mw_baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/polymorphism_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/execution/run_full_pipeline.py` — NOT invoked by the run-book
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/polymorphism_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/define_lift.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/power_analysis_threshold.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/define_lift.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/power_analysis_threshold.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_report.py` — NOT invoked by the run-book
    - `code/analysis/interpret.py` — IS a run-book command
  Make ONE of these WRITE `data/results/shap_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/validation/fingerprint_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/validate_fingerprints.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/fingerprint_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/validation/report_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/report_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/validation/success_criterion_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/success_criterion_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
