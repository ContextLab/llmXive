# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…alidation Module (T026)  Generates a synthetic dataset with known groun…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset of exoplanets wi…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {n_planets} planets…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic data to {SYNTHETIC_RAW_PATH}"…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…Run the binning step on synthetic data.     Uses the existing b…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…"Running binning step on synthetic data")      # Create bins…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…et of the full range for synthetic data to ensure enough points…”
- code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…the GMM fitting step on synthetic data.     Uses the existing g…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 12 fabricated/simulated-result signal(s) — results are not real measurements: code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…alidation Module (T026)  Generates a synthetic dataset with known groun…”; code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic dataset of exoplanets wi…”; code/validation/synthetic_recovery.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with {n_planets} planets…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/data/ingest.py; 3 command(s) failed: python code/ingest/preprocess.py (rc=1); python code/main.py (rc=1); python code/tests/integration/test_quickstart_validation.py --mode synthetic (rc=1); 10 declared deliverable(s) absent: data/processed/binned_planets.csv; data/processed/binned_stats.csv; data/processed/deduped_planets.csv

## Failing / missing run-book commands

- python code/data/ingest.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-787-assessing-orbital-period-dependence-of-t/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/data/ingest.py': [Errno 2] No such file or directory

- python code/ingest/preprocess.py -> rc=1
dependence-of-t/code/ingest/preprocess.py", line 170, in main
    df = load_merged_catalogs(merged_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/ingest/preprocess.py", line 22, in load_merged_catalogs
    raise FileNotFoundError(f"Merged catalog not found at {merged_path}")
FileNotFoundError: Merged catalog not found at data/raw/merged_catalog.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/ingest/preprocess.py", line 187, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/ingest/preprocess.py", line 170, in main
    df = load_merged_catalogs(merged_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/ingest/preprocess.py", line 22, in load_merged_catalogs
    raise FileNotFoundError(f"Merged catalog not found at {merged_path}")
FileNotFoundError: Merged catalog not found at data/raw/merged_catalog.csv

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/main.py", line 17, in <module>
    from utils.setup_dirs import initialize_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/utils/setup_dirs.py", line 47, in <module>
    def get_data_dir(subdir: Optional[str] = None) -> Path:
                             ^^^^^^^^
NameError: name 'Optional' is not defined

- python code/tests/integration/test_quickstart_validation.py --mode synthetic -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/tests/integration/test_quickstart_validation.py", line 18, in <module>
    from utils.setup_dirs import initialize_directories
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-787-assessing-orbital-period-dependence-of-t/code/utils/setup_dirs.py", line 47, in <module>
    def get_data_dir(subdir: Optional[str] = None) -> Path:
                             ^^^^^^^^
NameError: name 'Optional' is not defined


## Declared deliverables still missing

- data/processed/binned_planets.csv
- data/processed/binned_stats.csv
- data/processed/deduped_planets.csv
- data/processed/filtered_planets.csv
- data/processed/gap_locations.csv
- data/processed/kde_validation.json
- data/processed/synthetic_validation.json
- data/raw/completeness_map.csv
- data/raw/dr25_raw.csv
- data/raw/kic_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/binned_planets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/binning.py` — NOT invoked by the run-book
    - `code/analysis/gmm_fitter.py` — NOT invoked by the run-book
    - `code/analysis/integrate_gap_analysis.py` — NOT invoked by the run-book
    - `code/analysis/kde_validator.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_binning.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_gmm.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/binned_planets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/binned_stats.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/binned_stats.py` — NOT invoked by the run-book
    - `code/analysis/integrate_gap_analysis.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_regression.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/binned_stats.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/deduped_planets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/binning.py` — NOT invoked by the run-book
    - `code/analysis/integrate_gap_analysis.py` — NOT invoked by the run-book
    - `code/analysis/kde_validator.py` — NOT invoked by the run-book
    - `code/ingest/loaders.py` — NOT invoked by the run-book
    - `code/ingest/preprocess.py` — IS a run-book command
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/deduped_planets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_planets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/vectorized_binning.py` — NOT invoked by the run-book
    - `code/ingest/preprocess.py` — IS a run-book command
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered_planets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gap_locations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/binned_stats.py` — NOT invoked by the run-book
    - `code/analysis/generate_results.py` — NOT invoked by the run-book
    - `code/analysis/gmm_fitter.py` — NOT invoked by the run-book
    - `code/analysis/integrate_gap_analysis.py` — NOT invoked by the run-book
    - `code/analysis/kde_validator.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_gmm.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gap_locations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/kde_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_results.py` — NOT invoked by the run-book
    - `code/analysis/kde_validator.py` — NOT invoked by the run-book
    - `code/models/gap_result.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/kde_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation/synthetic_recovery.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synthetic_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/completeness_map.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/vectorized_regression.py` — NOT invoked by the run-book
    - `code/ingest/download_completeness.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/completeness_map.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dr25_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/download_dr25.py` — NOT invoked by the run-book
    - `code/ingest/merge_catalogs.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/dr25_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/kic_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/download_kic.py` — NOT invoked by the run-book
    - `code/ingest/merge_catalogs.py` — NOT invoked by the run-book
    - `code/tests/integration/test_quickstart_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/kic_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
