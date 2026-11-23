# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/preprocessing.py: self-declared fabricated metric — “…create a minimal CSV     with placeholder values for the supplied ``participa…”
- code/preprocessing.py: self-declared fabricated metric — “…thetic one with deterministic placeholder values     synthetic_path = raw_dir…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…# Dummy Data Directory  This director…”
- data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…pt will generate its own dummy data dynamically in a tempora…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -c "import datasets; datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')"`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/preprocessing.py: self-declared fabricated metric — “…create a minimal CSV     with placeholder values for the supplied ``participa…”; code/preprocessing.py: self-declared fabricated metric — “…thetic one with deterministic placeholder values     synthetic_path = raw_dir…”; data/dummy/README.md: synthetic/fake INPUT data not authorized by the spec — “…# Dummy Data Directory  This director…”; every produced artifact is gitignored (data/raw/metadata.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: bash scripts/pre-run-validation.sh (rc=1); python code/main.py (rc=1); python code/main.py --step preprocess (rc=1); 1 declared deliverable(s) absent: data/processed/feature_matrix.csv

## Failing / missing run-book commands

- python -c "import datasets; datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')" -> rc=1
1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/datasets/load.py", line 1667, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/datasets/load.py", line 1290, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/datasets/load.py", line 1176, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-712-predicting-individual-pain-sensitivity-f/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'openneuro/ds003542' doesn't exist on the Hub or cannot be accessed.

- bash scripts/pre-run-validation.sh -> rc=1
=== Pre-run Validation ===
Project Root: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f

2026-10-23 06:24:19,261 - __main__ - ERROR - Missing required citations:
2026-10-23 06:24:19,261 - __main__ - ERROR -   - doi:10.1234/example1
2026-10-23 06:24:19,261 - __main__ - ERROR -   - doi:10.5678/example2

- python code/main.py -> rc=1

Error processing participant .gitkeep: Participant folder not found: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/.gitkeep
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 206, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 142, in main
    df = aggregate_features(participant_features, feature_matrix_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 46, in aggregate_features
    raise ValueError("No participant data provided for aggregation.")
ValueError: No participant data provided for aggregation.

- python code/main.py --step preprocess -> rc=1
projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/.gitkeep
Error processing participant metadata: Participant folder not found: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/metadata
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 206, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 142, in main
    df = aggregate_features(participant_features, feature_matrix_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 46, in aggregate_features
    raise ValueError("No participant data provided for aggregation.")
ValueError: No participant data provided for aggregation.

- python code/main.py --step model -> rc=1
projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/.gitkeep
Error processing participant metadata: Participant folder not found: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/metadata
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 206, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 142, in main
    df = aggregate_features(participant_features, feature_matrix_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 46, in aggregate_features
    raise ValueError("No participant data provided for aggregation.")
ValueError: No participant data provided for aggregation.

- python code/main.py --step diagnostics -> rc=1
projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/.gitkeep
Error processing participant metadata: Participant folder not found: /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/data/raw/metadata
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/utils.py", line 206, in wrapper
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 142, in main
    df = aggregate_features(participant_features, feature_matrix_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/code/main.py", line 46, in aggregate_features
    raise ValueError("No participant data provided for aggregation.")
ValueError: No participant data provided for aggregation.

- python -m pytest -q -> rc=2
oolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_checksum_manager.py:17: in <module>
    from checksum_manager import (
E   ModuleNotFoundError: No module named 'checksum_manager'
_______________ ERROR collecting tests/unit/test_data_loader.py ________________
import file mismatch:
imported module 'test_data_loader' has this __file__ attribute:
  /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/tests/integration/test_data_loader.py
which is not the same as the test file we want to collect:
  /home/runner/work/llmXive/llmXive/projects/PROJ-712-predicting-individual-pain-sensitivity-f/tests/unit/test_data_loader.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
=========================== short test summary info ============================
ERROR tests/unit/test_checksum_manager.py
ERROR tests/unit/test_data_loader.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 1.33s ===============================



## Declared deliverables still missing

- data/processed/feature_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
    - `code/validate_feature_matrix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
