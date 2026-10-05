# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/error_handling.py: synthetic/fake INPUT data not authorized by the spec — “…. It does NOT     return synthetic data or a placeholder.     ""…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/integration/test_full_pipeline.py --sample-size 100`
  - argparse error: `python -m pytest: error: unrecognized arguments: --sample-size 100`

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/error_handling.py: synthetic/fake INPUT data not authorized by the spec — “…. It does NOT     return synthetic data or a placeholder.     ""…”; 7 command(s) failed: python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet (rc=1); python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet (rc=1); python code/modeling/split.py --input data/processed/crystal_molecules.parquet --output_dir data/splits (rc=1); 12 declared deliverable(s) absent: data/processed/crystal_dataset.csv; data/processed/grouped_dataset.csv; data/processed/polymorphic_dataset.csv

## Failing / missing run-book commands

- python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/ingestion/load_cod.py", line 25, in <module>
    from exceptions import DownloadError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/exceptions.py", line 38, in <module>
    class ValidationError(Exception):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/exceptions.py", line 46, in ValidationError
    def __init__(self, message: str, field: str = None, value: Any = None):
                                                               ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
- python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/ingestion/parse_cif.py", line 38, in <module>
    from error_handling import handle_memory_error, safe_process_item
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/error_handling.py", line 19, in <module>
    from exceptions import DownloadError, MemoryErrorHandled, ValidationError
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/exceptions.py", line 38, in <module>
    class ValidationError(Exception):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/exceptions.py", line 46, in ValidationError
    def __init__(self, message: str, field: str = None, value: Any = None):
                                                               ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?
- python code/modeling/split.py --input data/processed/crystal_molecules.parquet --output_dir data/splits -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/modeling/split.py", line 342, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/modeling/split.py", line 309, in main
    input_file = get_path_processed_data("grouped_dataset.csv")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path_processed_data() takes 0 positional arguments but 1 was given
- python code/modeling/train.py --train data/splits/train.parquet --test data/splits/test.parquet --output data/results/model_metrics.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/modeling/train.py", line 15, in <module>
    from sklearn.externals import joblib
ImportError: cannot import name 'joblib' from 'sklearn.externals' (/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/.venv/lib/python3.11/site-packages/sklearn/externals/__init__.py)
- python code/analysis/interpret.py --model_path data/results/model_metrics.json --data data/splits/train.parquet --output data/results/feature_importance.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/analysis/interpret.py", line 273, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/analysis/interpret.py", line 193, in main
    dataset_path = get_path_processed_data("crystal_dataset.csv")
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path_processed_data() takes 0 positional arguments but 1 was given
- python -m pytest tests/unit/test_ingestion.py -v -> rc=4
    ============================= test session starts ==============================
platform linux -- Python 3.11.16, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/llmXive/llmXive/projects/PROJ-030-predicting-crystal-structures-from-molec/code/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_ingestion.py
- python -m pytest tests/integration/test_full_pipeline.py --sample-size 100 -> rc=4
    ERROR: usage: python -m pytest [options] [file_or_dir] [file_or_dir] [...]
python -m pytest: error: unrecognized arguments: --sample-size 100
  inifile: /home/runner/work/llmXive/llmXive/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive

## Declared deliverables still missing

- data/processed/crystal_dataset.csv
- data/processed/grouped_dataset.csv
- data/processed/polymorphic_dataset.csv
- data/processed/split_indices.json
- data/results/majority_class_baseline_metrics.json
- data/results/model_metrics.json
- data/results/mw_baseline_metrics.json
- data/results/polymorphism_metrics.json
- data/results/shap_analysis.json
- data/validation/fingerprint_check.json
- data/validation/report_check.json
- data/validation/success_criterion_check.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path_processed_data` — defined in `code/config.py`; called 10 way(s):

- code/config.py: "processed": str(get_path_processed_data()),
- code/ingestion/dataset_builder.py: processed_dir = get_path_processed_data()
- code/ingestion/validate_fingerprints.py: dataset_path = get_path_processed_data("crystal_dataset.csv")
- code/modeling/split.py: input_file = get_path_processed_data("grouped_dataset.csv")
- code/modeling/split.py: output_split_file = get_path_processed_data("split_indices.json")
- code/modeling/evaluate.py: split_path = get_path_absolute(get_path_processed_data(), "split_indices.json")
- code/modeling/evaluate.py: dataset_path = get_path_absolute(get_path_processed_data(), "grouped_dataset.csv")
- code/modeling/validate_split.py: dataset_path = get_path_processed_data("grouped_dataset.csv")
- code/modeling/validate_split.py: split_indices_path = get_path_processed_data("split_indices.json")
- code/analysis/interpret.py: dataset_path = get_path_processed_data("crystal_dataset.csv")

Make `get_path_processed_data` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/crystal_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/run_pipeline.py` — NOT invoked by the run-book
    - `code/ingestion/validate_fingerprints.py` — NOT invoked by the run-book
    - `code/modeling/group_rare.py` — NOT invoked by the run-book
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/analysis/interpret.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/crystal_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/grouped_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/split.py` — IS a run-book command
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/group_rare.py` — NOT invoked by the run-book
    - `code/modeling/validate_split.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/grouped_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/polymorphic_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/ingestion/dataset_builder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/polymorphic_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/modeling/split.py` — IS a run-book command
    - `code/modeling/generate_overlap_gate_report.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
    - `code/modeling/__init__.py` — NOT invoked by the run-book
    - `code/modeling/validate_split.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/majority_class_baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/majority_class_baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/mw_baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — IS a run-book command
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mw_baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/polymorphism_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/polymorphism_metrics.py` — NOT invoked by the run-book
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/polymorphism_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_report.py` — NOT invoked by the run-book
    - `code/analysis/interpret.py` — IS a run-book command
  Make ONE of these WRITE `data/results/shap_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/fingerprint_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/validate_fingerprints.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/fingerprint_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/report_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/report_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/success_criterion_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/generate_final_metrics.py` — NOT invoked by the run-book
    - `code/modeling/verify_success_criterion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/success_criterion_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
