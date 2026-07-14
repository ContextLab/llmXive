# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: run-book completed but produced no data/figure artifacts; 3 declared deliverable(s) absent: data/processed/baseline_metrics.json; data/processed/cleaned_metrics.json; data/processed/null_fpr_metrics.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/baseline_metrics.json
- data/processed/cleaned_metrics.json
- data/processed/null_fpr_metrics.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_baseline_analysis` — defined in `code/analysis.py`; called 13 way(s):

- code/t023_reanalyze_cleaned_variants.py: metrics = run_baseline_analysis(dataframe=df_clean)
- code/t012_run_baseline_analysis.py: run_baseline_analysis(raw_dir, output_file, {})
- code/t013_record_baseline_metrics.py: success = run_baseline_analysis(
- code/t040_create_comparison_report.py: run_baseline_analysis(raw_dir=raw_dir, output_file=str(baseline_path))
- code/t040_create_comparison_report.py: run_baseline_analysis(str(raw_dir), str(baseline_path))
- code/analysis.py: 1. ``run_baseline_analysis(dataframe=my_df)`` – analyse an in‑memory DataFrame.
- code/analysis.py: 2. ``run_baseline_analysis(dataframe=my_df, outcome='y', predictors=['x1','x2'])``
- code/analysis.py: 3. ``run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json',
- code/analysis.py: run_baseline_analysis(
- code/t033_outlier_threshold_sweep.py: result = run_baseline_analysis(dataframe=df)
- code/t033_outlier_threshold_sweep.py: cleaned_result = run_baseline_analysis(dataframe=df_clean)
- code/t033_outlier_threshold_sweep.py: null_result = run_baseline_analysis(dataframe=df_null)
- code/t032_permutation_null_fpr.py: result = run_baseline_analysis(dataframe=df_null)

Make `run_baseline_analysis` in `code/analysis.py` accept ALL of the above.

### `setup_logging` — defined in `code/utils.py`; called 25 way(s):

- code/t036_pvalue_shift_reporting.py: logger = setup_logging(log_level="INFO")
- code/run_quickstart_validation.py: logger = setup_logging("INFO")
- code/t037_ci_width_reporting.py: logger = setup_logging(log_level="INFO")
- code/t022_save_cleaned_datasets.py: setup_logging("INFO")
- code/t034_generate_forest_plot.py: logger = setup_logging(log_level="INFO")
- code/t045_conditional_bootstrap_reduction.py: setup_logging("INFO")
- code/t023_reanalyze_cleaned_variants.py: logger = setup_logging(log_level="INFO")
- code/t012_run_baseline_analysis.py: logger = setup_logging(log_level="INFO")
- code/utils.py: - setup_logging()
- code/utils.py: - setup_logging("INFO")
- code/utils.py: - setup_logging(log_level="DEBUG")
- code/utils.py: - setup_logging(name="my_logger", log_level="WARNING")
- code/utils.py: - setup_logging("my_logger", "DEBUG")
- code/t044_runtime_profiling.py: setup_logging()
- code/cleanup_utils.py: setup_logging(log_level)
- code/t035_generate_ci_heatmap.py: logger = setup_logging(log_level="INFO")
- code/profiler.py: setup_logging()
- code/t048_verify_checksums_and_state.py: logger = setup_logging("INFO")
- code/t041_generate_final_report.py: logger = setup_logging(log_level="INFO")
- code/main.py: logger = setup_logging(log_level="INFO")
- code/data_loader.py: logger = setup_logging("INFO")
- code/t013_record_baseline_metrics.py: logger = setup_logging()
- code/t040_create_comparison_report.py: logger = setup_logging(log_level="INFO")
- code/t030_dataset_size_sensitivity.py: logger = setup_logging("INFO")
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
- code/config.py: return self._config.get(key, default)
- code/utils.py: name: Optional[str] = kwargs.get("name")
- code/utils.py: level: Optional[str] = kwargs.get("log_level")
- code/t044_runtime_profiling.py: total_duration = sum(item.get("duration_seconds", 0) for item in profiling_data)
- code/t044_runtime_profiling.py: "name": item.get("function") or item.get("block"),
- code/t044_runtime_profiling.py: "duration_seconds": item.get("duration_seconds"),
- code/t044_runtime_profiling.py: "status": item.get("status")
- code/t035_generate_ci_heatmap.py: b_ci = b.get("t_test", {}).get("ci", [0, 0])
- code/t035_generate_ci_heatmap.py: c_ci = c.get("t_test", {}).get("ci", [0, 0])
- code/t035_generate_ci_heatmap.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/profiler.py: item.get("duration_seconds", 0) for item in _profile_data
- code/profiler.py: "successful": sum(1 for item in _profile_data if item.get("status") == "success"),

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t012_run_baseline_analysis.py` — NOT invoked by the run-book
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
    - `code/main.py` — IS a run-book command
    - `code/t033_outlier_threshold_sweep.py` — NOT invoked by the run-book
    - `code/t032_permutation_null_fpr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
