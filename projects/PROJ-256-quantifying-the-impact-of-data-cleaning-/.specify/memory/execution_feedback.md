# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/sensitivity.py: self-declared fabricated metric — “…lder         inc_rate = 0.1 # Placeholder                  results["fpr"].append({"k": k, "fpr"…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main --dataset-id wine_quality --stage cleaning_bootstrap`
  - script usage: `main.py [-h] [--stage STAGE]`
  - argparse error: `main.py: error: unrecognized arguments: --dataset-id wine_quality`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/sensitivity.py: self-declared fabricated metric — “…lder         inc_rate = 0.1 # Placeholder                  results["fpr"].append({"k": k, "fpr"…”; 3 command(s) failed: python -m code.main (rc=1); python -m code.data_loader (rc=1); python -m code.main --dataset-id wine_quality --stage cleaning_bootstrap (rc=2); 5 declared deliverable(s) absent: data/processed/baseline_metrics.json; data/processed/cleaned_metrics.json; data/processed/comparison_report.json

## Failing / missing run-book commands

- python -m code.main -> rc=1
    s
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/main.py", line 75, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/main.py", line 71, in main
    run_pipeline(stage=args.stage)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/main.py", line 44, in run_pipeline
    run_baseline_analysis(raw_dir=raw_dir, output_file=out_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/analysis.py", line 194, in run_baseline_analysis
    dataframe = _load_raw_dataset(raw_dir)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-256-quantifying-the-impact-of-data-cleaning-/code/analysis.py", line 124, in _load_raw_dataset
    raise FileNotFoundError(f"No CSV files found in raw directory: {raw_dir}")
FileNotFoundError: No CSV files found in raw directory: data/raw
- python -m code.data_loader -> rc=1
    No dataset URLs found in configuration. Aborting.
- python -m code.main --dataset-id wine_quality --stage cleaning_bootstrap -> rc=2
    usage: main.py [-h] [--stage STAGE]
main.py: error: unrecognized arguments: --dataset-id wine_quality

## Declared deliverables still missing

- data/processed/baseline_metrics.json
- data/processed/cleaned_metrics.json
- data/processed/comparison_report.json
- data/processed/null_fpr_metrics.json
- data/processed/outlier_threshold_sweep_report.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **150** real records with fields: sepallength, sepalwidth, petallength, petalwidth, class, outcome.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd
# Iris dataset (UCI) is available on OpenML with ID 61
dataset = openml.datasets.get_dataset(61)
X, y, _, _ = dataset.get_data(dataset_format='dataframe')
# Combine features and target, naming the target column 'outcome'
df = X.copy()
df['outcome'] = y
print(f"RECORDS={len(df)}")
print("FIELDS=" + ",".join(df.columns))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `run_baseline_analysis` — defined in `code/analysis.py`; called 12 way(s):

- code/t033_outlier_threshold_sweep.py: raw_metrics = run_baseline_analysis(
- code/t033_outlier_threshold_sweep.py: cleaned_metrics = run_baseline_analysis(
- code/t033_outlier_threshold_sweep.py: null_metrics = run_baseline_analysis(
- code/t023_reanalyze_cleaned_variants.py: metrics = run_baseline_analysis(dataframe=df)
- code/t013_record_baseline_metrics.py: metrics = run_baseline_analysis(dataframe=df)
- code/main.py: run_baseline_analysis(raw_dir=raw_dir, output_file=out_file)
- code/analysis.py: 1. ``run_baseline_analysis(dataframe=df)`` – analyse the supplied DataFrame.
- code/analysis.py: 2. ``run_baseline_analysis(df)`` – positional DataFrame.
- code/analysis.py: 3. ``run_baseline_analysis(raw_dir='data/raw')`` – load first CSV from directory.
- code/analysis.py: 4. ``run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')``
- code/analysis.py: 5. ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – third
- code/t012_run_baseline_analysis.py: run_baseline_analysis(

Make `run_baseline_analysis` in `code/analysis.py` accept ALL of the above.

### `setup_logging` — defined in `code/utils.py`; called 25 way(s):

- code/t1204_cleanup_t0_scripts.py: logger = setup_logging(log_level="INFO")
- code/validate_dataset_bins.py: logger = setup_logging(log_level="INFO")
- code/t027_run_comparison.py: logger = setup_logging("INFO")
- code/sensitivity.py: logger = setup_logging("INFO")
- code/t039_log_excluded_datasets.py: logger = setup_logging(log_level="INFO")
- code/t034_generate_forest_plot.py: logger = setup_logging(log_level="INFO")
- code/t038_effect_size_reporting.py: logger = setup_logging(log_level="INFO")
- code/audit_util_duplicates.py: logger = setup_logging("INFO")
- code/validation.py: logger = setup_logging(log_level="INFO")
- code/t041_generate_final_report.py: logger = setup_logging(log_level="INFO")
- code/t033_outlier_threshold_sweep.py: logger = setup_logging(log_level="INFO")
- code/generate_raw_readme.py: logger = setup_logging(log_level="INFO")
- code/t045_conditional_bootstrap_reduction.py: setup_logging("INFO")
- code/t023_reanalyze_cleaned_variants.py: logger = setup_logging(log_level="INFO")
- code/utils.py: - ``setup_logging()``                     → INFO level, default name.
- code/utils.py: - ``setup_logging("INFO")``               → INFO level, default name.
- code/utils.py: - ``setup_logging(log_level="DEBUG")``    → DEBUG level, default name.
- code/utils.py: - ``setup_logging(name="my_logger")``     → INFO level, custom name.
- code/utils.py: - ``setup_logging("my_logger", "WARNING")`` → WARNING level, custom name.
- code/t013_record_baseline_metrics.py: logger = setup_logging(log_level="INFO")
- code/t048_verify_checksums_and_state.py: logger = setup_logging("INFO")
- code/t044_runtime_profiling.py: setup_logging()
- code/t036_pvalue_shift_reporting.py: logger = setup_logging(log_level="INFO")
- code/main.py: logger = setup_logging(log_level="INFO")
- code/audit_t0_files.py: setup_logging(log_level="INFO")

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
- code/validate_dataset_bins.py: baseline_path = Path(config.get("PROCESSED_DATA_PATH", "data/processed")) / "baseline_metrics.json"
- code/validate_dataset_bins.py: dataset_name = dataset_info.get("dataset_name", "unknown")
- code/validate_dataset_bins.py: n_rows = dataset_info.get("n_rows", dataset_info.get("dataset_size", 0))
- code/sensitivity.py: n = data.get('dataset_info', {}).get('n_rows', 0)
- code/config.py: Attributes are accessed via ``get(key, default)``.  Unknown attribute
- code/config.py: return self._store.get(key, default)
- code/t034_generate_forest_plot.py: b_p = b.get("t_test", {}).get("p_value", 1)
- code/t034_generate_forest_plot.py: c_p = c.get("t_test", {}).get("p_value", 1)
- code/t034_generate_forest_plot.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/t038_effect_size_reporting.py: b_d = b.get("t_test", {}).get("effect_size", None)
- code/t038_effect_size_reporting.py: c_d = c.get("t_test", {}).get("effect_size", None)
- code/t038_effect_size_reporting.py: cleaned_path = Path(info.get("cleaned_metrics_path", ""))
- code/t041_generate_final_report.py: "generated_at": comparison.get("generated_at", "unknown"),
- code/t041_generate_final_report.py: "num_datasets": len(comparison.get("baseline_metrics", [])),
- code/t045_conditional_bootstrap_reduction.py: size = data.get('dataset_size') or data.get('n_rows')
- code/utils.py: logger.setLevel(logging._nameToLevel.get(level.upper(), logging.INFO))
- code/t013_record_baseline_metrics.py: seed = int(config.get("RANDOM_SEED", 42))
- code/t013_record_baseline_metrics.py: raw_path = Path(config.get("RAW_DATA_PATH", "data/raw"))
- code/t013_record_baseline_metrics.py: output_path = Path(config.get("PROCESSED_DATA_PATH", "data/processed"))
- code/t048_verify_checksums_and_state.py: "random_seed": config.get("RANDOM_SEED", "unknown"),
- code/t048_verify_checksums_and_state.py: "dataset_urls": config.get("DATASET_URLS", "unknown")
- code/t048_verify_checksums_and_state.py: artifacts_in_state = existing_state.get("artifacts", {})
- code/t048_verify_checksums_and_state.py: artifact_dir = config.get("OUTPUT_PATH", "data/processed")
- code/t044_runtime_profiling.py: total_duration = sum(item.get("duration_seconds", 0) for item in profiling_data)
- code/t044_runtime_profiling.py: "name": item.get("function") or item.get("block"),

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_dataset_bins.py` — NOT invoked by the run-book
    - `code/t027_run_comparison.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/t039_log_excluded_datasets.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t038_effect_size_reporting.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/t041_generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/t027_run_comparison.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/t039_log_excluded_datasets.py` — NOT invoked by the run-book
    - `code/t034_generate_forest_plot.py` — NOT invoked by the run-book
    - `code/t038_effect_size_reporting.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `code/t033_outlier_threshold_sweep.py` — NOT invoked by the run-book
    - `code/t023_reanalyze_cleaned_variants.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/comparison_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/t027_run_comparison.py` — NOT invoked by the run-book
    - `code/t041_generate_final_report.py` — NOT invoked by the run-book
    - `code/t040_create_comparison_report.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
    - `code/scripts/generate_migration_plan.py` — NOT invoked by the run-book
    - `code/scripts/quickstart_fix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparison_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_fpr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/t033_outlier_threshold_sweep.py` — NOT invoked by the run-book
    - `code/t032_permutation_null_fpr.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/outlier_threshold_sweep_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/outlier_threshold_sweep_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
