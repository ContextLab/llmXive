# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”
- code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate deterministic synthetic solar‑wind and geomagnet…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m code.ingestion.download_real --start 2000-01-01 --end 2020-12-31`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/download_ace.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     run_ingestion(confi…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for ACE and NO…”; code/ingestion/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a deterministic synthetic solar‑wind / geomagnetic…”; 4 command(s) failed: python -m code.main (rc=1); python -m pytest tests/ (rc=2); python -m code.ingestion.download_real --start 2000-01-01 --end 2020-12-31 (rc=1); 5 declared deliverable(s) absent: data/artifacts/alignment_report.json; data/artifacts/cv_metrics.json; data/artifacts/delta_r2.json

## Failing / missing run-book commands

- python -m code.main -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 14, in <module>
    from code.analysis.coupling_functions import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/analysis/coupling_functions.py", line 49, in <module>
    V: Union[pd.Series, pd.DataFrame],
       ^^^^^
NameError: name 'Union' is not defined

- python -m pytest tests/ -> rc=2
OR collecting projects/PROJ-505-exploring-the-statistical-relationship-b/tests/unit/test_regression.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/tests/unit/test_regression.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_regression.py:14: in <module>
    from analysis.regression import (
E   ImportError: cannot import name '_check_multicollinearity' from 'analysis.regression' (/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/analysis/regression.py)
=========================== short test summary info ============================
ERROR tests/unit/test_coupling.py - NameError: name 'Union' is not defined
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_regression.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.47s ===============================


- python -m code.ingestion.download_real --start 2000-01-01 --end 2020-12-31 -> rc=1
 "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 208, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 203, in main
    summary = download_and_preserve(start=args.start, end=args.end)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 139, in download_and_preserve
    omni_files = _fetch_cdf_files("omni_h0", "OMNI hourly", trange)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion/download_real.py", line 70, in _fetch_cdf_files
    raise ConnectionError(
ConnectionError: Failed to fetch OMNI hourly from CDAWeb via pyspedas: pyspedas stub: real data download not implemented in this test environment.

- python -m code.main --quick  # uses only the initial segment of rows. -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/main.py", line 14, in <module>
    from code.analysis.coupling_functions import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-505-exploring-the-statistical-relationship-b/code/analysis/coupling_functions.py", line 49, in <module>
    V: Union[pd.Series, pd.DataFrame],
       ^^^^^
NameError: name 'Union' is not defined


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
