# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py (rc=1); python projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py (rc=1); python projects/001-predicting-molecular-dipole-moments/code/data/preprocess_3d.py (rc=1); 1 declared deliverable(s) absent: data/processed/molecules_10k.parquet

## Failing / missing run-book commands

- python projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py -> rc=1
    "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1168, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'qm9' doesn't exist on the Hub or cannot be accessed.
- python projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py -> rc=1
    ts/code/data/create_subset.py", line 55, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py", line 38, in main
    raise FileNotFoundError(f"Raw QM9 parquet not found at {raw_path}")
FileNotFoundError: Raw QM9 parquet not found at data/raw/qm9.parquet
- python projects/001-predicting-molecular-dipole-moments/code/data/preprocess_3d.py -> rc=1
    "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1168, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'qm9' doesn't exist on the Hub or cannot be accessed.
- python projects/001-predicting-molecular-dipole-moments/code/data/extract_2d_descriptors.py -> rc=1
    Subset parquet not found at data/processed/molecules_10k.parquet
- python code/analysis/generate_performance_plots.py -> rc=1
     line 138, in generate_plots
    df = load_metrics(metrics_csv)
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 46, in load_metrics
    raise FileNotFoundError(f"Metrics file not found: {csv_path}")
FileNotFoundError: Metrics file not found: results/metrics.csv
- python code/generate_summary.py -> rc=1
    ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 42, in read_metrics
    raise FileNotFoundError(f"Metrics file not found: {csv_path}")
FileNotFoundError: Metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/results/metrics.csv

## Declared deliverables still missing

- data/processed/molecules_10k.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/molecules_10k.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/training/train_gnn.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/molecules_10k.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
