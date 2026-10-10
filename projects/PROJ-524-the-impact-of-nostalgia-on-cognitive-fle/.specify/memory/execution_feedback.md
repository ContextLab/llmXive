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

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic WCST (Wisconsin Card Sor…”; code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…e         DataFrame with synthetic WCST data.     """     np.random.s…”; code/task_t010d_generate_simulation.py: synthetic/fake INPUT data not authorized by the spec — “…(T010d)...")          # Generate synthetic data     df = generate_s…”; 12 command(s) failed: python code/main.py (rc=1); python code/task_t010d_generate_simulation.py (rc=1); python code/task_t012a_age_exclusion.py (rc=1); 12 declared deliverable(s) absent: data/processed/cleaned_age_filtered.csv; data/processed/cleaned_dataset_no_mmse.csv; data/processed/cleaned_score_filtered.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
line (T010c)...
2026-10-10 06:35:45,827 - llmXive - INFO - Running Age Exclusion (T012a)...
2026-10-10 06:35:46,240 - llmXive - ERROR - T012a failed: 2026-10-10 06:35:46,182 - T012a_AgeExclusion - INFO - Starting T012a: Age Exclusion
2026-10-10 06:35:46,182 - T012a_AgeExclusion - ERROR - Raw dataset not found at data/raw/raw_dataset.csv
2026-10-10 06:35:46,182 - T012a_AgeExclusion - ERROR - Data file missing: Raw dataset not found at data/raw/raw_dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 155, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 133, in main
    df_raw = load_raw_dataset(paths)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 44, in load_raw_dataset
    raise FileNotFoundError(f"Raw dataset not found at {input_path}")
FileNotFoundError: Raw dataset not found at data/raw/raw_dataset.csv


- python code/task_t010d_generate_simulation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t010d_generate_simulation.py", line 123, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t010d_generate_simulation.py", line 83, in main
    ensure_dirs()
TypeError: ensure_dirs() missing 1 required positional argument: 'config'

- python code/task_t012a_age_exclusion.py -> rc=1

2026-10-10 06:35:46,995 - T012a_AgeExclusion - INFO - Starting T012a: Age Exclusion
2026-10-10 06:35:46,995 - T012a_AgeExclusion - ERROR - Raw dataset not found at data/raw/raw_dataset.csv
2026-10-10 06:35:46,995 - T012a_AgeExclusion - ERROR - Data file missing: Raw dataset not found at data/raw/raw_dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 155, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 133, in main
    df_raw = load_raw_dataset(paths)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 44, in load_raw_dataset
    raise FileNotFoundError(f"Raw dataset not found at {input_path}")
FileNotFoundError: Raw dataset not found at data/raw/raw_dataset.csv

- python code/task_t012b_score_exclusion.py -> rc=1

2026-10-10 06:35:47,398 - ERROR - File not found: Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/data/processed/cleaned_age_filtered.csv

- python code/task_t012d_mmse_flag.py -> rc=1

2026-10-10 06:35:47,806 - llmXive - ERROR - Raw dataset not found at data/raw/raw_dataset.csv

- python code/task_t012e_mmse_exclusion.py -> rc=1

2026-10-10 06:35:48,211 - llmXive - INFO - Starting T012e: MMSE Exclusion and Robustness Prep
2026-10-10 06:35:48,211 - llmXive - ERROR - File not found: MMSE flag not found at /home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/data/processed/mmse_flag.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012e_mmse_exclusion.py", line 148, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012e_mmse_exclusion.py", line 109, in main
    has_mmse = load_mmse_flag(paths['mmse_flag_path'])
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012e_mmse_exclusion.py", line 48, in load_mmse_flag
    raise FileNotFoundError(f"MMSE flag not found at {path}")
FileNotFoundError: MMSE flag not found at /home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/data/processed/mmse_flag.json

- python code/task_t014a_create_cleaned_dataset.py -> rc=1

2026-10-10 06:35:48,623 - llmXive - INFO - Starting T014a: Generate Cleaned Dataset at 2026-10-10T06:35:48.623729
2026-10-10 06:35:48,623 - llmXive - WARNING - Exclusion log not found at data/processed/exclusion_log.json. Proceeding without it.
2026-10-10 06:35:48,623 - llmXive - WARNING - MMSE flag not found at data/processed/mmse_flag.json. Assuming MMSE filtering was not applied.
2026-10-10 06:35:48,624 - llmXive - INFO - MMSE filtering applied: False
2026-10-10 06:35:48,624 - llmXive - ERROR - Data not found: Input dataset not found at data/processed/cleaned_dataset.csv

- python code/task_t014b_validity_metrics.py -> rc=1

2026-10-10 06:35:49,034 - llmXive - INFO - Starting T014b: Validity Metrics Calculation
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t014b_validity_metrics.py", line 144, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t014b_validity_metrics.py", line 126, in main
    paths = get_config_paths()
            ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t014b_validity_metrics.py", line 25, in get_config_paths
    'raw_dataset': config['paths']['data_raw'] + '/raw_dataset.csv',
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'data_raw'

- python code/analysis.py -> rc=1

2026-10-10 06:35:50,075 - INFO - Starting statistical analysis (T018: Welch's t-test)
2026-10-10 06:35:50,075 - ERROR - Data Error: Cleaned dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/data/processed/final_cleaned_dataset.csv

- python code/task_t027b_mmse_robustness_analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t027b_mmse_robustness_analysis.py", line 14, in <module>
    from statsmodels.stats.power import t_ind_solve_power
ImportError: cannot import name 't_ind_solve_power' from 'statsmodels.stats.power' (/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/.venv/lib/python3.11/site-packages/statsmodels/stats/power.py)

- python code/generate_robustness_summary.py -> rc=1

2026-10-10 06:35:51,359 - INFO - Starting T053: Robustness Summary Report Generation
2026-10-10 06:35:51,359 - INFO - Loading primary report from data/results/primary_analysis_report.json
2026-10-10 06:35:51,359 - ERROR - Missing required input file: Required file not found: data/results/primary_analysis_report.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/generate_robustness_summary.py", line 239, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/generate_robustness_summary.py", line 201, in main
    primary_report = load_json_file(primary_report_path)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/generate_robustness_summary.py", line 28, in load_json_file
    raise FileNotFoundError(f"Required file not found: {path}")
FileNotFoundError: Required file not found: data/results/primary_analysis_report.json

- python -m pytest tests/integration/test_full_pipeline.py -v -> rc=1
(T012a)...
2026-10-10 06:35:52,046 - llmXive - ERROR - T012a failed: 2026-10-10 06:35:51,989 - T012a_AgeExclusion - INFO - Starting T012a: Age Exclusion
2026-10-10 06:35:51,989 - T012a_AgeExclusion - ERROR - Raw dataset not found at data/raw/raw_dataset.csv
2026-10-10 06:35:51,989 - T012a_AgeExclusion - ERROR - Data file missing: Raw dataset not found at data/raw/raw_dataset.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 155, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 133, in main
    df_raw = load_raw_dataset(paths)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/code/task_t012a_age_exclusion.py", line 44, in load_raw_dataset
    raise FileNotFoundError(f"Raw dataset not found at {input_path}")
FileNotFoundError: Raw dataset not found at data/raw/raw_dataset.csv
=============================== 1 error in 0.49s ===============================



## Declared deliverables still missing

- data/processed/cleaned_age_filtered.csv
- data/processed/cleaned_dataset_no_mmse.csv
- data/processed/cleaned_score_filtered.csv
- data/processed/exclusion_log.json
- data/processed/final_cleaned_dataset.csv
- data/processed/mmse_flag.json
- data/processed/validity_metrics.json
- data/raw/metadata.json
- data/raw/raw_dataset.csv
- data/results/robustness_report.json
- data/results/runtime_log.json
- data/results/sensitivity_comparison.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_age_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012a_age_exclusion.py` — IS a run-book command
    - `code/task_t012b_score_exclusion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_age_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_dataset_no_mmse.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_robustness_summary.py` — IS a run-book command
    - `code/task_t012e_mmse_exclusion.py` — IS a run-book command
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
    - `code/task_t027b_mmse_robustness_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset_no_mmse.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_score_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/task_t012b_score_exclusion.py` — IS a run-book command
    - `code/task_t012e_mmse_exclusion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_score_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
    - `code/ingestion/fetcher.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/task_t012c_generate_exclusion_log.py` — NOT invoked by the run-book
    - `code/task_t012d_mmse_exclusion.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_cleaned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/assumption_checks.py` — NOT invoked by the run-book
    - `code/task_t014a_create_cleaned_dataset.py` — IS a run-book command
    - `code/task_t021_power_analysis.py` — NOT invoked by the run-book
    - `code/task_t022_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_cleaned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mmse_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/task_t012d_mmse_flag.py` — IS a run-book command
    - `code/task_t012e_mmse_exclusion.py` — IS a run-book command
    - `code/task_t014a_create_cleaned_dataset.py` — IS a run-book command
    - `code/task_t014b_validity_metrics.py` — IS a run-book command
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/task_t027a_mmse_robustness_prep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mmse_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
    - `code/ingestion/validator.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/task_t014b_validity_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/validity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/generate_data_model.py` — NOT invoked by the run-book
    - `code/ingestion/__init__.py` — NOT invoked by the run-book
    - `code/ingestion/fetcher.py` — NOT invoked by the run-book
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/reference_validator.py` — NOT invoked by the run-book
    - `code/run_ingestion.py` — NOT invoked by the run-book
    - `code/task_t010d_generate_simulation.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/raw_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/run_ingestion.py` — NOT invoked by the run-book
    - `code/run_t010b_fetch.py` — NOT invoked by the run-book
    - `code/task_t010d_generate_simulation.py` — IS a run-book command
    - `code/task_t012a_age_exclusion.py` — IS a run-book command
    - `code/task_t012d_mmse_flag.py` — IS a run-book command
    - `code/task_t014b_validity_metrics.py` — IS a run-book command
    - `code/task_t015a_generate_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/raw_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_robustness_summary.py` — IS a run-book command
    - `code/task_t027_robustness_check.py` — NOT invoked by the run-book
    - `code/task_t027b_mmse_robustness_analysis.py` — IS a run-book command
    - `code/task_t027c_compare_robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/task_t015b_stimulus_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_robustness_summary.py` — IS a run-book command
    - `code/task_t027c_compare_robustness.py` — NOT invoked by the run-book
    - `code/task_t028_sensitivity_report.py` — NOT invoked by the run-book
    - `code/task_t030_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
