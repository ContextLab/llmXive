# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”
- code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”; code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”; 6 command(s) failed: python -m src.cli run  --mode single  --N 1000  --theta 2.5  --k 1  --pattern diagonal  --seed 42 (rc=1); python -m src.cli sweep  --N 2000  --theta-grid 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2.0 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8 2.9 3.0  --k 1 2 5  --patterns diagonal block-sparse random-sparse  --iterations 500  --seed-start 1000 (rc=1); python -m src.cli sensitivity  --N 1500  --theta 1.5  --k 2  --pattern random-sparse  --densities 0.05 0.1 0.2 0.3 0.4 0.5  --iterations 500  --seed-start 5000 (rc=1); 8 declared deliverable(s) absent: data/figures/outlier_probability_vs_theta.png; data/processed/convergence_data.json; data/processed/mc_results.csv

## Failing / missing run-book commands

- python -m src.cli run  --mode single  --N 1000  --theta 2.5  --k 1  --pattern diagonal  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python: Error while finding module specification for 'src.cli' (ModuleNotFoundError: No module named 'src')

- python -m src.cli sweep  --N 2000  --theta-grid 0.5 0.6 0.7 0.8 0.9 1.0 1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9 2.0 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8 2.9 3.0  --k 1 2 5  --patterns diagonal block-sparse random-sparse  --iterations 500  --seed-start 1000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python: Error while finding module specification for 'src.cli' (ModuleNotFoundError: No module named 'src')

- python -m src.cli sensitivity  --N 1500  --theta 1.5  --k 2  --pattern random-sparse  --densities 0.05 0.1 0.2 0.3 0.4 0.5  --iterations 500  --seed-start 5000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python: Error while finding module specification for 'src.cli' (ModuleNotFoundError: No module named 'src')

- python -m src.cli finite_size  --Ns 500 1000 1500 2000  --theta 1.5  --k 1  --pattern diagonal  --iterations 500  --seed-start 8000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python: Error while finding module specification for 'src.cli' (ModuleNotFoundError: No module named 'src')

- python -m pytest tests/contract/test_schemas.py -> rc=1
ation_time_ms': 63.30494999997427, 'eigenvalues': [{'deviation': 0.851642355090902, 'eigenvalue_ind...': False, 'run_id': 'def348d2-beec-4836-b994-d94222ca2dac', ...}, ...], 'empirical_bulk_edge': 2.0003950533337433, ...}
schema = {'$schema': 'http://json-schema.org/draft-07/schema#', 'description': 'Record of a single simulation run: parameters (...ect'}, 'minItems': 1, 'type': 'array'}, ...}, 'required': ['run_id', 'timestamp', 'N', 'seed', 'theta', 'k', ...], ...}
label = 'single_run_results.json'

    def _validate_against(data, schema, label):
        errors = sorted(Draft7Validator(schema).iter_errors(data), key=str)
        if errors:
            msgs = "; ".join(e.message for e in errors[:5])
>           raise AssertionError(f"{label} failed schema validation: {msgs}")
E           AssertionError: single_run_results.json failed schema validation: None is not of type 'number', 'string'

tests/contract/test_schemas.py:76: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_schemas.py::test_processed_json_files - AssertionE...
========================= 1 failed, 2 passed in 0.07s ==========================


- python -m pytest tests/integration/test_t001.py -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
configfile: pyproject.toml
plugins: platformdirs-4.13.3
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_t001.py



## Declared deliverables still missing

- data/figures/outlier_probability_vs_theta.png
- data/processed/convergence_data.json
- data/processed/mc_results.csv
- data/processed/sensitivity_density_sweep.csv
- data/processed/sensitivity_metadata.json
- data/processed/sensitivity_variation.csv
- data/processed/threshold_statistical.json
- data/processed/threshold_sweep_results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/figures/outlier_probability_vs_theta.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plot_outlier_probability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/figures/outlier_probability_vs_theta.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/convergence_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_sweep.py` — NOT invoked by the run-book
    - `code/analysis/threshold_sweep_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/mc_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_thresholds.py` — NOT invoked by the run-book
    - `code/analysis/apply_outlier_rule.py` — NOT invoked by the run-book
    - `code/analysis/fit_utils.py` — NOT invoked by the run-book
    - `code/analysis/monte_carlo_runner.py` — NOT invoked by the run-book
    - `code/analysis/threshold_analysis_runner.py` — NOT invoked by the run-book
    - `code/analysis/threshold_fit.py` — NOT invoked by the run-book
    - `code/analysis/threshold_identification_raw.py` — NOT invoked by the run-book
    - `code/analysis/threshold_sweep.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/mc_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_density_sweep.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_density_sweep.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_metadata_recorder.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_variation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_density_sweep.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_metadata_recorder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_variation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_variation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_variation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_statistical.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_thresholds.py` — NOT invoked by the run-book
    - `code/analysis/threshold_fit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_statistical.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_sweep_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_thresholds.py` — NOT invoked by the run-book
    - `code/analysis/threshold_sweep_aggregator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_sweep_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
