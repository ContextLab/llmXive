# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_metrics.json; data/processed/null_fpr_metrics.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    ta/processed/baseline_metrics.json
2026-07-14 03:45:45 - analysis - INFO - Running baseline analysis on directory: data/raw
2026-07-14 03:45:45 - analysis - INFO - Loaded dataset: placeholder_dataset (20 rows)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/t012_run_baseline_analysis.py", line 52, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/t012_run_baseline_analysis.py", line 42, in main
    success = run_baseline_analysis(raw_dir, output_file, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/analysis.py", line 302, in run_baseline_analysis
    "generated_at": datetime.now().isoformat(),
                    ^^^^^^^^
NameError: name 'datetime' is not defined
2026-07-14 03:45:45 - __main__ - ERROR - Script t012_run_baseline_analysis.py failed with return code 1
2026-07-14 03:45:45 - __main__ - ERROR - Pipeline failed at t012_run_baseline_analysis.py

## Declared deliverables still missing

- data/processed/cleaned_metrics.json
- data/processed/null_fpr_metrics.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_baseline_analysis` — defined in `code/analysis.py`; called 11 way(s):

- code/t023_reanalyze_cleaned_variants.py: # The function signature is: run_baseline_analysis(df, dataset_name=..., config=config)
- code/t023_reanalyze_cleaned_variants.py: result = run_baseline_analysis(
- code/t012_run_baseline_analysis.py: success = run_baseline_analysis(raw_dir, output_file, config)
- code/t013_record_baseline_metrics.py: results = run_baseline_analysis(df, dataset_name=dataset_name, config=config)
- code/t013_record_baseline_metrics.py: # We need to load the dataframe here to pass to run_baseline_analysis(df, ...)
- code/analysis.py: 1. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
- code/analysis.py: 2. run_baseline_analysis(df, dataset_name=...) -> returns dict
- code/analysis.py: 3. run_baseline_analysis(df_cleaned, dataset_name=..., config=config) -> returns dict
- code/analysis.py: success = run_baseline_analysis(raw_dir, output_file, config=config)
- code/t033_outlier_threshold_sweep.py: result = run_baseline_analysis(df_cleaned, dataset_name=f"null_k_{k}", config=None)
- code/t032_permutation_null_fpr.py: results = run_baseline_analysis(df=df_null, dataset_name=dataset_name, config=config)

Make `run_baseline_analysis` in `code/analysis.py` accept ALL of the above.

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
- code/t036_pvalue_shift_reporting.py: base_p = base_entry.get('p_value')
- code/t036_pvalue_shift_reporting.py: clean_p = clean_entry.get('p_value')
- code/t036_pvalue_shift_reporting.py: base_p = base_tests[test_name].get('p_value')
- code/t036_pvalue_shift_reporting.py: clean_p = clean_tests[test_name].get('p_value')
- code/t037_ci_width_reporting.py: if not metrics.get('baseline') or not metrics.get('cleaned'):
- code/t037_ci_width_reporting.py: baseline_data = metrics['baseline'].get('datasets', [])
- code/t037_ci_width_reporting.py: cleaned_data = metrics['cleaned'].get('datasets', [])
- code/t037_ci_width_reporting.py: dataset_name = b_entry.get('dataset_name')
- code/t037_ci_width_reporting.py: ci = entry['t_test'].get('ci')
- code/t037_ci_width_reporting.py: coefs = entry['regression'].get('coefficients', [])
- code/t037_ci_width_reporting.py: baseline_cis = get_all_ci_widths(b_entry.get('analysis', {}))
- code/t037_ci_width_reporting.py: cleaned_cis = get_all_ci_widths(c_entry.get('analysis', {}))
- code/t022_save_cleaned_datasets.py: raw_dir = config.get("RAW_DATA_PATH", "data/raw")
- code/t022_save_cleaned_datasets.py: processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
- code/t022_save_cleaned_datasets.py: df_clean = strat["func"](df, k=strat.get("k", 1.5))
- code/t034_generate_forest_plot.py: ds_id = item.get('dataset_id') or item.get('dataset_name') or item.get('name')
- code/t034_generate_forest_plot.py: ds_id = baseline_item.get('dataset_id') or baseline_item.get('dataset_name') or baseline_item.get('name')
- code/t034_generate_forest_plot.py: cleaned_item = cleaned_map.get(ds_id)
- code/t034_generate_forest_plot.py: strategy = cleaned_item.get('strategy', cleaned_item.get('cleaning_strategy', 'Unknown'))
- code/t034_generate_forest_plot.py: output_dir = config.get('OUTPUT_PATH', 'data/processed')
- code/t045_conditional_bootstrap_reduction.py: size = data.get('dataset_size') or data.get('n_rows')
- code/t023_reanalyze_cleaned_variants.py: if result and result.get('success', True):
- code/t023_reanalyze_cleaned_variants.py: seed = config.get("RANDOM_SEED", 42)
- code/t023_reanalyze_cleaned_variants.py: processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
- code/t012_run_baseline_analysis.py: raw_dir = config.get("RAW_DATA_PATH", "data/raw")
- code/t012_run_baseline_analysis.py: output_file = config.get("PROCESSED_DATA_PATH", "data/processed")

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t036_pvalue_shift_reporting.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/t037_ci_width_reporting.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t023_reanalyze_cleaned_variants.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/t035_generate_ci_heatmap.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_fpr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/t041_generate_final_report.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/t032_permutation_null_fpr.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
