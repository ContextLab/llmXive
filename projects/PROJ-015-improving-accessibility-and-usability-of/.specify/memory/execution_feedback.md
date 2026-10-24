# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/data_cleaner.py: synthetic/fake INPUT data not authorized by the spec — “…line to run even if only simulated data is present. "…”
- code/analysis/run_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…b: Entry gate to prevent simulated data bypass in full mode.…”
- code/analysis/run_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…store_true", help="Allow simulated data.")          args = parse…”
- code/simulator/simulator.py: synthetic/fake INPUT data not authorized by the spec — “…y]]:         """         Generate N synthetic sessions.          Logic…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/data_cleaner.py: synthetic/fake INPUT data not authorized by the spec — “…line to run even if only simulated data is present. "…”; code/analysis/run_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…b: Entry gate to prevent simulated data bypass in full mode.…”; code/analysis/run_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…store_true", help="Allow simulated data.")          args = parse…”; 2 command(s) failed: python -m code.analysis.run_analysis --mode pilot (rc=1); python -m pytest tests/ -v (rc=2); 4 declared deliverable(s) absent: data/processed/metrics_summary.csv; figures/completion_time.png; figures/error_count.png

## Failing / missing run-book commands

- python -m code.analysis.run_analysis --mode pilot -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 189, in _run_module_as_main
  File "<frozen runpy>", line 112, in _get_module_details
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-015-improving-accessibility-and-usability-of/code/analysis.py", line 23, in <module>
    from analysis.run_analysis import main as run_analysis_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-015-improving-accessibility-and-usability-of/code/analysis.py", line 23, in <module>
    from analysis.run_analysis import main as run_analysis_main
ModuleNotFoundError: No module named 'analysis.run_analysis'; 'analysis' is not a package

- python -m pytest tests/ -v -> rc=2
st_report_consistency.py
ERROR tests/unit/test_report_generator.py
ERROR tests/unit/test_run_analysis.py
ERROR tests/unit/test_run_analysis_precondition.py
ERROR tests/unit/test_sample_size_verification.py
ERROR tests/unit/test_session_logger.py - NameError: name 'Dict' is not defined
ERROR tests/unit/test_settings.py - NameError: name 'Dict' is not defined
ERROR tests/unit/test_simulator.py - NameError: name 'Dict' is not defined
ERROR tests/unit/test_stat_rigor.py
ERROR tests/unit/test_stat_utils.py
ERROR tests/unit/test_stats_engine.py
ERROR tests/unit/test_stats_engine_validation.py
ERROR tests/unit/test_sus_visualization.py
ERROR tests/unit/test_t026_metrics_summary.py
ERROR tests/unit/test_t108_precondition.py
ERROR tests/unit/test_validator.py
ERROR tests/unit/test_visualizations.py
ERROR tests/unit/test_visualizer.py
ERROR tests/unit/test_visualizer_completion_time.py
ERROR tests/unit/test_xai_wrapper.py - NameError: name 'Dict' is not defined
ERROR tests/utils/test_seed.py - NameError: name 'Dict' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 39 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 12 warnings, 39 errors in 2.74s ========================



## Declared deliverables still missing

- data/processed/metrics_summary.csv
- figures/completion_time.png
- figures/error_count.png
- figures/sus_score.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_cleaner.py` — NOT invoked by the run-book
    - `code/analysis/determinism_check.py` — NOT invoked by the run-book
    - `code/analysis/generate_metrics_summary.py` — NOT invoked by the run-book
    - `code/analysis/generate_power_report.py` — NOT invoked by the run-book
    - `code/analysis/power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/report_consistency_check.py` — NOT invoked by the run-book
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/run_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metrics_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/completion_time.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_cleaner.py` — NOT invoked by the run-book
    - `code/analysis/determinism_check.py` — NOT invoked by the run-book
    - `code/analysis/generate_metrics_summary.py` — NOT invoked by the run-book
    - `code/analysis/optimize_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/run_analysis.py` — IS a run-book command
    - `code/analysis/run_cleaning_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/run_notebook_validation.py` — NOT invoked by the run-book
    - `code/analysis/run_visualizations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/completion_time.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/error_count.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_cleaner.py` — NOT invoked by the run-book
    - `code/analysis/determinism_check.py` — NOT invoked by the run-book
    - `code/analysis/generate_metrics_summary.py` — NOT invoked by the run-book
    - `code/analysis/run_analysis.py` — IS a run-book command
    - `code/analysis/run_cleaning_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/run_notebook_validation.py` — NOT invoked by the run-book
    - `code/analysis/run_visualizations.py` — NOT invoked by the run-book
    - `code/analysis/stat_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/error_count.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/sus_score.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/clean_data.py` — NOT invoked by the run-book
    - `code/analysis/data_cleaner.py` — NOT invoked by the run-book
    - `code/analysis/determinism_check.py` — NOT invoked by the run-book
    - `code/analysis/generate_metrics_summary.py` — NOT invoked by the run-book
    - `code/analysis/run_analysis.py` — IS a run-book command
    - `code/analysis/run_cleaning_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/run_visualizations.py` — NOT invoked by the run-book
    - `code/analysis/stat_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/sus_score.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
