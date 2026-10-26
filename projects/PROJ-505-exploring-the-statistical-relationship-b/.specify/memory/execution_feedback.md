# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”
- code/ingestion/download_real.py: synthetic/fake INPUT data not authorized by the spec — “…nvokes the deterministic synthetic data generator (task T015) as…”
- code/ingestion/download_real.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> dict:     """     Generate deterministic synthetic data as a fallback when…”
- code/ingestion/download_real.py: synthetic/fake INPUT data not authorized by the spec — “…)     log.info(         "Synthetic fallback data generated for period %s.…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate deterministic synthetic solar‑wind and geomagnet…”
- code/ingestion/run_download_real.py: synthetic/fake INPUT data not authorized by the spec — “…lts to the deterministic synthetic data path) to continue withou…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”; code/ingestion/download_real.py: synthetic/fake INPUT data not authorized by the spec — “…nvokes the deterministic synthetic data generator (task T015) as…”; code/ingestion/download_real.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> dict:     """     Generate deterministic synthetic data as a fallback when…”; 4 command(s) failed: python -m code.verify_requirements (rc=1); python -m code.main (rc=1); python -m code.ingestion.download_real_composition --start 2000-01-01 --end 2020-12-31 --output data/raw/real_composition.parquet (rc=1); 5 declared deliverable(s) absent: data/artifacts/alignment_report.json; data/artifacts/cv_metrics.json; data/artifacts/delta_r2.json

## Failing / missing run-book commands

- python -m code.verify_requirements -> rc=1
Xive/projects/PROJ-505-exploring-the-statistical-relationship-b/requirements.txt
2026-10-26 13:36:15,275 WARNING __main__: pip install exited with code 1 – proceeding because pinning validation is the primary objective.
2026-10-26 13:36:15,275 INFO __main__: Validating requirement pinning patterns
2026-10-26 13:36:15,275 ERROR __main__: Invalid requirement at line 7: fastparquet==2024.*
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/verify_requirements.py", line 108, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/verify_requirements.py", line 100, in main
    _validate_pinning(req_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/verify_requirements.py", line 77, in _validate_pinning
    raise ValueError("One or more requirement lines do not match the required pattern")
ValueError: One or more requirement lines do not match the required pattern

- python -m code.main -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 81, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/logging.py", line 76, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 40, in main
    raise FileNotFoundError(
FileNotFoundError: Aligned data not found at data/processed/aligned_hourly.parquet. Run the alignment step before executing the main driver.

- python -m code.ingestion.download_real_composition --start 2000-01-01 --end 2020-12-31 --output data/raw/real_composition.parquet -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-505-exploring-the-statistical-relationship-b/bin/python: No module named code.ingestion.download_real_composition

- python -m code.main --quick   # processes only the initial subset of rows for rapid debugging -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 81, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/utils/logging.py", line 76, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 40, in main
    raise FileNotFoundError(
FileNotFoundError: Aligned data not found at data/processed/aligned_hourly.parquet. Run the alignment step before executing the main driver.


## Declared deliverables still missing

- data/artifacts/alignment_report.json
- data/artifacts/cv_metrics.json
- data/artifacts/delta_r2.json
- data/processed/aligned_hourly.parquet
- data/processed/with_coupling.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/alignment_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/align.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/alignment_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/cv_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/cross_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/cv_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/delta_r2.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/cross_validation.py` — NOT invoked by the run-book
    - `code/analysis/integrate_results.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/delta_r2.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_hourly.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/coupling_functions.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/ingestion/align.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/aligned_hourly.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/with_coupling.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/coupling_functions.py` — NOT invoked by the run-book
    - `code/analysis/cross_validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/with_coupling.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
