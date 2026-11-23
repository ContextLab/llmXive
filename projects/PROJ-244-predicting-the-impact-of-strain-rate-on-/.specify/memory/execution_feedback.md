# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…ate a physics‑consistent synthetic dataset for pipeline   validatio…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Simulated data generator # ------------…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic tensile‑test dataset wit…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> None:     """     Generate a synthetic dataset and write it to…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…bytes)     logger.info(f"Simulated dataset written to {output_path}…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…bytes)     logger.info(f"Simulated dataset also written to {raw_pat…”
- code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…``simulated`` creates a synthetic dataset for pipeline testing."…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/raw_input.csv, data/raw/simulated_tensile.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…ate a physics‑consistent synthetic dataset for pipeline   validatio…”; code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Simulated data generator # ------------…”; code/ingestion/fetchers.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic tensile‑test dataset wit…”; every produced artifact is gitignored (data/raw/raw_input.csv, data/raw/simulated_tensile.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 3 command(s) failed: python code/ingestion/fetchers.py --mode real (rc=-1); python -m pytest tests/contract/ -v (rc=2); python -m pytest tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/encoded_features.csv; data/processed/failure_regimes.csv; data/processed/test.csv

## Failing / missing run-book commands

- python code/ingestion/fetchers.py --mode real -> rc=-1

2026-10-22 01:37:08,491 INFO root: Starting [get] request for the URL https://www.openml.org/api/v1/xml/data/1234

[TIMEOUT after 120s]
- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-244-predicting-the-impact-of-strain-rate-on-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -v -> rc=2
/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_model_output_schema.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/contract/test_model_output_schema.py:13: in <module>
    from ingestion.preprocess import load_config
code/ingestion/preprocess.py:15: in <module>
    from ingestion.preprocess import (
E   ImportError: cannot import name 'load_raw_for_sensitivity' from partially initialized module 'ingestion.preprocess' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py)
=========================== short test summary info ============================
ERROR code/tests/contract/test_dataset_schema.py
ERROR code/tests/contract/test_model_output_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.89s ===============================


- python -m pytest tests/ -v -> rc=2
1868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_plots.py
ERROR tests/unit/test_sample_size_estimator.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 2 errors in 1.28s ========================



## Declared deliverables still missing

- data/processed/encoded_features.csv
- data/processed/failure_regimes.csv
- data/processed/test.csv
- data/processed/train.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/encoded_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/contract/test_dataset_schema.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/encoded_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/failure_regimes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
    - `code/visualization/failure_regimes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/failure_regimes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/fetchers.py` — IS a run-book command
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/evaluation.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
    - `code/reporting/compile_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/fetchers.py` — IS a run-book command
    - `code/ingestion/preprocess.py` — NOT invoked by the run-book
    - `code/modeling/empirical_models.py` — NOT invoked by the run-book
    - `code/modeling/evaluation.py` — NOT invoked by the run-book
    - `code/modeling/ml_models.py` — NOT invoked by the run-book
    - `code/modeling/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reporting/append_failure_regimes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
