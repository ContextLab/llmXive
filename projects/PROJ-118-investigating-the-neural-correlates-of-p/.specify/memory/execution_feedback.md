# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/performance_benchmark.py: self-declared fabricated metric — “…# we might need to create a dummy metrics file for the benchmark.…”
- code/performance_benchmark.py: synthetic/fake INPUT data not authorized by the spec — “…algorithm* by creating a synthetic small dataset         # from the real…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/performance_benchmark.py: self-declared fabricated metric — “…# we might need to create a dummy metrics file for the benchmark.…”; code/performance_benchmark.py: synthetic/fake INPUT data not authorized by the spec — “…algorithm* by creating a synthetic small dataset         # from the real…”; 6 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/extract.py (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1
stigating-the-neural-correlates-of-p/code/download.py", line 218, in main
    download_openneuro_dataset(dataset_id, raw_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 209, in download_openneuro_dataset
    run_download_pipeline(dataset_id, raw_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 148, in run_download_pipeline
    extract_archive(archive_path, target_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 111, in extract_archive
    shutil.unpack_archive(str(archive_path), str(dest_dir))
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/shutil.py", line 1337, in unpack_archive
    func(filename, extract_dir, **kwargs)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/shutil.py", line 1242, in _unpack_zipfile
    raise ReadError("%s is not a zip file" % filename)
shutil.ReadError: /home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/data/raw/ds003645.zip is not a zip file

- python code/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/preprocess.py", line 89, in <module>
    @log_execution_time()
     ^^^^^^^^^^^^^^^^^^^^
TypeError: log_execution_time() missing 1 required positional argument: 'func'

- python code/extract.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/extract.py", line 46, in <module>
    @log_execution_time()
     ^^^^^^^^^^^^^^^^^^^^
TypeError: log_execution_time() missing 1 required positional argument: 'func'

- python code/stats.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/stats.py", line 34, in <module>
    @log_execution_time()
     ^^^^^^^^^^^^^^^^^^^^
TypeError: log_execution_time() missing 1 required positional argument: 'func'

- python code/viz.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/viz.py", line 17, in <module>
    from extract import load_epochs, get_subject_epochs_paths
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/extract.py", line 46, in <module>
    @log_execution_time()
     ^^^^^^^^^^^^^^^^^^^^
TypeError: log_execution_time() missing 1 required positional argument: 'func'

- python -m pytest tests/ -> rc=2
mary info ============================
ERROR tests/integration/test_preprocess.py - TypeError: log_execution_time() ...
ERROR tests/integration/test_preprocess_epoching_integration.py - TypeError: ...
ERROR tests/integration/test_preprocess_integration.py - TypeError: log_execu...
ERROR tests/integration/test_viz.py - TypeError: log_execution_time() missing...
ERROR tests/unit/test_analyze_rejection.py - NameError: name 'Optional' is no...
ERROR tests/unit/test_download.py
ERROR tests/unit/test_edge_cases.py - TypeError: log_execution_time() missing...
ERROR tests/unit/test_extract.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_performance_benchmark.py - TypeError: log_execution_tim...
ERROR tests/unit/test_performance_monitor.py - TypeError: log_execution_time(...
ERROR tests/unit/test_preprocess.py - TypeError: log_execution_time() missing...
ERROR tests/unit/test_preprocess_epoching.py - TypeError: log_execution_time(...
ERROR tests/unit/test_stats_filtering.py - TypeError: log_execution_time() mi...
!!!!!!!!!!!!!!!!!!! Interrupted: 14 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 14 errors in 1.91s ========================


