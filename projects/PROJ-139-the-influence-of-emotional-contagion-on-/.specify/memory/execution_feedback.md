# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…ny fallback to synthetic/mock data. If all real sources fai…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…ny fallback to synthetic/mock data. If all real sources fai…”; 2 command(s) failed: python code/data/download.py --source askScience --source fdr (rc=1); python code/analysis/run_pipeline.py (rc=1); 9 declared deliverable(s) absent: data/processed/all_threads_classified.csv; data/processed/collinearity_diagnostics.json; data/processed/external_validation_correlation.csv

## Failing / missing run-book commands

- python code/data/download.py --source askScience --source fdr -> rc=1
    INFO:__main__:Directories ensured.
INFO:__main__:Processing subreddit: fdr
INFO:__main__:Attempting Pushshift API: https://api.pushshift.io/reddit/search/subreddit/fdr
WARNING:__main__:Pushshift failed with status 404.
WARNING:__main__:Reddit API credentials not found in config. Skipping Reddit API.
WARNING:__main__:Internet Archive fallback is not fully implemented for Reddit data.
ERROR:__main__:CRITICAL FAILURE: Could not retrieve any data for subreddit 'fdr' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.
ERROR:__main__:CRITICAL FAILURE: Could not retrieve any data for subreddit 'fdr' from Pushshift, Reddit API, or Internet Archive. The pipeline cannot proceed without real data. Please check network connectivity, API credentials, or source availability.
- python code/analysis/run_pipeline.py -> rc=1
    object has no attribute 'state_dir' ---
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/analysis/run_pipeline.py", line 126, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/analysis/run_pipeline.py", line 123, in main
    run_full_pipeline(args)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/analysis/run_pipeline.py", line 92, in run_full_pipeline
    run_stage("Data Extraction", extract_main)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/analysis/run_pipeline.py", line 45, in run_stage
    func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/extract.py", line 298, in main
    ensure_directories()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-139-the-influence-of-emotional-contagion-on-/code/data/extract.py", line 23, in ensure_directories
    config.state_dir
AttributeError: 'Config' object has no attribute 'state_dir'

## Declared deliverables still missing

- data/processed/all_threads_classified.csv
- data/processed/collinearity_diagnostics.json
- data/processed/external_validation_correlation.csv
- data/processed/ground_truth_stats.json
- data/processed/sensitivity_analysis.csv
- data/processed/thread_metrics.csv
- data/processed/threads_with_seeds.csv
- data/processed/vader_validation_report.json
- data/processed/valid_threads.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/config/settings.py`) — accessed via method/attribute names this round: `state_dir`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config/settings.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.state_dir` call sites (0):

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/all_threads_classified.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/update_analysis_summary.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/all_threads_classified.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_collinearity_heatmap.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/collinearity_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/external_validation_correlation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/generate_report.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_modeling_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline_execution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/external_validation_correlation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_ground_truth_coverage.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/tests/test_validate_ground_truth_coverage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_sensitivity_grid.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/tests/test_modeling.py` — NOT invoked by the run-book
    - `code/tests/test_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/thread_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_reports.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/sampling.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_generate_final_reports.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_decision_quality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/thread_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threads_with_seeds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/extract.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
    - `code/tests/test_extract.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_metrics_data_flow.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threads_with_seeds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vader_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/sentiment_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vader_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_threads.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/analyze_sampling_power.py` — NOT invoked by the run-book
    - `code/analysis/validate_ground_truth_coverage.py` — NOT invoked by the run-book
    - `code/analysis/final_validation.py` — NOT invoked by the run-book
    - `code/data/sentiment.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/annotate_corpus.py` — NOT invoked by the run-book
    - `code/data/modeling.py` — NOT invoked by the run-book
    - `code/tests/test_extract.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_threads.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
