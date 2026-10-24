# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data_pipeline.py --sample-size 800 --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/runtime_validator.py: synthetic/fake INPUT data not authorized by the spec — “…> list:     """Generates mock data for a dry run."""     re…”; 3 command(s) failed: python code/data_pipeline.py --sample-size 800 --seed 42 (rc=1); python code/statistical_analysis.py (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python code/data_pipeline.py --sample-size 800 --seed 42 -> rc=1
aceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 325, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 310, in main
    df = run_pipeline(
         ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 248, in run_pipeline
    sampled_functions = load_sampled_functions_stratified(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 179, in load_sampled_functions_stratified
    verify_dataset_source(dataset_id)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/data_pipeline.py", line 50, in verify_dataset_source
    raise ConnectionError(error_msg)
ConnectionError: Dataset code-search-net/python is unreachable: Dataset 'code-search-net/python' doesn't exist on the Hub or cannot be accessed.

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
(name[level:], package, level)
tests/unit/test_statistical_analysis.py:9: in <module>
    from code.statistical_analysis import (
E   ImportError: cannot import name 'generate_sensitivity_report' from 'code.statistical_analysis' (/home/runner/work/llmXive/llmXive/projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/statistical_analysis.py)
______________ ERROR collecting tests/unit/test_verify_dataset.py ______________
tests/unit/test_verify_dataset.py:13: in <module>
    from code.verify_dataset import (
code/verify_dataset.py:30: in <module>
    TEST_SHARD_FILE = get_data_path("raw", "test_shard.jsonl")
E   TypeError: get_data_path() takes 1 positional argument but 2 were given
=========================== short test summary info ============================
ERROR tests/unit/test_config.py
ERROR tests/unit/test_data_pipeline_stratified.py
ERROR tests/unit/test_quickstart_validation.py
ERROR tests/unit/test_statistical_analysis.py
ERROR tests/unit/test_verify_dataset.py - TypeError: get_data_path() takes 1 ...
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 4.54s ===============================


