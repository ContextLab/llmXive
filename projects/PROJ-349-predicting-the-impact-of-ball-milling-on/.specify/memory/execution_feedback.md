# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/audit_report_T048.md: synthetic/fake INPUT data not authorized by the spec — “…No synthetic fallbacks, mock data generators, or random da…”
- code/scripts/real_data_audit.py: synthetic/fake INPUT data not authorized by the spec — “…ited patterns that would generate synthetic data (e.g., `generate_sy…”
- code/scripts/real_data_audit.py: synthetic/fake INPUT data not authorized by the spec — “…# Patterns that indicate synthetic data generation or mocking PR…”
- code/src/ingest/stream_uci_fallback.py: synthetic/fake INPUT data not authorized by the spec — “…domain match. # We will generate synthetic-like but REAL-derived ro…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/arxiv_tables.json, data/raw/nist_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/audit_report_T048.md: synthetic/fake INPUT data not authorized by the spec — “…No synthetic fallbacks, mock data generators, or random da…”; code/scripts/real_data_audit.py: synthetic/fake INPUT data not authorized by the spec — “…ited patterns that would generate synthetic data (e.g., `generate_sy…”; code/scripts/real_data_audit.py: synthetic/fake INPUT data not authorized by the spec — “…# Patterns that indicate synthetic data generation or mocking PR…”; every produced artifact is gitignored (data/raw/arxiv_tables.json, data/raw/nist_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 9 command(s) failed: python -m src.preprocess.pipeline (rc=1); python -m src.model.train_gpr # may be skipped automatically (rc=1); python -m src.model.train_rf (rc=1)

## Failing / missing run-book commands

- python -m src.preprocess.pipeline -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/src/preprocess/pipeline.py", line 16, in <module>
    from sklearn.impute import IterativeImputer
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/sklearn/impute/__init__.py", line 19, in __getattr__
    raise ImportError(
ImportError: IterativeImputer is experimental and the API might change without any deprecation cycle. To use it, you need to explicitly import enable_iterative_imputer:
from sklearn.experimental import enable_iterative_imputer

- python -m src.model.train_gpr # may be skipped automatically -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.model.train_gpr

- python -m src.model.train_rf -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.model.train_rf

- python -m src.model.baseline_lr -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.model.baseline_lr

- python -m src.evaluate.metrics -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.evaluate.metrics

- python -m src.interpret.partial_dependence -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.interpret.partial_dependence

- python -m src.interpret.feature_importance -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.interpret.feature_importance

- python -m src.utils.generate_report # creates results/summary.txt and figures -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-349-predicting-the-impact-of-ball-milling-on/bin/python: No module named src.utils.generate_report

- python -m pytest -q tests/contract/test_dataset_schema.py -> rc=1
ontract/test_dataset_schema.py E...                               [100%]

==================================== ERRORS ====================================
_______________ ERROR at setup of test_schema_validation_passes ________________
file /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/tests/contract/test_dataset_schema.py, line 23
  def test_schema_validation_passes(df):
E       fixture 'df' not found
>       available fixtures: cache, capfd, capfdbinary, caplog, capsys, capsysbinary, doctest_namespace, monkeypatch, platformdirs_isolated, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, sample_experiment, tmp_data_dir, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory
>       use 'pytest --fixtures [testpath]' for help on them.

/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/tests/contract/test_dataset_schema.py:23
=========================== short test summary info ============================
ERROR tests/contract/test_dataset_schema.py::test_schema_validation_passes
========================== 3 passed, 1 error in 0.31s ==========================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
