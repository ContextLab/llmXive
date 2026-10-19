# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/adult/holdout.parquet, data/processed/adult/train.parquet, data/raw/adult/raw.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/adult/holdout.parquet, data/processed/adult/train.parquet, data/raw/adult/raw.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python -m src.cli.run_fidelity --smoke (rc=1); python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity --smoke -> rc=1
oad_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/__init__.py", line 17, in <module>
    from sdv import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/data_processing/__init__.py", line 3, in <module>
    from sdv.data_processing.data_processor import DataProcessor
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/sdv/data_processing/data_processor.py", line 12, in <module>
    from rdt.transformers import AnonymizedFaker, IDGenerator, get_default_transformers
ImportError: cannot import name 'IDGenerator' from 'rdt.transformers' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-187-evaluating-the-statistical-properties-of/lib/python3.11/site-packages/rdt/transformers/__init__.py)

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def schema():
        if not SCHEMA_YAML.is_file():
>           pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
E           Failed: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-statistical-fidelity/contracts/metric_results.schema.yaml

tests/contract/test_metric_schema.py:39: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.19s


