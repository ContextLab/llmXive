# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/salience/generate_maps.py: synthetic/fake INPUT data not authorized by the spec — “…------------ # Helper to generate a tiny synthetic stimulus set when none e…”
- code/utils/create_readme.py: synthetic/fake INPUT data not authorized by the spec — “…a source is unreachable. Synthetic data fallbacks are strictly f…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/salience/generate_maps.py: synthetic/fake INPUT data not authorized by the spec — “…------------ # Helper to generate a tiny synthetic stimulus set when none e…”; code/utils/create_readme.py: synthetic/fake INPUT data not authorized by the spec — “…a source is unreachable. Synthetic data fallbacks are strictly f…”; 2 command(s) failed: python -m code.ingestion.verify_data (rc=1); python -m pytest tests/ -q (rc=2); 9 declared deliverable(s) absent: data/interim/detection_metadata.json; data/interim/fixations.csv; data/interim/flagged_images.csv

## Failing / missing run-book commands

- python -m code.ingestion.verify_data -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-471-the-influence-of-visual-salience-on-atte/code/ingestion/verify_data.py", line 157, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-471-the-influence-of-visual-salience-on-atte/code/ingestion/verify_data.py", line 91, in main
    raise RuntimeError(
RuntimeError: DATA_MISSING_001: ds003123 incomplete (no sub‑* participant folders)

- python -m pytest tests/ -q -> rc=2
1/site-packages/torch/nn/modules/transformer.py:20
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-471-the-influence-of-visual-salience-on-atte/lib/python3.11/site-packages/torch/nn/modules/transformer.py:20: UserWarning: Failed to initialize NumPy: _ARRAY_API not found (Triggered internally at ../torch/csrc/utils/tensor_numpy.cpp:84.)
    device: torch.device = torch.device(torch._C._get_default_device()),  # torch.device('cpu'),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py - RuntimeError: The `huggingface_hub...
ERROR tests/test_alignment.py - json.decoder.JSONDecodeError: Expecting value...
ERROR tests/test_download_success.py - RuntimeError: The `huggingface_hub` li...
ERROR tests/unit/test_add_disclaimer.py
ERROR tests/unit/test_download_data.py - RuntimeError: The `huggingface_hub` ...
ERROR tests/unit/test_salience_batcher.py
ERROR tests/unit/test_salience_gen.py
ERROR tests/unit/test_update_spec_governance.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 8 errors in 3.35s



## Declared deliverables still missing

- data/interim/detection_metadata.json
- data/interim/fixations.csv
- data/interim/flagged_images.csv
- data/interim/low_level_features.json
- data/interim/salience_metadata.json
- data/processed/aligned_data.csv
- data/processed/alignment_stats.json
- data/processed/results.json
- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/detection_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/eye_tracking/segment_roi.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/detection_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/fixations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/align_data.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/eye_tracking/parse_fixations.py` — NOT invoked by the run-book
    - `code/processing/eye_tracking.py` — NOT invoked by the run-book
    - `code/processing/missing_fixation_handler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/fixations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/flagged_images.csv` is declared but was NOT written. Scripts referencing it:
    - `code/eye_tracking/segment_roi.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/flagged_images.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/low_level_features.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/align_data.py` — NOT invoked by the run-book
    - `code/analysis/feature_gen.py` — NOT invoked by the run-book
    - `code/analysis/vif_calc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/low_level_features.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/salience_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/salience/generate_maps.py` — NOT invoked by the run-book
    - `code/validation/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/salience_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/align_data.py` — NOT invoked by the run-book
    - `code/analysis/collinearity_and_modeling.py` — NOT invoked by the run-book
    - `code/analysis/lmm_fit.py` — NOT invoked by the run-book
    - `code/processing/alignment.py` — NOT invoked by the run-book
    - `code/processing/alignment_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alignment_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/align_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/collinearity_and_modeling.py` — NOT invoked by the run-book
    - `code/analysis/feature_gen.py` — NOT invoked by the run-book
    - `code/analysis/lmm_fit.py` — NOT invoked by the run-book
    - `code/analysis/null_result_logger.py` — NOT invoked by the run-book
    - `code/analysis/plot_sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/robustness.py` — NOT invoked by the run-book
    - `code/analysis/vif_calc.py` — NOT invoked by the run-book
    - `code/analysis/vif_interpretation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion/download_data.py` — NOT invoked by the run-book
    - `code/ingestion/verify_data.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
