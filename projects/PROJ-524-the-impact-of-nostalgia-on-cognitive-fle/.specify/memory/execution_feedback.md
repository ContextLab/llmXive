# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic WCST (Wisconsin Card Sor…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…e         DataFrame with synthetic WCST data.     """     np.random.s…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…(T010d)...")          # Generate synthetic data     df = generate_s…”
- code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…fo(f"Generated {len(df)} synthetic participant records")     log_info(f"Age ran…”
- code/task_t015_stimulus_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> None:     """     Generate synthetic nostalgia stimuli if rea…”
- code/task_t015_stimulus_integrity.py: synthetic/fake INPUT data not authorized by the spec — “…mplementation: We do NOT generate synthetic stimuli here.     We rai…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic WCST (Wisconsin Card Sor…”; code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…e         DataFrame with synthetic WCST data.     """     np.random.s…”; code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…(T010d)...")          # Generate synthetic data     df = generate_s…”; 2 command(s) failed: python code/main.py (rc=1); python -m pytest -v (rc=2); 5 declared deliverable(s) absent: data/processed/cleaned_dataset.csv; data/processed/exclusion_log.json; data/processed/mmse_flag.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
line (T010c)...
2026-10-20 12:10:49,989 - llmXive - INFO - Running Age Exclusion (T012a)...
2026-10-20 12:10:50,359 - llmXive - ERROR - T012a failed: 2026-10-20 12:10:50,320 - T012a_AgeExclusion - INFO - Starting T012a: Age Exclusion
2026-10-20 12:10:50,320 - T012a_AgeExclusion - ERROR - Raw dataset not found at data/raw/raw_dataset.csv
2026-10-20 12:10:50,320 - T012a_AgeExclusion - ERROR - Data file missing: Raw dataset not found at data/raw/raw_dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 155, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 133, in main
    df_raw = load_raw_dataset(paths)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 44, in load_raw_dataset
    raise FileNotFoundError(f"Raw dataset not found at {input_path}")
FileNotFoundError: Raw dataset not found at data/raw/raw_dataset.csv


- python -m pytest -v -> rc=2
runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/utils.py)
=========================== short test summary info ============================
ERROR tests/contract/test_ingestion_schema.py
ERROR tests/integration/test_ingestion.py
ERROR tests/integration/test_sensitivity.py
ERROR tests/integration/test_stimulus_integrity.py
ERROR tests/integration/test_t019_bonferroni.py
ERROR tests/unit/test_bonferroni.py
ERROR tests/unit/test_bonferroni_correction.py
ERROR tests/unit/test_cleaning.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_sensitivity.py
ERROR tests/unit/test_t012c_exclusion_log.py
ERROR tests/unit/test_t015_stimulus_integrity.py
ERROR tests/unit/test_t019_bonferroni.py
ERROR tests/unit/test_t020_effect_sizes.py
ERROR tests/unit/test_t027b_robustness.py
ERROR tests/unit/test_t043_verified_source.py
ERROR tests/unit/test_task_t020.py
ERROR tests/unit/test_task_t026.py
ERROR tests/unit/test_task_t027.py
ERROR tests/unit/test_utils.py
!!!!!!!!!!!!!!!!!!! Interrupted: 21 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 21 errors in 3.85s ==============================



## Declared deliverables still missing

- data/processed/cleaned_dataset.csv
- data/processed/exclusion_log.json
- data/processed/mmse_flag.json
- data/raw/metadata.json
- data/results/runtime_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/assumption_checks.py` — NOT invoked by the run-book
    - `code/generate_robustness_summary.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t020_effect_sizes.py` — NOT invoked by the run-book
    - `code/task_t021_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/task_t012c_generate_exclusion_log.py` — NOT invoked by the run-book
    - `code/task_t012d_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t014b_validity_metrics.py` — NOT invoked by the run-book
    - `code/task_t015a_generate_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mmse_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/task_t012d_mmse_flag.py` — NOT invoked by the run-book
    - `code/task_t012e_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — NOT invoked by the run-book
    - `code/task_t014b_validity_metrics.py` — NOT invoked by the run-book
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mmse_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/generate_data_model.py` — NOT invoked by the run-book
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
    - `code/ingestion/fetcher.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/reference_validator.py` — NOT invoked by the run-book
    - `code/run_ingestion.py` — NOT invoked by the run-book
    - `code/task_t010d_generate_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/task_t015b_stimulus_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
