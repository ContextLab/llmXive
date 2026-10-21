# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…Generate the primary simulated dataset (single halide) and an i…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ide prediction mode with simulated data."         )         stat…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…)         # Generate simulated datasets         primary_df, inde…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…# Write primary simulated dataset         processed_path.p…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…e)         logger.info(f"Simulated primary dataset written to {processed_pa…”
- code/02_save_processed_data.py: synthetic/fake INPUT data not authorized by the spec — “…ed (bool): If True, load simulated data. If False, load real cle…”
- code/02_save_processed_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading simulated data from {source_file}")…”
- code/05_statistical_reporting.py: synthetic/fake INPUT data not authorized by the spec — “…,             "reason": "Simulated Data Mode",             "stat…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/descriptors_added.csv, data/raw/fetch_outcome.json, data/raw/filtered_hosts.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…Generate the primary simulated dataset (single halide) and an i…”; code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ide prediction mode with simulated data."         )         stat…”; code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…)         # Generate simulated datasets         primary_df, inde…”; every produced artifact is gitignored (data/raw/descriptors_added.csv, data/raw/fetch_outcome.json, data/raw/filtered_hosts.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/06_partial_dependence.py; python code/07_independent_evaluation.py; 4 command(s) failed: python code/03_model_training.py (rc=1); python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml (rc=1); python code/04_feature_analysis.py (rc=1); 6 declared deliverable(s) absent: data/processed/feature_analysis.json; data/processed/feature_interpretation_summary.csv; data/processed/halide_binding_data.csv

## Failing / missing run-book commands

- python code/03_model_training.py -> rc=1

2026-10-21 01:32:06,455 - __main__ - INFO - Starting model training pipeline...
2026-10-21 01:32:06,455 - __main__ - ERROR - Unexpected error: Preprocessed data not found at data/processed/halide_binding_data.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 331, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 309, in main
    df = load_preprocessed_data()
         ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 86, in load_preprocessed_data
    raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
FileNotFoundError: Preprocessed data not found at data/processed/halide_binding_data.csv

- python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml -> rc=1

/home/runner/.cache/llmxive/base-env/py311-6f1866971868/jsonschema/__main__.py:4: DeprecationWarning: The jsonschema CLI is deprecated and will be removed in a future version. Please use check-jsonschema instead, which can be installed from https://pypi.org/project/check-jsonschema/
  from jsonschema.cli import main
'contracts/model_output.schema.yaml' does not exist.

- python code/04_feature_analysis.py -> rc=1

2026-10-21 01:32:07,569 - __main__ - INFO - Starting Feature Analysis (US3)...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/04_feature_analysis.py", line 236, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/04_feature_analysis.py", line 205, in main
    df = load_preprocessed_data()
         ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/04_feature_analysis.py", line 40, in load_preprocessed_data
    data_path = get_data_path("processed/halide_binding_data.csv")
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_data_path() takes 0 positional arguments but 1 was given

- python code/06_partial_dependence.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-446-predicting-molecular-halide-binding-affi/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/06_partial_dependence.py': [Errno 2] No such file or directory

- python code/05_statistical_reporting.py -> rc=1
llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/05_statistical_reporting.py", line 80, in save_power_status
    with open(output_path, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/data/processed/power_status.json'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/05_statistical_reporting.py", line 203, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/05_statistical_reporting.py", line 188, in main
    save_power_status(power_status)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/05_statistical_reporting.py", line 80, in save_power_status
    with open(output_path, 'w') as f:
         ^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/data/processed/power_status.json'

- python code/07_independent_evaluation.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-446-predicting-molecular-halide-binding-affi/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/07_independent_evaluation.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/feature_analysis.json
- data/processed/feature_interpretation_summary.csv
- data/processed/halide_binding_data.csv
- data/processed/model_runs.json
- data/processed/physical_plausibility.json
- data/processed/statistical_summary.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_feature_analysis.py` — IS a run-book command
    - `code/06_generate_final_report.py` — NOT invoked by the run-book
    - `code/06_save_feature_outputs.py` — NOT invoked by the run-book
    - `code/07_validate_quickstart.py` — NOT invoked by the run-book
    - `code/08_update_state_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_interpretation_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_feature_summary.py` — NOT invoked by the run-book
    - `code/06_save_feature_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_interpretation_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/halide_binding_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/02_save_processed_data.py` — NOT invoked by the run-book
    - `code/03_model_training.py` — IS a run-book command
    - `code/04_feature_analysis.py` — IS a run-book command
    - `code/05_statistical_reporting.py` — IS a run-book command
    - `code/07_validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/halide_binding_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_runs.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_save_model_runs.py` — NOT invoked by the run-book
    - `code/05_statistical_reporting.py` — IS a run-book command
    - `code/06_generate_final_report.py` — NOT invoked by the run-book
    - `code/07_validate_quickstart.py` — NOT invoked by the run-book
    - `code/08_update_state_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_runs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/physical_plausibility.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_feature_analysis.py` — IS a run-book command
    - `code/05_feature_summary.py` — NOT invoked by the run-book
    - `code/06_save_feature_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/physical_plausibility.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_statistical_reporting.py` — IS a run-book command
    - `code/06_generate_final_report.py` — NOT invoked by the run-book
    - `code/07_validate_quickstart.py` — NOT invoked by the run-book
    - `code/08_update_state_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
