# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data_pipeline.py --sample-size --seed 42`
  - script usage: `data_pipeline.py [-h] [--sample-size SAMPLE_SIZE] [--seed SEED]`
  - argparse error: `data_pipeline.py: error: argument --sample-size: expected one argument`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”; 3 command(s) failed: python code/data_pipeline.py --sample-size --seed 42 (rc=2); python code/statistical_analysis.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python code/data_pipeline.py --sample-size --seed 42 -> rc=2

usage: data_pipeline.py [-h] [--sample-size SAMPLE_SIZE] [--seed SEED]
                        [--dataset DATASET]
data_pipeline.py: error: argument --sample-size: expected one argument

- python code/statistical_analysis.py -> rc=1
-271-evaluating-the-effectiveness-of-llms-for/data/static_baseline.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py", line 392, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py", line 370, in main
    results = run_statistical_analysis()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py", line 303, in run_statistical_analysis
    static_df = load_static_baseline(static_baseline_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py", line 26, in load_static_baseline
    raise FileNotFoundError(f"Static baseline file not found: {filepath}")
FileNotFoundError: Static baseline file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/data/static_baseline.csv

- python -m pytest tests/ -> rc=2
test_statistical_analysis.py ___________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/tests/unit/test_statistical_analysis.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_statistical_analysis.py:9: in <module>
    from code.statistical_analysis import (
E   ImportError: cannot import name 'generate_sensitivity_report' from 'code.statistical_analysis' (/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py)
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_data_pipeline_stratified.py
ERROR tests/unit/test_quickstart_validation.py
ERROR tests/unit/test_statistical_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 4 errors in 3.58s ===============================


