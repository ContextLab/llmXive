# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…""     Validate that the simulated dataset size matches the MDES as…”
- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…r of participants in the simulated dataset.              Returns:…”
- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…# Note: This requires a simulated dataset to have been generated f…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…""Load MFQ data from the generated synthetic dataset."""     full_pat…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…al Stories data from the generated synthetic dataset."""     full_pat…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…nteraction logs from the generated synthetic dataset."""     full_pat…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…the simulation pipeline. Generates synthetic data, preprocesses it, a…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…ine")          # Step 1: Generate synthetic MFQ data     log_pipelin…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 23 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…""     Validate that the simulated dataset size matches the MDES as…”; code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…r of participants in the simulated dataset.              Returns:…”; code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…# Note: This requires a simulated dataset to have been generated f…”; 7 run-book script(s) missing (plan/impl path mismatch): python code/fetch_real_data.py --mode real; python code/simulate_vr.py --salience low --salience high --n-samples 1000; python code/preprocessing.py; 4 command(s) failed: python code/data/fetch_real_vr.py --mode real (rc=1); python code/models/bayesian_model.py (rc=1); python code/analysis/model_comparison.py (rc=1); 10 declared deliverable(s) absent: data/processed/merged_data.csv; data/processed/merged_simulation.csv; data/processed/synthetic_logs.csv

## Failing / missing run-book commands

- python -c "import os; assert os.path.exists('specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md') and 'APPROVED' in open('specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md').read(), 'T095: Amendment not found or not approved'" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
AssertionError: T095: Amendment not found or not approved

- python code/data/fetch_real_vr.py --mode real -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/fetch_real_vr.py", line 23, in <module>
    from datasets import load_dataset, DatasetDict  # huggingface_hub datasets library
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'datasets'

- python code/fetch_real_data.py --mode real -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/fetch_real_data.py': [Errno 2] No such file or directory

- python code/simulate_vr.py --salience low --salience high --n-samples 1000 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/simulate_vr.py': [Errno 2] No such file or directory

- python code/preprocessing.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/preprocessing.py': [Errno 2] No such file or directory

- python code/models/bayesian_model.py -> rc=1
n3.11/site-packages/arviz/__init__.py:50: FutureWarning: 
ArviZ is undergoing a major refactor to improve flexibility and extensibility while maintaining a user-friendly interface.
Some upcoming changes may be backward incompatible.
For details and migration guidance, visit: https://python.arviz.org/en/latest/user_guide/migration_guide.html
  warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian_model.py", line 20, in <module>
    from pymc import Model, InferenceData
ImportError: cannot import name 'InferenceData' from 'pymc' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/lib/python3.11/site-packages/pymc/__init__.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian_model.py", line 24, in <module>
    raise ImportError("PyMC5 is required. Install via: pip install pymc==5.12.0")
ImportError: PyMC5 is required. Install via: pip install pymc==5.12.0

- python code/analysis/model_comparison.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/model_comparison.py", line 42, in <module>
    from code.utils.logging import get_logger, log_operation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/__init__.py", line 18, in <module>
    from .hashing import (
ImportError: cannot import name 'calculate_sha256' from 'code.utils.hashing' (/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/hashing.py)

- python code/analysis/sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/sensitivity.py': [Errno 2] No such file or directory

- python code/analysis/bonferroni.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/analysis/bonferroni.py': [Errno 2] No such file or directory

- python code/simulate_vr.py --salience low --salience high --n-samples 1000 --mode full-synthetic -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/simulate_vr.py': [Errno 2] No such file or directory

- python code/preprocessing.py --mode synthetic -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/preprocessing.py': [Errno 2] No such file or directory

- python code/models/bayesian_model.py --mode synthetic -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian_model.py", line 20, in <module>
    from pymc import Model, InferenceData
ImportError: cannot import name 'InferenceData' from 'pymc' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-134-the-cognitive-mechanisms-underlying-intu/lib/python3.11/site-packages/pymc/__init__.py)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian_model.py", line 24, in <module>
    raise ImportError("PyMC5 is required. Install via: pip install pymc==5.12.0")
ImportError: PyMC5 is required. Install via: pip install pymc==5.12.0


## Declared deliverables still missing

- data/processed/merged_data.csv
- data/processed/merged_simulation.csv
- data/processed/synthetic_logs.csv
- data/processed/synthetic_mfq.csv
- data/raw/mfq_real.csv
- data/raw/stories_real.csv
- data/raw/vr_logs_real.parquet
- data/results/mixed_effects_bonferroni_results.json
- data/results/model_comparison.json
- data/results/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/models/bayesian.py` — NOT invoked by the run-book
    - `code/models/regression.py` — NOT invoked by the run-book
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/tests/test_e2e_real_data.py` — NOT invoked by the run-book
    - `code/tests/test_edge_cases.py` — NOT invoked by the run-book
    - `code/tests/test_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_simulation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_simulation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/simulation_stories.py` — NOT invoked by the run-book
    - `code/utils/hashing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synthetic_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_mfq.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingest.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/data/simulation_mfq.py` — NOT invoked by the run-book
    - `code/tests/test_edge_cases.py` — NOT invoked by the run-book
    - `code/tests/test_ingest_integration.py` — NOT invoked by the run-book
    - `code/tests/test_ingest_mfq.py` — NOT invoked by the run-book
    - `code/utils/hashing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synthetic_mfq.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/mfq_real.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fetch_real.py` — NOT invoked by the run-book
    - `code/data/gate_mode.py` — NOT invoked by the run-book
    - `code/data/real_mode_gate.py` — NOT invoked by the run-book
    - `code/data/validate_mfq_norms.py` — NOT invoked by the run-book
    - `code/tests/test_e2e_real_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/mfq_real.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/stories_real.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fetch_real.py` — NOT invoked by the run-book
    - `code/data/gate_mode.py` — NOT invoked by the run-book
    - `code/data/real_mode_gate.py` — NOT invoked by the run-book
    - `code/tests/test_e2e_real_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/stories_real.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/vr_logs_real.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/fail_loudly.py` — NOT invoked by the run-book
    - `code/data/fetch_real.py` — NOT invoked by the run-book
    - `code/data/fetch_real_vr.py` — IS a run-book command
    - `code/data/gate_mode.py` — NOT invoked by the run-book
    - `code/data/real_mode_gate.py` — NOT invoked by the run-book
    - `code/data/verify_vr_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/vr_logs_real.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mixed_effects_bonferroni_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mixed_effects_bonferroni_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/model_comparison.py` — IS a run-book command
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
    - `code/tests/test_e2e_real_data.py` — NOT invoked by the run-book
    - `code/tests/test_edge_cases.py` — NOT invoked by the run-book
    - `code/tests/test_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/validation.py` — NOT invoked by the run-book
    - `code/reports/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
