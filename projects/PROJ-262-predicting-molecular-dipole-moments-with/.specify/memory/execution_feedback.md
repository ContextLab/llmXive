# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data/generate_processed_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/generate_processed_data.py (rc=1); python code/training/train_rf.py (rc=1); python code/analysis/generate_performance_plots.py (rc=1); 1 declared deliverable(s) absent: data/processed/molecules_10k.parquet

## Failing / missing run-book commands

- python code/data/generate_processed_data.py -> rc=1
    mport_optional_dependency(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/compat/_optional.py", line 161, in import_optional_dependency
    raise ImportError(msg) from err
ImportError: `Import pyarrow` failed. pyarrow is required for parquet support. Use pip or conda to install the pyarrow package.
- python code/training/train_rf.py -> rc=1
    ts-with/code/training/train_rf.py", line 40, in <module>
    from training.save_checkpoints import save_rf_checkpoint
ImportError: cannot import name 'save_rf_checkpoint' from partially initialized module 'training.save_checkpoints' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/save_checkpoints.py)
- python code/analysis/generate_performance_plots.py -> rc=1
     line 138, in generate_plots
    df = load_metrics(metrics_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 51, in load_metrics
    raise ValueError(f"Metrics CSV missing columns: {missing}")
ValueError: Metrics CSV missing columns: {'mae', 'rmse', 'model'}
- python code/analysis/generate_significance.py -> rc=1
    ric_data = _load_metrics(metrics_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 54, in _load_metrics
    raise ValueError(f"Metrics CSV missing required columns: {missing}")
ValueError: Metrics CSV missing required columns: {'mae', 'rmse', 'model'}
- python code/generate_summary.py -> rc=1
    ary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv

## Declared deliverables still missing

- data/processed/molecules_10k.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/molecules_10k.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/generate_processed_data.py` — IS a run-book command
    - `code/training/train_rf.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/molecules_10k.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## Files your producers ACTUALLY wrote — reconcile consumers against THESE

A `missing columns` / `KeyError` / `FileNotFoundError: <file>` failure above is a cross-file DATA-contract mismatch: a consumer expects column names or a path the UPSTREAM producer did not write. The traceback shows only what the consumer EXPECTS — here is what actually landed on disk. Make the PRODUCER write the exact column names / path the consumers need (or make the consumers read these actual names). Fix the ROOT producer first: a script failing on a missing INPUT file is a CASCADE that clears once its producer is fixed — do not edit the cascade victim in isolation.

- `data/checkpoints/model_seed_0.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_1.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_2.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_3.pt.npy` (144 bytes)
- `data/checkpoints/model_seed_4.pt.npy` (144 bytes)
- `data/checkpoints/rf_metrics.csv` — actual CSV header: `model,seed,mae,rmse`
- `data/checkpoints/rf_seed_0.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_1.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_2.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_3.pkl` (337617 bytes)
- `data/checkpoints/rf_seed_4.pkl` (337617 bytes)
- `results/metrics.csv` — actual CSV header: `seed,model_type,MAE,RMSE`
