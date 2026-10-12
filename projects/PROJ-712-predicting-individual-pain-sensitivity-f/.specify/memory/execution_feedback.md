# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/preprocessing.py: self-declared fabricated metric — “…ll generate realistic-looking mock values to ensure the structure is c…”
- code/preprocessing.py: self-declared fabricated metric — “…work on REAL data.     # The mock values here are just to satisfy the…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…e, never falling back to synthetic data. """ import os import nu…”
- code/preprocessing.py: synthetic/fake INPUT data not authorized by the spec — “…ssary inputs.          # Simulated inputs for the sake of the feat…”
- code/preprocessing.py: synthetic/fake INPUT data not authorized by the spec — “…n.     # IMPORTANT: This mock data is ONLY for the purpose…”
- code/preprocessing.py: synthetic/fake INPUT data not authorized by the spec — “…r reproducibility of the mock data     n_samples = 1000…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…# Dummy Data Directory  This director…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…pt will generate its own dummy data dynamically in a tempora…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/preprocessing.py: self-declared fabricated metric — “…ll generate realistic-looking mock values to ensure the structure is c…”; code/preprocessing.py: self-declared fabricated metric — “…work on REAL data.     # The mock values here are just to satisfy the…”; code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…e, never falling back to synthetic data. """ import os import nu…”; 6 command(s) failed: bash scripts/pre-run-validation.sh (rc=1); python code/main.py (rc=1); python code/main.py --step preprocess (rc=1); 1 declared deliverable(s) absent: data/processed/feature_matrix.csv

## Failing / missing run-book commands

- bash scripts/pre-run-validation.sh -> rc=1
=== Pre-run Validation ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f
Checking citations...

2026-10-12 17:08:12 - ERROR - Missing required citations:
2026-10-12 17:08:12 - ERROR -   - doi:10.1234/example1
2026-10-12 17:08:12 - ERROR -   - doi:10.5678/example2

- python code/main.py -> rc=1
 - INFO - Step 1: Preprocessing and Feature Extraction...
2026-10-12 17:08:13 - INFO - Found 1 participants to process.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 211, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 169, in main
    participant_features = preprocess_all_participants(participant_ids, loader)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 268, in preprocess_all_participants
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 152, in dirname
TypeError: expected str, bytes or os.PathLike object, not EEGDataLoader

- python code/main.py --step preprocess -> rc=1
 - INFO - Step 1: Preprocessing and Feature Extraction...
2026-10-12 17:08:15 - INFO - Found 1 participants to process.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 211, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 169, in main
    participant_features = preprocess_all_participants(participant_ids, loader)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 268, in preprocess_all_participants
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 152, in dirname
TypeError: expected str, bytes or os.PathLike object, not EEGDataLoader

- python code/main.py --step model -> rc=1
 - INFO - Step 1: Preprocessing and Feature Extraction...
2026-10-12 17:08:16 - INFO - Found 1 participants to process.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 211, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 169, in main
    participant_features = preprocess_all_participants(participant_ids, loader)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 268, in preprocess_all_participants
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 152, in dirname
TypeError: expected str, bytes or os.PathLike object, not EEGDataLoader

- python code/main.py --step diagnostics -> rc=1
 - INFO - Step 1: Preprocessing and Feature Extraction...
2026-10-12 17:08:17 - INFO - Found 1 participants to process.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 215, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 211, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 169, in main
    participant_features = preprocess_all_participants(participant_ids, loader)
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/preprocessing.py", line 268, in preprocess_all_participants
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 152, in dirname
TypeError: expected str, bytes or os.PathLike object, not EEGDataLoader

- python -m pytest tests/ -v -> rc=2
v/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_data_loader.py
ERROR tests/integration/test_permutation.py
ERROR tests/test_config.py
ERROR tests/unit/test_checksum_manager.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 14 warnings, 4 errors in 1.83s ========================



## Declared deliverables still missing

- data/processed/feature_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
