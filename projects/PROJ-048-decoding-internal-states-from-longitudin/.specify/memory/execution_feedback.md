# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/alignment.py: synthetic/fake INPUT data not authorized by the spec — “…that here, we will     # generate a synthetic ground truth for the sak…”
- code/analysis/null_model.py: synthetic/fake INPUT data not authorized by the spec — “…n_behaviors))          # Generate synthetic neural activity: X_null…”
- code/analysis/null_model.py: synthetic/fake INPUT data not authorized by the spec — “…null model")          # Generate null model synthetic activity     synthetic_a…”
- code/analysis/null_model.py: synthetic/fake INPUT data not authorized by the spec — “…demonstration, we'll use synthetic data if not found)         #…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…# Example usage with synthetic data (for demonstration)…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…= 30.0  # Hz          # Generate synthetic traces     np.random.see…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…ask] = np.nan          # Generate synthetic behavior data     behavi…”
- code/data/preprocess_stub.py: synthetic/fake INPUT data not authorized by the spec — “…# Example usage with mock data     np.random.seed(42)…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/alignment.py: synthetic/fake INPUT data not authorized by the spec — “…that here, we will     # generate a synthetic ground truth for the sak…”; code/analysis/null_model.py: synthetic/fake INPUT data not authorized by the spec — “…n_behaviors))          # Generate synthetic neural activity: X_null…”; code/analysis/null_model.py: synthetic/fake INPUT data not authorized by the spec — “…null model")          # Generate null model synthetic activity     synthetic_a…”; 5 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/analysis/nmf_engine.py --k 10 20 30 (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
{"timestamp": "2026-10-10T07:25:37.269910Z", "level": "INFO", "logger": "download", "message": "Starting download from https://allen-brain-atlas-data.s3.amazonaws.com/visual-coding/sample_subset.h5", "module": "download", "function": "download_allen_data", "line": 78}
{"timestamp": "2026-10-10T07:25:37.401423Z", "level": "INFO", "logger": "download", "message": "Estimated dataset size: 0.00 GB (Limit: 5.0 GB)", "module": "download", "function": "download_allen_data", "line": 85}
Download Error: Download failed: 404 Client Error: Not Found for url: https://allen-brain-atlas-data.s3.amazonaws.com/visual-coding/sample_subset.h5

WARNING:root:Could not fetch Content-Length for https://allen-brain-atlas-data.s3.amazonaws.com/visual-coding/sample_subset.h5: 404 Client Error: Not Found for url: https://allen-brain-atlas-data.s3.amazonaws.com/visual-coding/sample_subset.h5
INFO:download:Estimated dataset size: 0.00 GB (Limit: 5.0 GB)

- python code/data/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/data/preprocess.py", line 377, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/data/preprocess.py", line 331, in main
    log_stage_start(logger, "main")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/utils/logger.py", line 77, in log_stage_start
    extra = {"extra_data": {"stage": stage, "event": "start"} | (details or {})}
                           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~
TypeError: unsupported operand type(s) for |: 'dict' and 'str'

- python code/analysis/nmf_engine.py --k 10 20 30 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/analysis/nmf_engine.py", line 11, in <module>
    from data.loader import load_chunked_hdf5, LoaderError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/data/loader.py", line 4, in <module>
    import h5py
ModuleNotFoundError: No module named 'h5py'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/analysis/nmf_engine.py", line 17, in <module>
    from data.loader import load_chunked_hdf5, LoaderError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/data/loader.py", line 4, in <module>
    import h5py
ModuleNotFoundError: No module named 'h5py'

- python code/analysis/stats.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/analysis/stats.py", line 244, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/code/analysis/stats.py", line 231, in main
    random_seed = get_config_value("RANDOM_SEED", 42)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_config_value() takes 1 positional argument but 2 were given

- python -m pytest tests/ -v -> rc=1
/tests/test_split.py:152: FutureWarning: 'H' is deprecated and will be removed in a future version, please use 'h' instead.
    'timestamp': pd.date_range('2023-01-01', periods=100, freq='H')

tests/test_split.py::TestSplitValidation::test_no_temporal_leakage
  /home/runner/work/llmXive/llmXive/projects/PROJ-048-decoding-internal-states-from-longitudin/tests/test_split.py:238: FutureWarning: 'H' is deprecated and will be removed in a future version, please use 'h' instead.
    timestamps = pd.date_range('2023-01-01', periods=100, freq='H')

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_split.py::TestTimeBasedSplitter::test_split_arrays - assert...
FAILED tests/test_split.py::TestRunSplit::test_run_split_csv - TypeError: log...
FAILED tests/test_split.py::TestRunSplit::test_run_split_with_time_column - T...
FAILED tests/test_split.py::TestRunSplit::test_run_split_nonexistent_file - T...
FAILED tests/test_split.py::TestSplitValidation::test_split_metadata_contains_validation_info
=================== 5 failed, 9 passed, 4 warnings in 0.26s ====================


