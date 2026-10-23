# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aFrame:     """     Load simulated student data from CSV.      Args:…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with simulated student records.      Raises:         Fi…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…ileNotFoundError: If the simulated data file does not exist.…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aise FileNotFoundError(f"Simulated data file not found at: {file…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading simulated student data from: {file_path}")…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…raise ValueError(f"Simulated data missing required columns…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “….info(f"Loaded {len(df)} simulated student records")     return df  def val…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Merge real and simulated datasets.      Args:         real…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 40 fabricated/simulated-result signal(s) — results are not real measurements: code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aFrame:     """     Load simulated student data from CSV.      Args:…”; code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with simulated student records.      Raises:         Fi…”; code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…ileNotFoundError: If the simulated data file does not exist.…”; 10 run-book script(s) missing (plan/impl path mismatch): python code/data/download_assistments.py; python code/data/download_khan.py   # **MANDATORY**: aborts if no verified URL or timeout; python code/tools/validate_pilot.py   # checks against contracts/pilot_data.schema.yaml; 4 command(s) failed: python code/tools/reference_validator.py --threshold 0.8 (rc=1); python code/download/unify_datasets.py (rc=1); python code/download/validate_unified_schema.py (rc=1); 3 declared deliverable(s) absent: data/pilot/real_pilot_data.csv; data/raw/assistments.csv; data/raw/khan_academy.csv

## Failing / missing run-book commands

- python code/tools/reference_validator.py --threshold 0.8 -> rc=1

2026-10-23 23:25:39,006 ERROR __main__: Failed to fetch URL https://huggingface.co/datasets/khanacademy/math: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/khanacademy/math
2026-10-23 23:25:39,006 ERROR __main__: ERROR: URL validation failed for https://huggingface.co/datasets/khanacademy/math

- python code/data/download_assistments.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/data/download_assistments.py': [Errno 2] No such file or directory

- python code/data/download_khan.py   # **MANDATORY**: aborts if no verified URL or timeout -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/data/download_khan.py': [Errno 2] No such file or directory

- python code/download/unify_datasets.py -> rc=1
2026-10-23 23:25:39,123 - INFO - Starting dataset unification process...
2026-10-23 23:25:39,124 - ERROR - Source file not found: data/raw/assistments.csv
2026-10-23 23:25:39,124 - ERROR - Dataset unification failed. Aborting.


- python code/download/validate_unified_schema.py -> rc=1
2026-10-23 23:25:39,167 - INFO - Starting schema validation for: data/raw/unified_problems.csv
2026-10-23 23:25:39,167 - INFO - Using schema: contracts/problem.schema.yaml
2026-10-23 23:25:39,167 - ERROR - Unified data file not found at: data/raw/unified_problems.csv
2026-10-23 23:25:39,167 - ERROR - Dependency T012e (unify_datasets.py) must run successfully first.
2026-10-23 23:25:39,167 - ERROR - Schema validation failed.


- python code/tools/validate_pilot.py   # checks against contracts/pilot_data.schema.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/tools/validate_pilot.py': [Errno 2] No such file or directory

- python code/simulation/pilot_calibrator.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/simulation/pilot_calibrator.py': [Errno 2] No such file or directory

- python code/generation/batch_generate.py  --conditions neural symbolic neuro_symbolic  --timeout $(python -c "import yaml,sys; print(yaml.safe_load(open('code/config.yaml'))['explanation_timeout_seconds'])") -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/generation/batch_generate.py': [Errno 2] No such file or directory

- python code/simulation/present_to_simulator.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/simulation/present_to_simulator.py': [Errno 2] No such file or directory

- python code/simulate/run_simulation.py -> rc=1
2026-10-23 23:25:39,705 - __main__ - ERROR - Calibration check failed. Cannot proceed with simulation.


- python code/tools/validate_interactions.py   # checks against contracts/interaction_log.schema.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/tools/validate_interactions.py': [Errno 2] No such file or directory

- python code/analysis/merge_data.py   # creates merged_interaction_logs.csv (adds data_source) -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/analysis/merge_data.py': [Errno 2] No such file or directory

- python code/analysis/exploratory_regression.py   # runs mixed‑effects model on combined data for diagnostics only -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/analysis/exploratory_regression.py': [Errno 2] No such file or directory

- python code/analysis/regression_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-559-neuro-symbolic-learning-networks-bridgin/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/analysis/regression_analysis.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/pilot/real_pilot_data.csv
- data/raw/assistments.csv
- data/raw/khan_academy.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/pilot/real_pilot_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pilot/ingest_human_pilot.py` — NOT invoked by the run-book
    - `code/pilot/synthetic_pilot_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/pilot/real_pilot_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/assistments.csv` is declared but was NOT written. Scripts referencing it:
    - `code/docs/generate_scope_statement.py` — NOT invoked by the run-book
    - `code/download/__init__.py` — NOT invoked by the run-book
    - `code/download/fetch_assistments.py` — NOT invoked by the run-book
    - `code/download/fetch_datasets.py` — NOT invoked by the run-book
    - `code/download/run_fetcher.py` — NOT invoked by the run-book
    - `code/download/unify_datasets.py` — IS a run-book command
    - `code/download/validate_assistments_data.py` — NOT invoked by the run-book
    - `code/tests/integration/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/assistments.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/khan_academy.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download/fetch_datasets.py` — NOT invoked by the run-book
    - `code/download/fetch_khan_academy.py` — NOT invoked by the run-book
    - `code/download/unify_datasets.py` — IS a run-book command
    - `code/download/verify_timeout_handling_khan.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/khan_academy.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
