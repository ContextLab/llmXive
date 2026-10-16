# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- results/resampling_log.json: results file is EMPTY ([]) — the analysis produced no values

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: results/resampling_log.json: results file is EMPTY ([]) — the analysis produced no values; 8 command(s) failed: python code/ingestion.py --output data/raw/merged_raw.parquet (rc=1); python code/descriptors.py --input data/raw/merged_raw.parquet --output data/processed/processed.parquet (rc=1); python code/imbalance.py --input data/processed/processed.parquet --output results/imbalance_metrics.json (rc=1); 3 declared deliverable(s) absent: data/processed/descriptor_schema.json; data/processed/descriptors.parquet; data/processed/preprocessed_data.parquet

## Failing / missing run-book commands

- python code/ingestion.py --output data/raw/merged_raw.parquet -> rc=1
s/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/ingestion.py", line 499, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/ingestion.py", line 478, in main
    result = ingest_materials_data(streaming=args.streaming)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/ingestion.py", line 410, in ingest_materials_data
    oqmd_data = fetch_oqmd_data(streaming=streaming)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/ingestion.py", line 213, in fetch_oqmd_data
    return exponential_backoff_retry(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/ingestion.py", line 137, in exponential_backoff_retry
    raise DataFetchError(error_msg)
downloaders.DataFetchError: Persistent failure for OQMD after 6 attempts: download_oqmd_constitution() got an unexpected keyword argument 'streaming'

- python code/descriptors.py --input data/raw/merged_raw.parquet --output data/processed/processed.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/descriptors.py", line 13, in <module>
    from magpie import Magpie
ModuleNotFoundError: No module named 'magpie'

- python code/imbalance.py --input data/processed/processed.parquet --output results/imbalance_metrics.json -> rc=1

Cannot proceed: Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/data/processed/descriptors.parquet

- python code/training.py --input data/processed/processed.parquet --strategy skewed --output artifacts/models/baseline/ -> rc=1
57,709 - INFO - Starting training pipeline...
2026-10-16 09:52:57,709 - INFO - Memory profile logged for run_training_pipeline: 188.42 MB

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 167, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 164, in main
    run_training_pipeline(data_path, output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/memory_profiler.py", line 98, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 99, in run_training_pipeline
    df = load_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 31, in load_data
    raise FileNotFoundError(f"Data file not found: {data_path}")
FileNotFoundError: Data file not found: --input

- python code/resampling.py --input data/processed/processed.parquet --output data/processed/balanced.parquet -> rc=1
2026-10-16 09:52:58,191 - __main__ - ERROR - Resampling pipeline failed: Processed data not found at data/processed/descriptors.parquet. Run descriptors.py first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/resampling.py", line 332, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/resampling.py", line 329, in main
    run_resampling_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/resampling.py", line 243, in run_resampling_pipeline
    df = load_processed_data()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/resampling.py", line 59, in load_processed_data
    raise FileNotFoundError(f"Processed data not found at {input_path}. "
FileNotFoundError: Processed data not found at data/processed/descriptors.parquet. Run descriptors.py first.

- python code/training.py --input data/processed/balanced.parquet --strategy balanced --output artifacts/models/balanced/ -> rc=1
59,068 - INFO - Starting training pipeline...
2026-10-16 09:52:59,068 - INFO - Memory profile logged for run_training_pipeline: 188.50 MB

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 167, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 164, in main
    run_training_pipeline(data_path, output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/memory_profiler.py", line 98, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 99, in run_training_pipeline
    df = load_data(data_path)
         ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/training.py", line 31, in load_data
    raise FileNotFoundError(f"Data file not found: {data_path}")
FileNotFoundError: Data file not found: --input

- python code/evaluation.py --baseline artifacts/models/baseline/ --balanced artifacts/models/balanced/ --output results/comparison_report.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/evaluation.py", line 114, in <module>
    def isolate_bottom_deferred(df: pd.DataFrame, target_col: str, quantile: float = 0.2):
                                    ^^
NameError: name 'pd' is not defined. Did you mean: 'id'?

- python code/shap_analysis.py --models artifacts/models/ --output results/shap_comparison.json -> rc=1
2026-10-16 09:53:00,932 - INFO - Generating synthetic ground truth...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/shap_analysis.py", line 145, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/shap_analysis.py", line 138, in main
    df_synthetic = generate_synthetic_dataset(schema_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/shap_analysis.py", line 64, in generate_synthetic_dataset
    schema = load_descriptor_schema(schema_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/code/shap_analysis.py", line 30, in load_descriptor_schema
    raise FileNotFoundError(f"Schema file not found: {schema_path}")
FileNotFoundError: Schema file not found: data/processed/descriptor_schema.json


## Declared deliverables still missing

- data/processed/descriptor_schema.json
- data/processed/descriptors.parquet
- data/processed/preprocessed_data.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptor_schema.json` is declared but was NOT written. Scripts referencing it:
    - `code/shap_analysis.py` — IS a run-book command
    - `code/shap_ranking.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptor_schema.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors.py` — IS a run-book command
    - `code/evaluation.py` — IS a run-book command
    - `code/generate_schemas.py` — NOT invoked by the run-book
    - `code/imbalance.py` — IS a run-book command
    - `code/main.py` — NOT invoked by the run-book
    - `code/resampling.py` — IS a run-book command
    - `code/shap_analysis.py` — IS a run-book command
    - `code/shap_compute.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/preprocessed_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/descriptors.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/preprocessed_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
