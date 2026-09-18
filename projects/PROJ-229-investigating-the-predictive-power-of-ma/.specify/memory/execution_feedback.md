# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/compute_descriptors.py: synthetic/fake INPUT data not authorized by the spec — “…main__":     # Test with mock data     df = pd.DataFrame({'…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…API key provided. Using mock data.")         # Return mock…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…data.")         # Return mock data for testing         retu…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…# For now, we return mock data         logger.info("Fet…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…")         # Fallback to mock data         logger.warning("…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…warning("Falling back to mock data.")         return _gener…”
- code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…taFrame:     """Generate mock data for testing."""     logg…”
- code/data/generate_processed_checksums.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data. """  import logging fro…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/data/compute_descriptors.py: synthetic/fake INPUT data not authorized by the spec — “…main__":     # Test with mock data     df = pd.DataFrame({'…”; code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…API key provided. Using mock data.")         # Return mock…”; code/data/fetch_materials_project.py: synthetic/fake INPUT data not authorized by the spec — “…data.")         # Return mock data for testing         retu…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/models/train_baselines.py; python code/validate/validate_external.py; python code/validate/sensitivity_analysis.py; 4 command(s) failed: python code/data/fetch_materials.py (rc=1); python code/data/compute_descriptors.py (rc=1); python code/models/train_symbolic.py (rc=1); 11 declared deliverable(s) absent: data/external/literature_pcms_mapped.csv; data/external/literature_pcms_raw.csv; data/models/shap_summary.json

## Failing / missing run-book commands

- python code/data/fetch_materials.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/data/fetch_materials.py", line 8, in <module>
    from utils.logger import get_pipeline_logger, log_error, log_warning, log_info
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/utils/__init__.py", line 4, in <module>
    from .logger import setup_logger, get_pipeline_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/utils/logger.py", line 9, in <module>
    from config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/data/compute_descriptors.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/data/compute_descriptors.py", line 15, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/models/train_baselines.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/models/train_baselines.py': [Errno 2] No such file or directory
- python code/models/train_symbolic.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/models/train_symbolic.py", line 18, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/validate/validate_external.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/validate/validate_external.py': [Errno 2] No such file or directory
- python code/validate/sensitivity_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/validate/sensitivity_analysis.py': [Errno 2] No such file or directory
- python code/main.py --generate-report -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/main.py", line 28, in <module>
    from utils.logger import get_pipeline_logger, log_error, log_info
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/utils/__init__.py", line 4, in <module>
    from .logger import setup_logger, get_pipeline_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/utils/logger.py", line 9, in <module>
    from config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-229-investigating-the-predictive-power-of-ma/code/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/external/literature_pcms_mapped.csv
- data/external/literature_pcms_raw.csv
- data/models/shap_summary.json
- data/raw/materials_project_data.json
- data/raw/nist_data.json
- data/results/baseline_verification.json
- data/results/correlation_report.json
- data/results/data_manifest.json
- data/results/model_comparison.json
- data/results/target_decision.json
- data/results/validation_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/external/literature_pcms_mapped.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/map_literature_pcms.py` — NOT invoked by the run-book
    - `code/data/map_literature_pcm.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/external/literature_pcms_mapped.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/external/literature_pcms_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fetch_literature_pcm.py` — NOT invoked by the run-book
    - `code/data/map_literature_pcms.py` — NOT invoked by the run-book
    - `code/data/map_literature_pcm.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/external/literature_pcms_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/shap_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/train_shap_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/shap_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/materials_project_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/data/fetch_materials.py` — IS a run-book command
    - `code/data/fetch_nist_data.py` — NOT invoked by the run-book
    - `code/data/run_fetch_materials.py` — NOT invoked by the run-book
    - `code/data/generate_data_manifest.py` — NOT invoked by the run-book
    - `code/data/target_consistency_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/materials_project_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/nist_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/run_fetch_nist_data.py` — NOT invoked by the run-book
    - `code/data/fetch_nist_data.py` — NOT invoked by the run-book
    - `code/data/generate_data_manifest.py` — NOT invoked by the run-book
    - `code/data/target_consistency_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/nist_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/verify_baseline_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/data_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_data_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/evaluate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/target_decision.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/fetch_nist_data.py` — NOT invoked by the run-book
    - `code/data/generate_data_manifest.py` — NOT invoked by the run-book
    - `code/data/map_literature_pcms.py` — NOT invoked by the run-book
    - `code/data/target_consistency_check.py` — NOT invoked by the run-book
    - `code/data/run_target_consistency_check.py` — NOT invoked by the run-book
    - `code/utils/__init__.py` — NOT invoked by the run-book
    - `code/utils/schema_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/target_decision.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/validation_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate/generate_validation_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/validation_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
