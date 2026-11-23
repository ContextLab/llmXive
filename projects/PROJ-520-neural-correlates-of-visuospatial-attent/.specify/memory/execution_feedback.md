# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…ntegrityError(f"Detected synthetic data source: {source_url}")…”
- code/verify_metadata.py: synthetic/fake INPUT data not authorized by the spec — “….error(f"Found potential synthetic data indicators: {found_indic…”
- code/verify_metadata_task.py: synthetic/fake INPUT data not authorized by the spec — “…integrity and absence of synthetic data.  This script verifies t…”
- code/verify_metadata_task.py: synthetic/fake INPUT data not authorized by the spec — “…s or values that suggest synthetic data generation     # based o…”
- code/verify_metadata_task.py: synthetic/fake INPUT data not authorized by the spec — “…logger.error("CRITICAL: Synthetic data indicators found in meta…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…ntegrityError(f"Detected synthetic data source: {source_url}")…”; code/verify_metadata.py: synthetic/fake INPUT data not authorized by the spec — “….error(f"Found potential synthetic data indicators: {found_indic…”; code/verify_metadata_task.py: synthetic/fake INPUT data not authorized by the spec — “…integrity and absence of synthetic data.  This script verifies t…”; 4 command(s) failed: python code/main.py --task download (rc=1); python code/main.py --task preprocess (rc=1); python code/main.py --task features (rc=1); 4 declared deliverable(s) absent: data/processed/feature_metadata.json; data/processed/features_matrix.csv; data/processed/metadata.json

## Failing / missing run-book commands

- python code/main.py --task download -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 13, in <module>
    from config import get_paths, get_config, set_random_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 2, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --task preprocess -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 13, in <module>
    from config import get_paths, get_config, set_random_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 2, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --task features -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 13, in <module>
    from config import get_paths, get_config, set_random_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 2, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --task classify -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/main.py", line 13, in <module>
    from config import get_paths, get_config, set_random_seed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-520-neural-correlates-of-visuospatial-attent/code/config.py", line 2, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/processed/feature_metadata.json
- data/processed/features_matrix.csv
- data/processed/metadata.json
- data/processed/t_test_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_correlations.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/collinearity_analysis.py` — NOT invoked by the run-book
    - `code/fwe_correction.py` — NOT invoked by the run-book
    - `code/fix_metadata_missing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_correlations.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/classification.py` — NOT invoked by the run-book
    - `code/collinearity_analysis.py` — NOT invoked by the run-book
    - `code/feature_validation.py` — NOT invoked by the run-book
    - `code/feature_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze_correlations.py` — NOT invoked by the run-book
    - `code/save_features.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/streaming_loader.py` — NOT invoked by the run-book
    - `code/classification.py` — NOT invoked by the run-book
    - `code/download_data.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/t_test_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/fwe_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/t_test_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
