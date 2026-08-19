# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/audit_report_T048.md: synthetic/fake INPUT data not authorized by the spec — “…No synthetic fallbacks, mock data generators, or random da…”
- code/src/ingest/stream_uci_fallback.py: synthetic/fake INPUT data not authorized by the spec — “…domain match. # We will generate synthetic-like but REAL-derived ro…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/audit_report_T048.md: synthetic/fake INPUT data not authorized by the spec — “…No synthetic fallbacks, mock data generators, or random da…”; code/src/ingest/stream_uci_fallback.py: synthetic/fake INPUT data not authorized by the spec — “…domain match. # We will generate synthetic-like but REAL-derived ro…”; 9 command(s) failed: python -m src.ingest.arxiv_extractor (rc=1); python -m src.preprocess.pipeline (rc=1); python -m src.model.train_gpr # may be skipped automatically (rc=1)

## Failing / missing run-book commands

- python -m src.ingest.arxiv_extractor -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/src/ingest/arxiv_extractor.py", line 20, in <module>
    from pdfminer.layout import LAParams, LTTable, LTText
ImportError: cannot import name 'LTTable' from 'pdfminer.layout' (/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/lib/python3.11/site-packages/pdfminer/layout.py)
- python -m src.preprocess.pipeline -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/src/preprocess/pipeline.py", line 16, in <module>
    from sklearn.impute import IterativeImputer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/lib/python3.11/site-packages/sklearn/impute/__init__.py", line 19, in __getattr__
    raise ImportError(
ImportError: IterativeImputer is experimental and the API might change without any deprecation cycle. To use it, you need to explicitly import enable_iterative_imputer:
from sklearn.experimental import enable_iterative_imputer
- python -m src.model.train_gpr # may be skipped automatically -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.model.train_gpr
- python -m src.model.train_rf -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.model.train_rf
- python -m src.model.baseline_lr -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.model.baseline_lr
- python -m src.evaluate.metrics -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.evaluate.metrics
- python -m src.interpret.partial_dependence -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.interpret.partial_dependence
- python -m src.interpret.feature_importance -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.interpret.feature_importance
- python -m src.utils.generate_report # creates results/summary.txt and figures -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-349-predicting-the-impact-of-ball-milling-on/code/.venv/bin/python: No module named src.utils.generate_report
