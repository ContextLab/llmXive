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
82067f35f7ebb0ec9fe084ca7799a8bd651d884e1e1b772 .gitkeep\n
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 413, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 406, in main
    download_openneuro_dataset(dataset_id, raw_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 341, in download_openneuro_dataset
    verify_all_checksums(output_dir, manifest)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/download.py", line 272, in verify_all_checksums
    raise RuntimeError(
RuntimeError: Checksum verification failed for 1 file(s):\nChecksum verification failed – file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/data/raw/checksums.txt\n2d18614d05c4e1c55346ca45137baac22abb0af630d5cba1bc5b9d1e09b164e5 ds003645.zip\n0ce0d0ae585f6d34f82067f35f7ebb0ec9fe084ca7799a8bd651d884e1e1b772 .gitkeep\n

- python code/preprocess.py -> rc=1
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/cleanup_utils.py", line 135, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/preprocess.py", line 405, in run_preprocessing_pipeline
    ensure_directory(output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/config_loader.py", line 105, in ensure_directory
    path = get_path(path_key)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/config_loader.py", line 91, in get_path
    raise ValueError(f"Unknown path key: {key}. Available keys: {list(path_map.keys())}")
ValueError: Unknown path key: /home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/data/processed. Available keys: ['raw_data', 'processed_data', 'results', 'code', 'tests', 'figures', 'config', 'metrics', 'stats', 'rejected_log']

- python code/extract.py -> rc=1

2026-10-14 20:32:27,876 - ERROR - No epoch files found.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/extract.py", line 395, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/extract.py", line 391, in main
    metrics_path = run_extraction_pipeline(str(epochs_dir), str(output_dir))
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/cleanup_utils.py", line 123, in wrapper
    result = real_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/extract.py", line 344, in run_extraction_pipeline
    raise FileNotFoundError("No epoch files found.")
FileNotFoundError: No epoch files found.

- python code/stats.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/stats.py", line 210, in <module>
    epochs: mne.Epochs,
            ^^^
NameError: name 'mne' is not defined

- python code/viz.py -> rc=1
File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/viz.py", line 282, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/viz.py", line 279, in main
    run_viz_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/viz.py", line 246, in run_viz_pipeline
    ensure_directory(plots_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/config_loader.py", line 105, in ensure_directory
    path = get_path(path_key)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/code/config_loader.py", line 91, in get_path
    raise ValueError(f"Unknown path key: {key}. Available keys: {list(path_map.keys())}")
ValueError: Unknown path key: /home/runner/work/llmXive/llmXive/projects/PROJ-118-investigating-the-neural-correlates-of-p/results/plots. Available keys: ['raw_data', 'processed_data', 'results', 'code', 'tests', 'figures', 'config', 'metrics', 'stats', 'rejected_log']

- python -m pytest tests/ -> rc=2
nit__.py:1448
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/config/__init__.py:1448: PytestConfigWarning: Unknown config option: timeout_method
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_preprocess.py
ERROR tests/integration/test_preprocess_integration.py
ERROR tests/unit/test_analyze_rejection.py - NameError: name 'Optional' is no...
ERROR tests/unit/test_download.py
ERROR tests/unit/test_edge_cases.py - NameError: name 'mne' is not defined
ERROR tests/unit/test_extract.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_performance_benchmark.py - NameError: name 'mne' is not...
ERROR tests/unit/test_performance_monitor.py - NameError: name 'mne' is not d...
ERROR tests/unit/test_preprocess_epoching.py
ERROR tests/unit/test_stats_filtering.py - NameError: name 'mne' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 2 warnings, 11 errors in 1.89s ========================


