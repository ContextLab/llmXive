# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/baseline_metrics.json; data/processed/cleaned_metrics.json; data/processed/null_fpr_metrics.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/main.py", line 14, in <module>
    from utils import setup_logging, pin_random_seed
ImportError: cannot import name 'pin_random_seed' from 'utils' (/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/utils.py)

## Declared deliverables still missing

- data/processed/baseline_metrics.json
- data/processed/cleaned_metrics.json
- data/processed/null_fpr_metrics.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_baseline_analysis` — defined in `code/analysis.py`; called 10 way(s):

- code/t023_reanalyze_cleaned_variants.py: metrics = run_baseline_analysis(
- code/t012_run_baseline_analysis.py: run_baseline_analysis()
- code/t013_record_baseline_metrics.py: run_baseline_analysis(str(raw_dir), str(output_file))
- code/analysis.py: 1. run_baseline_analysis(dataframe=df)
- code/analysis.py: 2. run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])
- code/analysis.py: 3. run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')
- code/analysis.py: 4. run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
- code/analysis.py: 5. run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)
- code/t033_outlier_threshold_sweep.py: return run_baseline_analysis(dataframe=df)
- code/t032_permutation_null_fpr.py: metrics = run_baseline_analysis(dataframe=df)

Make `run_baseline_analysis` in `code/analysis.py` accept ALL of the above.

### `setup_logging` — defined in `code/utils.py`; called 25 way(s):

- code/t036_pvalue_shift_reporting.py: logger = setup_logging(log_level="INFO")
- code/run_quickstart_validation.py: logger = setup_logging("INFO")
- code/t037_ci_width_reporting.py: logger = setup_logging(log_level="INFO")
- code/t022_save_cleaned_datasets.py: setup_logging("INFO")
- code/t034_generate_forest_plot.py: logger = setup_logging(log_level="INFO")
- code/t045_conditional_bootstrap_reduction.py: setup_logging("INFO")
- code/t023_reanalyze_cleaned_variants.py: logger = setup_logging(log_level="INFO")
- code/utils.py: - setup_logging()
- code/utils.py: - setup_logging("INFO")
- code/utils.py: - setup_logging(log_level="INFO")
- code/utils.py: - setup_logging(name="my_logger", log_level="DEBUG")
- code/utils.py: - setup_logging("my_logger", "DEBUG")
- code/utils.py: - setup_logging("my_logger")
- code/t044_runtime_profiling.py: setup_logging()
- code/cleanup_utils.py: setup_logging(log_level)
- code/t035_generate_ci_heatmap.py: logger = setup_logging(log_level="INFO")
- code/profiler.py: setup_logging()
- code/t048_verify_checksums_and_state.py: logger = setup_logging("INFO")
- code/t041_generate_final_report.py: logger = setup_logging(log_level="INFO")
- code/main.py: logger = setup_logging(log_level="INFO")
- code/data_loader.py: logger = setup_logging("INFO")
- code/t013_record_baseline_metrics.py: logger = setup_logging(log_level="INFO")
- code/t040_create_comparison_report.py: logger: logging.Logger = setup_logging(log_level="INFO")
- code/t030_dataset_size_sensitivity.py: logger = setup_logging(log_level="INFO")
- code/t039_log_excluded_datasets.py: logger = setup_logging(log_level="INFO")

Make `setup_logging` in `code/utils.py` accept ALL of the above.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (25):
- code/t036_pvalue_shift_reporting.py: b_p = b.get("t_test", {}).get("p_value", 1)
- code/t036_pvalue_shift_reporting.py: c_p = c.get("t_test", {}).get("p_value", 1)
- code/t036_pvalue_shift_reporting.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/t037_ci_width_reporting.py: b_ci = b.get("t_test", {}).get("ci", [0, 0])
- code/t037_ci_width_reporting.py: c_ci = c.get("t_test", {}).get("ci", [0, 0])
- code/t037_ci_width_reporting.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/t022_save_cleaned_datasets.py: raw_dir = config.get("RAW_DATA_PATH", "data/raw")
- code/t022_save_cleaned_datasets.py: processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
- code/t022_save_cleaned_datasets.py: df_clean = strat["func"](df, k=strat.get("k", 1.5))
- code/t034_generate_forest_plot.py: b_p = b.get("t_test", {}).get("p_value", 1)
- code/t034_generate_forest_plot.py: c_p = c.get("t_test", {}).get("p_value", 1)
- code/t034_generate_forest_plot.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/t045_conditional_bootstrap_reduction.py: size = data.get('dataset_size') or data.get('n_rows')
- code/config.py: Scripts import ``get_config`` and use ``config.get(key, default)`` to obtain
- code/t044_runtime_profiling.py: total_duration = sum(item.get("duration_seconds", 0) for item in profiling_data)
- code/t044_runtime_profiling.py: "name": item.get("function") or item.get("block"),
- code/t044_runtime_profiling.py: "duration_seconds": item.get("duration_seconds"),
- code/t044_runtime_profiling.py: "status": item.get("status")
- code/t035_generate_ci_heatmap.py: b_ci = b.get("t_test", {}).get("ci", [0, 0])
- code/t035_generate_ci_heatmap.py: c_ci = c.get("t_test", {}).get("ci", [0, 0])
- code/t035_generate_ci_heatmap.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/profiler.py: item.get("duration_seconds", 0) for item in _profile_data
- code/profiler.py: "successful": sum(1 for item in _profile_data if item.get("status") == "success"),
- code/profiler.py: "failed": sum(1 for item in _profile_data if item.get("status") == "failed"),
- code/profiler.py: if item.get("duration_seconds", 0) > threshold_seconds

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/t035_generate_ci_heatmap.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t023_reanalyze_cleaned_variants.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/t035_generate_ci_heatmap.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_fpr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t032_permutation_null_fpr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
