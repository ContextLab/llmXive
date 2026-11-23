# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206)
- code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…...")          # Prepare dummy input based on sample data str…”
- code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…al()          # Create a dummy input for tracing         # Sh…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/model/estimator_train.py`
  - script usage: `estimator_train.py [-h] --input INPUT [--output OUTPUT]`
  - argparse error: `estimator_train.py: error: the following arguments are required: --input`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/fetch_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/inference/hybrid_sim.py: metric `latency_reduction` assigned from an RNG draw (line 206); code/models/gru_estimator.py: synthetic/fake INPUT data not authorized by the spec — “…n{model}")          # 3. Dummy Data Generation for Verificat…”; code/utils/inference_optimizer.py: synthetic/fake INPUT data not authorized by the spec — “…...")          # Prepare dummy input based on sample data str…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/utils/state_manager.py --update; 7 command(s) failed: python code/data/fetch_data.py (rc=1); python code/data/extract_turn_taking.py (rc=1); python code/model/estimator_train.py (rc=2); 7 declared deliverable(s) absent: data/metrics/power_analysis_final.json; data/metrics/theoretical_defaults.json; data/processed/counterfactual_indices.json

## Failing / missing run-book commands

- python code/data/fetch_data.py -> rc=1
in__ - INFO - Starting data fetch process...
2026-10-10 03:22:25,148 - data.validate_logs - INFO - Logs directory does not exist: /home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/data/raw/wan_streamer_logs
2026-10-10 03:22:25,148 - __main__ - INFO - Wan-Streamer logs not found or forced. Attempting to fetch VoxCeleb2...
2026-10-10 03:22:25,148 - data.validate_logs - INFO - Fetching VoxCeleb2 dataset (revision=main)...
2026-10-10 03:22:25,249 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/agent-harnesses "HTTP/1.1 200 OK"
2026-10-10 03:22:25,289 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/voxceleb2/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-10 03:22:25,290 - data.validate_logs - ERROR - Failed to fetch VoxCeleb2 dataset: Dataset 'voxceleb2' doesn't exist on the Hub or cannot be accessed.
2026-10-10 03:22:25,290 - __main__ - ERROR - CRITICAL: Failed to fetch data. No real source available. Error: Could not fetch canonical VoxCeleb2 dataset: Dataset 'voxceleb2' doesn't exist on the Hub or cannot be accessed.
2026-10-10 03:22:25,290 - __main__ - ERROR - Aborting. Do not fabricate data.

- python code/data/extract_turn_taking.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/data/extract_turn_taking.py", line 25, in <module>
    from code.data.verify_event_counts import main as verify_events_main
ModuleNotFoundError: No module named 'code.data.verify_event_counts'

- python code/model/estimator_train.py -> rc=2

usage: estimator_train.py [-h] --input INPUT [--output OUTPUT]
estimator_train.py: error: the following arguments are required: --input

- python code/model/hybrid_simulate.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/model/hybrid_simulate.py", line 25, in <module>
    from metrics.baseline_comparison import run_baseline_comparison
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/__init__.py", line 4, in <module>
    from .fid_stability_corr import calculate_fid_stability_correlation
ModuleNotFoundError: No module named 'metrics.fid_stability_corr'

- python code/metrics/calculate_fid_stability.py -> rc=1
2026-10-10 03:22:30,752 - INFO - Starting FID Stability Correlation Calculation (T085)...
2026-10-10 03:22:30,752 - ERROR - Missing required metrics files (Hybrid or Baseline).
2026-10-10 03:22:30,752 - ERROR - Ensure T060 (Ground Truth) and T050c (Metrics Computation) have run successfully.


- python code/metrics/statistical_tests.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/statistical_tests.py", line 33, in <module>
    from metrics.tost_equivalence import load_hybrid_output as load_hybrid_for_tost, load_baseline_metrics, perform_tost_test
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/metrics/__init__.py", line 4, in <module>
    from .fid_stability_corr import calculate_fid_stability_correlation
ModuleNotFoundError: No module named 'metrics.fid_stability_corr'

- python code/utils/state_manager.py --update -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/code/utils/state_manager.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
dataset_schema.py::TestDatasetSchema::test_required_columns_present
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_column_data_types
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_no_null_values
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_sample_size_minimum
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_event_types_valid
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_latent_delta_non_negative
FAILED tests/contract/test_dataset_schema.py::TestDatasetSchema::test_timestamp_monotonicity_within_sessions
FAILED tests/contract/test_hybrid_output_schema.py::test_hybrid_output_file_exists
ERROR tests/contract/test_model_output_schema.py::test_output_shape - TypeErr...
ERROR tests/contract/test_model_output_schema.py::test_output_dtype - TypeErr...
ERROR tests/contract/test_model_output_schema.py::test_uncertainty_score_range
ERROR tests/contract/test_model_output_schema.py::test_delta_magnitude_non_negative
ERROR tests/contract/test_model_output_schema.py::test_output_consistency_with_schema
============== 10 failed, 4 passed, 5 skipped, 5 errors in 1.16s ===============



## Declared deliverables still missing

- data/metrics/power_analysis_final.json
- data/metrics/theoretical_defaults.json
- data/processed/counterfactual_indices.json
- data/processed/filtered.parquet
- data/processed/raw_extract.parquet
- data/processed/sampled_dataset.parquet
- data/processed/turn_taking_dataset.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/power_analysis_final.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/power_analysis_final.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/power_analysis_final.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/metrics/theoretical_defaults.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_defaults.py` — NOT invoked by the run-book
    - `code/data/power_analysis_initial.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/theoretical_defaults.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/counterfactual_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/inference/fallback_handler.py` — NOT invoked by the run-book
    - `code/inference/fallback_logic_handler.py` — NOT invoked by the run-book
    - `code/inference/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/inference/hybrid_sim.py` — NOT invoked by the run-book
    - `code/inference/precedence_rule.py` — NOT invoked by the run-book
    - `code/model/hybrid_simulate.py` — IS a run-book command
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/counterfactual_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/log_event_counts.py` — NOT invoked by the run-book
    - `code/data/power_analysis_initial.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/utils/validators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_extract.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_latents.py` — NOT invoked by the run-book
    - `code/data/generate_power_analysis.py` — NOT invoked by the run-book
    - `code/tasks/calibrate_thresholds.py` — NOT invoked by the run-book
    - `code/tasks/power_analysis.py` — NOT invoked by the run-book
    - `code/tasks/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/tasks/validate_thresholds.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_extract.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sampled_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_turn_taking.py` — IS a run-book command
    - `code/data/generate_counterfactual_indices.py` — NOT invoked by the run-book
    - `code/data/generate_defaults.py` — NOT invoked by the run-book
    - `code/data/power_analysis_final.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/validate_processed.py` — NOT invoked by the run-book
    - `code/inference/fallback_handler.py` — NOT invoked by the run-book
    - `code/inference/fallback_logic_handler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sampled_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/turn_taking_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_turn_taking.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/turn_taking_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
