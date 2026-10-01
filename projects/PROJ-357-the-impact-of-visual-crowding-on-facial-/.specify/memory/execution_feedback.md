# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…ading and validating raw synthetic judgment data.     """     logging.bas…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Unit-test helper to generate a small synthetic pilot dataset.  This scr…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…2 ) -> None:     """     Generate a small synthetic pilot dataset for unit t…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic pilot sample: {n_participants} partic…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate a small synthetic pilot dataset for unit t…”
- code/analysis/reporting.py: synthetic/fake INPUT data not authorized by the spec — “…the analysis (even with synthetic pilot data)     - Potential unmeasu…”
- code/analysis/reporting.py: synthetic/fake INPUT data not authorized by the spec — “…uracy. The analysis uses synthetic pilot data generated",         "to…”
- code/analysis/reporting.py: synthetic/fake INPUT data not authorized by the spec — “…"-" * 70,         "  - Synthetic data limitations: While stati…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…ading and validating raw synthetic judgment data.     """     logging.bas…”; code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Unit-test helper to generate a small synthetic pilot dataset.  This scr…”; code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…2 ) -> None:     """     Generate a small synthetic pilot dataset for unit t…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/run_full_pipeline.py; 9 command(s) failed: python code/utils/download.py (rc=1); python code/utils/frame_extractor.py (rc=1); python code/utils/stimulus_gen.py (rc=1); 3 declared deliverable(s) absent: data/processed/clutter_metrics.csv; data/processed/regression_results.json; data/processed/validation_report.json

## Failing / missing run-book commands

- python code/run_full_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/run_full_pipeline.py': [Errno 2] No such file or directory
- python code/utils/download.py -> rc=1
    ERROR: The 'datasets' library is required. Install with: pip install datasets
- python code/utils/frame_extractor.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/frame_extractor.py", line 23, in <module>
    logging.FileHandler('data/raw/frame_extraction.log')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/data/raw/frame_extraction.log'
- python code/utils/stimulus_gen.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/stimulus_gen.py", line 23, in <module>
    from utils.frame_extractor import extract_frames_from_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/frame_extractor.py", line 23, in <module>
    logging.FileHandler('data/raw/frame_extraction.log')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/data/raw/frame_extraction.log'
- python code/utils/manifest_validator.py -> rc=1
    2026-10-01 19:21:46,310 - INFO - Loading manifest from data/interim/stimuli_manifest.json
2026-10-01 19:21:46,310 - WARNING - Error log not found at data/interim/generation_errors.log
2026-10-01 19:21:46,310 - INFO - Scanning stimuli directory: data/interim/stimuli
2026-10-01 19:21:46,310 - ERROR - Error during validation: Stimuli directory not found: data/interim/stimuli
- python code/utils/clutter_metrics.py -> rc=1
    2026-10-01 19:21:46,379 - INFO - Starting clutter metrics computation
2026-10-01 19:21:46,379 - ERROR - Error during clutter metrics computation: 'str' object has no attribute 'get'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/clutter_metrics.py", line 420, in main
    results = compute_clutter_metrics()
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/clutter_metrics.py", line 229, in compute_clutter_metrics
    stimuli_files = [entry for entry in manifest if entry.get('status') == 'success']
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/clutter_metrics.py", line 229, in <listcomp>
    stimuli_files = [entry for entry in manifest if entry.get('status') == 'success']
                                                    ^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'
- python code/analysis/pilot_runner.py -> rc=1
    2026-10-01 19:21:46,417 - __main__ - INFO - Starting synthetic pilot with 10 participants
2026-10-01 19:21:46,417 - __main__ - INFO - Loading manifest from data/interim/stimuli_manifest.json
2026-10-01 19:21:46,417 - __main__ - INFO - Loaded 0 stimuli
2026-10-01 19:21:46,417 - __main__ - ERROR - Pilot run failed: Manifest contains no stimuli to process
- python code/analysis/aggregate_judgments.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/aggregate_judgments.py", line 134, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/aggregate_judgments.py", line 97, in main
    set_all_seeds(args.seed)
    ^^^^^^^^^^^^^
NameError: name 'set_all_seeds' is not defined
- python code/analysis/glmm_model.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/glmm_model.py", line 10, in <module>
    import statsmodels.api as sm
ModuleNotFoundError: No module named 'statsmodels'
- python code/analysis/reporting.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/reporting.py", line 17, in <module>
    from analysis.glmm_model import load_prepared_data, extract_results, apply_fdr_correction
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/glmm_model.py", line 10, in <module>
    import statsmodels.api as sm
ModuleNotFoundError: No module named 'statsmodels'

## Declared deliverables still missing

- data/processed/clutter_metrics.csv
- data/processed/regression_results.json
- data/processed/validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clutter_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/clutter_metrics.py` — IS a run-book command
    - `code/analysis/glmm_model.py` — IS a run-book command
    - `code/analysis/validation_report.py` — NOT invoked by the run-book
    - `code/analysis/write_model_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clutter_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/glmm_model.py` — IS a run-book command
    - `code/analysis/write_regression_results.py` — NOT invoked by the run-book
    - `code/analysis/reporting.py` — IS a run-book command
    - `code/analysis/write_model_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/clutter_metrics.py` — IS a run-book command
    - `code/utils/manifest_validator.py` — IS a run-book command
    - `code/analysis/validation_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
