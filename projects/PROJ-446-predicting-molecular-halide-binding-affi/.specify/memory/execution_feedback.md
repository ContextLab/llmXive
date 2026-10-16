# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_data_ingestion.py: self-declared fabricated metric — “…cavity_volume = tpsa * 0.5  # arbitrary scaling     return {"charge_density":…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…te basic descriptors for simulated data generation.     Returns…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data based on real descr…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…erating {n_rows} rows of simulated data for halide {target_halid…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ide prediction mode with simulated data."     )   def run_data_s…”
- code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ency & possibly generate simulated data     is_simulated = run_d…”
- code/02_save_processed_data.py: synthetic/fake INPUT data not authorized by the spec — “…ed (bool): If True, load simulated data. If False, load real cle…”
- code/02_save_processed_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading simulated data from {source_file}")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 17 fabricated/simulated-result signal(s) — results are not real measurements: code/01_data_ingestion.py: self-declared fabricated metric — “…cavity_volume = tpsa * 0.5  # arbitrary scaling     return {"charge_density":…”; code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…te basic descriptors for simulated data generation.     Returns…”; code/01_data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic data based on real descr…”; 3 command(s) failed: python code/03_model_training.py (rc=1); python code/04_feature_analysis.py (rc=1); python code/05_statistical_reporting.py (rc=1); 7 declared deliverable(s) absent: data/processed/feature_analysis.json; data/processed/feature_interpretation_summary.csv; data/processed/halide_binding_data.csv

## Failing / missing run-book commands

- python code/03_model_training.py -> rc=1

2026-10-16 17:24:10,189 - __main__ - INFO - Starting model training pipeline...
2026-10-16 17:24:10,189 - __main__ - ERROR - Unexpected error: Preprocessed data not found at data/processed/halide_binding_data.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 331, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 309, in main
    df = load_preprocessed_data()
         ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-446-predicting-molecular-halide-binding-affi/code/03_model_training.py", line 86, in load_preprocessed_data
    raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
FileNotFoundError: Preprocessed data not found at data/processed/halide_binding_data.csv

- python code/04_feature_analysis.py -> rc=1

2026-10-16 17:24:11,489 - __main__ - INFO - Starting Feature Analysis (US3)...
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


## Declared deliverables still missing

- data/processed/feature_analysis.json
- data/processed/feature_interpretation_summary.csv
- data/processed/halide_binding_data.csv
- data/processed/model_runs.json
- data/processed/physical_plausibility.json
- data/processed/power_status.json
- data/processed/statistical_summary.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PubChemPy` to the project's `requirements.txt` and `pip install PubChemPy`.
- **Verified**: this loads **3** real records with fields: host_smiles, host_inchi, halide_identity, source_database, source_record_id.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp
# Query a few common halide ions and collect available identifiers.
halides = ["Cl-", "Br-", "I-"]
records = []
for h in halides:
    comps = pcp.get_compounds(h, 'name')
    for c in comps:
        records.append({
            'host_smiles': getattr(c, 'isomeric_smiles', None),
            'host_inchi': getattr(c, 'inchi', None),
            'halide_identity': h,
            'binding_constant_value': None,
            'binding_constant_units': None,
            'solvent': None,
            'source_database': 'PubChem',
            'source_record_id': c.cid
        })
print(f"RECORDS={len(records)}")
print("FIELDS=host_smiles,host_inchi,halide_identity,source_database,source_record_id")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

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
- `data/processed/power_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_statistical_reporting.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_statistical_reporting.py` — IS a run-book command
    - `code/06_generate_final_report.py` — NOT invoked by the run-book
    - `code/07_validate_quickstart.py` — NOT invoked by the run-book
    - `code/08_update_state_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
