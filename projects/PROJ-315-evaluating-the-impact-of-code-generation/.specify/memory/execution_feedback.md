# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/stats.py: synthetic/fake INPUT data not authorized by the spec — “…metrics.csv')          # Mock data for demonstration of str…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/stats.py: synthetic/fake INPUT data not authorized by the spec — “…metrics.csv')          # Mock data for demonstration of str…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/viz.py; 5 command(s) failed: python code/data/preprocess.py (rc=1); python code/analysis/stats.py (rc=1); python -m pytest code/tests/test_classify.py (rc=4); 1 declared deliverable(s) absent: data/processed/classified_prs.parquet

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1
[2026-10-10T02:27:51.250587] [INFO] __main__: Starting audit accuracy pipeline. Input: docs/reports/audit_sample_labeled.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/data/preprocess.py", line 148, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/data/preprocess.py", line 145, in main
    run_audit_accuracy_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/data/preprocess.py", line 127, in run_audit_accuracy_pipeline
    df = load_human_labeled_sample(input_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/data/preprocess.py", line 38, in load_human_labeled_sample
    raise ValueError(f"Missing required columns in human labeled sample: {missing_cols}")
ValueError: Missing required columns in human labeled sample: ['commit_message', 'heuristic_label']

- python code/analysis/stats.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/analysis/stats.py", line 5, in <module>
    from scipy.stats import mannwhitneyu, power_analysis
ImportError: cannot import name 'power_analysis' from 'scipy.stats' (/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/.venv/lib/python3.11/site-packages/scipy/stats/__init__.py)

- python code/analysis/viz.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation/code/analysis/viz.py': [Errno 2] No such file or directory

- python -m pytest code/tests/test_classify.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation
configfile: pyproject.toml
plugins: platformdirs-4.12.4, anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_classify.py


- python -m pytest code/tests/test_stats.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation
configfile: pyproject.toml
plugins: platformdirs-4.12.4, anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_stats.py


- python -m pytest code/tests/test_pipeline.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-315-evaluating-the-impact-of-code-generation
configfile: pyproject.toml
plugins: platformdirs-4.12.4, anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: code/tests/test_pipeline.py



## Declared deliverables still missing

- data/processed/classified_prs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/classified_prs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_audit_sample.py` — NOT invoked by the run-book
    - `code/labeling/classify.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/classified_prs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
