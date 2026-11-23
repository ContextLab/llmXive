# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/neural_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…ry pressure is detected (simulated by corpus size or explicit flag),…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/neural_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…ry pressure is detected (simulated by corpus size or explicit flag),…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python -m pytest tests/ (rc=2); 9 declared deliverable(s) absent: data/processed/features.csv; data/processed/fixed_vocab.json; data/processed/graphs.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
ule '/home/runner/work/llmXive/llmXive/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag/tests/unit/test_timing_logger.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_timing_logger.py:15: in <module>
    from code.config import RESULTS_DIR
E   ImportError: cannot import name 'RESULTS_DIR' from '<unknown module name>' (unknown location)
=========================== short test summary info ============================
ERROR tests/integration/test_graph_pipeline.py
ERROR tests/integration/test_statistical_validation.py - FileNotFoundError: [...
ERROR tests/integration/test_t_test_integration.py - FileNotFoundError: [Errn...
ERROR tests/unit/test_schema_validation.py
ERROR tests/unit/test_t_test_metrics.py
ERROR tests/unit/test_timing_logger.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 skipped, 6 errors in 2.25s =========================



## Declared deliverables still missing

- data/processed/features.csv
- data/processed/fixed_vocab.json
- data/processed/graphs.json
- data/raw/sampled_corpus.parquet
- data/results/correlation.csv
- data/results/retrieval_scores.csv
- data/results/retrieved_features.csv
- data/results/ttest_results.json
- data/results/validation_status.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleanup_refactor.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/pipeline_writer.py` — NOT invoked by the run-book
    - `code/refactored_utils.py` — NOT invoked by the run-book
    - `code/retrieval_sim.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t_test_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/fixed_vocab.json` is declared but was NOT written. Scripts referencing it:
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/vocabulary_builder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fixed_vocab.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/graphs.json` is declared but was NOT written. Scripts referencing it:
    - `code/cleanup_refactor.py` — NOT invoked by the run-book
    - `code/data_loader.py` — IS a run-book command
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/pipeline_writer.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/topology_extractor.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/graphs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/sampled_corpus.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/sampled_corpus.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleanup_refactor.py` — NOT invoked by the run-book
    - `code/final_metrics_writer.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/validate_success_criteria.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/retrieval_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/retrieval_sim.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t_test_metrics.py` — NOT invoked by the run-book
    - `code/topology_extractor.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/retrieval_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/retrieved_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t_test_metrics.py` — NOT invoked by the run-book
    - `code/topology_extractor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/retrieved_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/ttest_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ttest_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/validation_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/validation_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
