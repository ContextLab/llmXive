# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…""     Checks if a valid synthetic data generation configuration…”
- code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…ts.          Per FR-001, synthetic data is only a fallback if IP…”
- code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…:         return True, f"Synthetic data configuration found at {…”
- code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…ue",         help="Allow synthetic data fallback if real data is…”
- code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…duction: Proceeding with synthetic data due to missing real data…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…""     Checks if a valid synthetic data generation configuration…”; code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…ts.          Per FR-001, synthetic data is only a fallback if IP…”; code/00_data_availability_gate.py: synthetic/fake INPUT data not authorized by the spec — “…:         return True, f"Synthetic data configuration found at {…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 6 command(s) failed: python code/00_data_availability_gate.py (rc=1); python code/01_data_acquisition.py (rc=1); python code/02_model_training.py (rc=1); 2 declared deliverable(s) absent: data/processed/metrics_records.json; data/processed/regression_results.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-778-quantifying-calibration-drift-of-machine/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/main.py': [Errno 2] No such file or directory

- python code/00_data_availability_gate.py -> rc=1
=== Data Availability Gate ===
Checking for required datasets (IPUMS CPS / UCI Adult)...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/00_data_availability_gate.py", line 136, in <module>
    sys.exit(run_gate())
             ^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/00_data_availability_gate.py", line 101, in run_gate
    is_real_data_available, real_msg = check_ipums_cps_availability(config)
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/00_data_availability_gate.py", line 30, in check_ipums_cps_availability
    data_root = get_path("data/raw")
                ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/utils/config.py", line 53, in get_path
    raise KeyError(f"Config key '{key}' not found or is empty.")
KeyError: "Config key 'data/raw' not found or is empty."

- python code/01_data_acquisition.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/01_data_acquisition.py", line 305, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/01_data_acquisition.py", line 297, in main
    parser = argparse.ArgumentParser(description="Data Acquisition and Alignment Pipeline")
             ^^^^^^^^
NameError: name 'argparse' is not defined

- python code/02_model_training.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/02_model_training.py", line 289, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/02_model_training.py", line 278, in main
    result = run_training_pipeline(config_path=args.config, force_train=args.force)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/02_model_training.py", line 205, in run_training_pipeline
    raw_data_dir = get_path("raw_data")
                   ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/utils/config.py", line 53, in get_path
    raise KeyError(f"Config key '{key}' not found or is empty.")
KeyError: "Config key 'raw_data' not found or is empty."

- python code/03_evaluation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/03_evaluation.py", line 376, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/03_evaluation.py", line 366, in main
    success = run_evaluation_pipeline(
              ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/03_evaluation.py", line 277, in run_evaluation_pipeline
    models_dir = get_path(config, 'paths.models_dir')
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_path() takes 1 positional argument but 2 were given

- python code/04_statistical_analysis.py -> rc=1

2026-10-11 04:10:06,864 - __main__ - INFO - Starting statistical analysis pipeline
2026-10-11 04:10:06,864 - __main__ - ERROR - Analysis pipeline failed: "Invalid config key: data/processed/metrics_records.json. Path segment 'json' not found."

- python code/05_report_generation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/05_report_generation.py", line 275, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-778-quantifying-calibration-drift-of-machine/code/05_report_generation.py", line 265, in main
    parser = argparse.ArgumentParser(description="Generate calibration drift report figures.")
             ^^^^^^^^
NameError: name 'argparse' is not defined

- python -c "import utils.config as cfg; print(cfg.check_data_integrity())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'utils.config'


## Declared deliverables still missing

- data/processed/metrics_records.json
- data/processed/regression_results.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **48842** real records with fields: age, workclass, fnlwgt, education, education-num, marital-status, occupation, relationship, race, sex, capital-gain.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd

ds = openml.datasets.get_dataset(1590)  # UCI Adult dataset
df, *_ = ds.get_data(dataset_format='dataframe')
print(f"RECORDS={len(df)}")
desired = ["year","age","workclass","fnlwgt","education","education-num","marital-status","occupation","relationship","race","sex","capital-gain"]
present = [c for c in desired if c in df.columns]
if present:
    print("FIELDS=" + ",".join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics_records.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_analysis.py` — IS a run-book command
    - `code/05_report_generation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metrics_records.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_analysis.py` — IS a run-book command
    - `code/05_report_generation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
