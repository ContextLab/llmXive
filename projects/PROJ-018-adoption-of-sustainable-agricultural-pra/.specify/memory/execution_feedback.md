# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Sustainabl…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…culture Adoption Study.  Generates a realistic synthetic dataset conforming to th…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…> Dict[str, Any]:     """Generate a single synthetic respondent record."""…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate the full synthetic dataset.      Args:…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…print(f"Generating synthetic data for {2000} respondents..…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…int(f"Successfully wrote synthetic data to {output_file}")     p…”
- code/03_engineer_features.py: synthetic/fake INPUT data not authorized by the spec — “…might need mapping, but synthetic data usually uses 0/1.     pr…”
- data/metadata.yaml: synthetic/fake INPUT data not authorized by the spec — “…grammatically."       - "Synthetic data approximates distributio…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Sustainabl…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…culture Adoption Study.  Generates a realistic synthetic dataset conforming to th…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…> Dict[str, Any]:     """Generate a single synthetic respondent record."""…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/01_download_data.py --synthetic; 5 command(s) failed: python code/02_clean_data.py (rc=1); python code/03_engineer_features.py (rc=1); python code/04_model_analysis.py (rc=1)

## Failing / missing run-book commands

- python code/01_download_data.py --synthetic -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/01_download_data.py': [Errno 2] No such file or directory
- python code/02_clean_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 292, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 233, in main
    raw_file = get_data_path(config['raw_data_file'])
                             ~~~~~~^^^^^^^^^^^^^^^^^
TypeError: 'Config' object is not subscriptable
- python code/03_engineer_features.py -> rc=1
    2026-07-14 02:11:35,354 - __main__ - INFO - Starting Feature Engineering (T020)...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/03_engineer_features.py", line 346, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/03_engineer_features.py", line 313, in main
    raise FileNotFoundError(f"Cleaned data not found at {input_path}. Run T014 first.")
FileNotFoundError: Cleaned data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv. Run T014 first.
- python code/04_model_analysis.py -> rc=1
    nalysis (E-values) will be skipped.
  warnings.warn("evalues library not installed. Sensitivity analysis (E-values) will be skipped.")
2026-07-14 02:11:37,520 - research_pipeline - INFO - Starting Mediation Analysis and Model Diagnostics (T040)
2026-07-14 02:11:37,520 - research_pipeline - ERROR - Mediation analysis failed: 'Config' object is not subscriptable
2026-07-14 02:11:37,521 - research_pipeline - INFO - Updating section 'mediation_analysis' in modeling_log.yaml
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 530, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 418, in main
    df = load_engineered_data()
         ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 38, in load_engineered_data
    path = Path(config['paths']['processed_data']) / 'engineered_data.csv'
                ~~~~~~^^^^^^^^^
TypeError: 'Config' object is not subscriptable
- python code/05_generate_report.py -> rc=1
    Error: Cleaned data not found at data/processed/cleaned_data.csv. Run T014 first.

2026-07-14 02:11:38,566 - __main__ - INFO - Starting PDF report generation (T042).
2026-07-14 02:11:38,566 - __main__ - ERROR - Missing required data file: Cleaned data not found at data/processed/cleaned_data.csv. Run T014 first.
2026-07-14 02:11:38,566 - __main__ - ERROR - Report generation failed: Cleaned data not found at data/processed/cleaned_data.csv. Run T014 first.
- python code/02_clean_data.py --input data/raw/survey_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 292, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 233, in main
    raw_file = get_data_path(config['raw_data_file'])
                             ~~~~~~^^^^^^^^^^^^^^^^^
TypeError: 'Config' object is not subscriptable

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.
