# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…alid_main()      # T023: Synthetic Data Generation (for validati…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…gger.info("Running T023: Synthetic Data Generator")     # synthe…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Belief Upd…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ion purposes. It creates synthetic datasets where the true parameter…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a complete synthetic dataset for model valida…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset for {n_participants} par…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic dataset to {output_path}")…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…Main entry point for synthetic data generation.      Command…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/utils/io.py --verify-checksums`
  - script usage: `io.py [-h] {verify-checksums} ...`
  - argparse error: `io.py: error: unrecognized arguments: --verify-checksums`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 12 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…alid_main()      # T023: Synthetic Data Generation (for validati…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…gger.info("Running T023: Synthetic Data Generator")     # synthe…”; code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Belief Upd…”; 8 command(s) failed: python code/utils/io.py --verify-checksums (rc=2); python code/main.py --stage preprocessing (rc=1); python code/main.py --stage modeling (rc=1); 3 declared deliverable(s) absent: data/models/failure_log.json; data/reports/qc_summary.json; data/synthetic/ground_truth.csv

## Failing / missing run-book commands

- python code/utils/io.py --verify-checksums -> rc=2

usage: io.py [-h] {verify-checksums} ...
io.py: error: unrecognized arguments: --verify-checksums

- python code/main.py --stage preprocessing -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 24, in <module>
    from nilearn.preprocessing import clean
ModuleNotFoundError: No module named 'nilearn.preprocessing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 18, in <module>
    from preprocessing.motion_correction import main as motion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 27, in <module>
    raise ImportError("nilearn is required for motion correction. Install via: pip install nilearn")
ImportError: nilearn is required for motion correction. Install via: pip install nilearn

- python code/main.py --stage modeling -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 24, in <module>
    from nilearn.preprocessing import clean
ModuleNotFoundError: No module named 'nilearn.preprocessing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 18, in <module>
    from preprocessing.motion_correction import main as motion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 27, in <module>
    raise ImportError("nilearn is required for motion correction. Install via: pip install nilearn")
ImportError: nilearn is required for motion correction. Install via: pip install nilearn

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 24, in <module>
    from nilearn.preprocessing import clean
ModuleNotFoundError: No module named 'nilearn.preprocessing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 18, in <module>
    from preprocessing.motion_correction import main as motion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 27, in <module>
    raise ImportError("nilearn is required for motion correction. Install via: pip install nilearn")
ImportError: nilearn is required for motion correction. Install via: pip install nilearn

- python code/main.py --stage sensitivity -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 24, in <module>
    from nilearn.preprocessing import clean
ModuleNotFoundError: No module named 'nilearn.preprocessing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 18, in <module>
    from preprocessing.motion_correction import main as motion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 27, in <module>
    raise ImportError("nilearn is required for motion correction. Install via: pip install nilearn")
ImportError: nilearn is required for motion correction. Install via: pip install nilearn

- python code/main.py --stage reporting -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 24, in <module>
    from nilearn.preprocessing import clean
ModuleNotFoundError: No module named 'nilearn.preprocessing'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 18, in <module>
    from preprocessing.motion_correction import main as motion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/motion_correction.py", line 27, in <module>
    raise ImportError("nilearn is required for motion correction. Install via: pip install nilearn")
ImportError: nilearn is required for motion correction. Install via: pip install nilearn

- python -m pytest tests/ -v -> rc=2
he/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_validation.py:12: in <module>
    from modeling.validation import (
code/modeling/validation.py:19: in <module>
    from utils.logger import get_logger
E   ModuleNotFoundError: No module named 'utils.logger'
=========================== short test summary info ============================
ERROR tests/contract/test_data_validation.py
ERROR tests/contract/test_model_convergence.py
ERROR tests/integration/test_belief_updater.py
ERROR tests/integration/test_motion_correction.py
ERROR tests/integration/test_permutation_test.py
ERROR tests/integration/test_roi_extraction.py
ERROR tests/integration/test_synthetic_recovery.py
ERROR tests/unit/test_convergence_reporter.py
ERROR tests/unit/test_logger.py
ERROR tests/unit/test_normalization.py
ERROR tests/unit/test_qc_reporter.py
ERROR tests/unit/test_roi_extraction_utils.py
ERROR tests/unit/test_runtime_enforcer.py
ERROR tests/unit/test_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 14 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 14 errors in 3.73s ==============================


- python -m pytest tests/contract/ -v -> rc=2
t_module(module_name)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/contract/test_model_convergence.py:18: in <module>
    from code.modeling.belief_updater import fit_belief_updater_model
code/modeling/belief_updater.py:25: in <module>
    from utils.config import get_config, set_seed, get_seed
E   ModuleNotFoundError: No module named 'utils.config'
=========================== short test summary info ============================
ERROR tests/contract/test_data_validation.py
ERROR tests/contract/test_model_convergence.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 2.51s ===============================



## Declared deliverables still missing

- data/models/failure_log.json
- data/reports/qc_summary.json
- data/synthetic/ground_truth.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/models/failure_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/models/failure_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/reports/qc_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/preprocessing/qc_reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/qc_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/synthetic/ground_truth.csv` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/synthetic_data_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/synthetic/ground_truth.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
