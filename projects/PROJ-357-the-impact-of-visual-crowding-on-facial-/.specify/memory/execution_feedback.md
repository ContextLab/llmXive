# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…"store_true", help="Load mock data if real data is missing"…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Unit-test helper to generate a small synthetic pilot dataset.  This scr…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…2 ) -> None:     """     Generate a small synthetic pilot dataset for unit t…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic pilot sample: {n_participants} partic…”
- code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate a small synthetic pilot dataset for unit t…”
- code/analysis/run_pilot.py: synthetic/fake INPUT data not authorized by the spec — “…(T014). 2. Invoking the synthetic data generator (T025) to crea…”
- code/analysis/run_pilot.py: synthetic/fake INPUT data not authorized by the spec — “…ts as the entry point to generate the raw synthetic response data required f…”
- code/analysis/run_pilot.py: synthetic/fake INPUT data not authorized by the spec — “…p="Directory to save raw synthetic data"     )     args = parser…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/utils/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…"store_true", help="Load mock data if real data is missing"…”; code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Unit-test helper to generate a small synthetic pilot dataset.  This scr…”; code/analysis/generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…2 ) -> None:     """     Generate a small synthetic pilot dataset for unit t…”; 7 command(s) failed: python code/run_full_pipeline.py (rc=1); python code/utils/download.py (rc=1); python code/utils/frame_extractor.py (rc=1); 5 declared deliverable(s) absent: data/interim/raw_pilot_responses.csv; data/processed/clutter_metrics.csv; data/processed/human_judgments_aggregates.csv

## Failing / missing run-book commands

- python code/run_full_pipeline.py -> rc=1
 /home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/analysis/validation_report.py
2026-10-09 07:26:24,621 - INFO - Starting validation report generation
2026-10-09 07:26:24,621 - ERROR - File error: Metrics file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/data/processed/clutter_metrics.csv. Run code/utils/clutter_metrics.py first to generate this file.
2026-10-09 07:26:24,733 - ERROR - Step 'Generate validation report' failed with return code 1
2026-10-09 07:26:24,734 - ERROR - Pipeline completed with 9 failures:
2026-10-09 07:26:24,734 - ERROR -   - Download RAVDESS dataset
2026-10-09 07:26:24,734 - ERROR -   - Extract frames from videos
2026-10-09 07:26:24,734 - ERROR -   - Validate manifest completeness
2026-10-09 07:26:24,734 - ERROR -   - Compute clutter metrics
2026-10-09 07:26:24,734 - ERROR -   - Aggregate human judgments
2026-10-09 07:26:24,734 - ERROR -   - Fit GLMM model
2026-10-09 07:26:24,734 - ERROR -   - Write regression results
2026-10-09 07:26:24,734 - ERROR -   - Generate associational report
2026-10-09 07:26:24,734 - ERROR -   - Generate validation report

- python code/utils/download.py -> rc=1
--- RAVDESS Dataset Downloader ---
Initializing download for dataset: parlance/RAVDESS
Verified URL source: parlance/RAVDESS
Target directory: /home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/data/raw
ERROR: Failed to fetch dataset parlance/RAVDESS: Dataset 'parlance/RAVDESS' doesn't exist on the Hub or cannot be accessed.
Download process failed: Dataset 'parlance/RAVDESS' doesn't exist on the Hub or cannot be accessed.

`trust_remote_code` is not supported anymore.
Please check that the Hugging Face dataset 'parlance/RAVDESS' isn't based on a loading script and remove `trust_remote_code`.
If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.

- python code/utils/frame_extractor.py -> rc=1

2026-10-09 07:26:25,705 - __main__ - INFO - Starting frame extraction from RAVDESS dataset
2026-10-09 07:26:25,705 - __main__ - INFO - Dataset directory: data/raw/RAVDESS
2026-10-09 07:26:25,705 - __main__ - INFO - Output directory: data/raw/frames
2026-10-09 07:26:25,706 - __main__ - INFO - Frame interval: 30
2026-10-09 07:26:25,706 - __main__ - ERROR - Dataset directory not found: data/raw/RAVDESS
2026-10-09 07:26:25,706 - __main__ - ERROR - Please run download.py first to fetch the RAVDESS dataset

- python code/utils/clutter_metrics.py -> rc=1
2026-10-09 07:26:26,265 - __main__ - INFO - Starting clutter metrics computation

ERROR:root:Error during clutter metrics computation: Manifest must be a list, got <class 'dict'>
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/clutter_metrics.py", line 538, in main
    metrics_path = compute_clutter_metrics(
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/code/utils/clutter_metrics.py", line 377, in compute_clutter_metrics
    raise ValueError(f"Manifest must be a list, got {type(full_manifest)}")
ValueError: Manifest must be a list, got <class 'dict'>

- python code/analysis/run_pilot.py -> rc=1

2026-10-09 07:26:26,375 - __main__ - INFO - Initializing pilot execution with seed=42
2026-10-09 07:26:26,375 - __main__ - INFO - Loading stimuli manifest from data/interim/stimuli_manifest.json
2026-10-09 07:26:26,375 - __main__ - ERROR - Manifest is empty. Cannot run pilot.

- python code/analysis/glmm_model.py -> rc=1

2026-10-09 07:26:26,729 - ERROR - Data file not found: Required data files not found. Run data_loader and clutter_metrics first.

- python code/analysis/reporting.py -> rc=1

2026-10-09 07:26:26,824 - ERROR - Error: Regression results not found at data/processed/regression_results.json
2026-10-09 07:26:26,824 - ERROR - Cannot generate report without regression results or model config.


## Declared deliverables still missing

- data/interim/raw_pilot_responses.csv
- data/processed/clutter_metrics.csv
- data/processed/human_judgments_aggregates.csv
- data/processed/regression_results.json
- data/processed/validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/raw_pilot_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_loader.py` — NOT invoked by the run-book
    - `code/analysis/pilot_protocol.py` — NOT invoked by the run-book
    - `code/analysis/validate_human_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/raw_pilot_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/clutter_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/glmm_model.py` — IS a run-book command
    - `code/analysis/validation_report.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — IS a run-book command
    - `code/utils/clutter_metrics.py` — IS a run-book command
    - `code/utils/hygiene.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clutter_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/human_judgments_aggregates.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/data_loader.py` — NOT invoked by the run-book
    - `code/analysis/glmm_model.py` — IS a run-book command
    - `code/analysis/reporting.py` — IS a run-book command
    - `code/utils/hygiene.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/human_judgments_aggregates.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/glmm_model.py` — IS a run-book command
    - `code/analysis/reporting.py` — IS a run-book command
    - `code/analysis/write_model_config.py` — NOT invoked by the run-book
    - `code/analysis/write_regression_results.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/regression_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation_report.py` — NOT invoked by the run-book
    - `code/run_full_pipeline.py` — IS a run-book command
    - `code/utils/clutter_metrics.py` — IS a run-book command
    - `code/utils/manifest_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
