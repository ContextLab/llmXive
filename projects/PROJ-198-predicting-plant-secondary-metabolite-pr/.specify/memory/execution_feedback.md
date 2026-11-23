# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…tion entry point – loads mock data, aligns, saves, and repo…”
- code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…ger(__name__)     # Load mock data files (used when CI_MODE…”
- code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…:         logger.error(f"Mock data not found: {e}")…”
- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…tiny demonstration using mock data (useful during developme…”
- code/scripts/quickstart_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# In CI, we might use mock data if no real species are c…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…├── mock_genomes.json # Mock genome data for CI testing │ ├── moc…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…─ mock_metabolites.csv # Mock metabolite data for CI testing │ └── moc…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…(`CI_MODE=true`) - Uses mock data files in `data/raw/` - N…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/cli/main.py --step download_and_align --limit 5`
  - script usage: `main.py [-h] [--config CONFIG] [--force-download]`
  - argparse error: `main.py: error: unrecognized arguments: --limit 5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 fabricated/simulated-result signal(s) — results are not real measurements: code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…tion entry point – loads mock data, aligns, saves, and repo…”; code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…ger(__name__)     # Load mock data files (used when CI_MODE…”; code/data/align.py: synthetic/fake INPUT data not authorized by the spec — “…:         logger.error(f"Mock data not found: {e}")…”; 4 command(s) failed: python code/cli/main.py --step download_and_align (rc=1); python code/cli/main.py --step train_and_evaluate (rc=1); python code/cli/main.py --step download_and_align --limit 5 (rc=2); 3 declared deliverable(s) absent: data/metadata/checksums.json; data/processed/aligned_matrix.csv; data/processed/phylo_covariance.npy

## Failing / missing run-book commands

- python code/cli/main.py --step download_and_align -> rc=1
rting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:35,744 INFO __main__: Starting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:35,744 INFO __main__: Starting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:35,747 INFO code.config: Configuration loaded (seed=42, species=5)
2026-10-26 10:53:35,747 INFO code.config: Configuration loaded (seed=42, species=5)
2026-10-26 10:53:35,747 INFO code.config: Configuration loaded (seed=42, species=5)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 193, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 162, in main
    ensure_directories(config.data_root)
                       ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-198-predicting-plant-secondary-metabolite-pr/lib/python3.11/site-packages/pydantic/main.py", line 1105, in __getattr__
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
AttributeError: 'Config' object has no attribute 'data_root'

- python code/cli/main.py --step train_and_evaluate -> rc=1
rting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:36,555 INFO __main__: Starting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:36,555 INFO __main__: Starting Plant Metabolite Prediction Pipeline
2026-10-26 10:53:36,557 INFO code.config: Configuration loaded (seed=42, species=5)
2026-10-26 10:53:36,557 INFO code.config: Configuration loaded (seed=42, species=5)
2026-10-26 10:53:36,557 INFO code.config: Configuration loaded (seed=42, species=5)
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 193, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 162, in main
    ensure_directories(config.data_root)
                       ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-198-predicting-plant-secondary-metabolite-pr/lib/python3.11/site-packages/pydantic/main.py", line 1105, in __getattr__
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
AttributeError: 'Config' object has no attribute 'data_root'

- python code/cli/main.py --step download_and_align --limit 5 -> rc=2

usage: main.py [-h] [--config CONFIG] [--force-download]
               [--step {download_and_align,train_and_evaluate}]
main.py: error: unrecognized arguments: --limit 5

- python -m pytest tests/ -> rc=2
 have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_project_structure.py:9: in <module>
    from scripts.setup_project_structure import create_directories, create_init_files
E   ImportError: cannot import name 'create_directories' from 'scripts.setup_project_structure' (/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/scripts/setup_project_structure.py)
=========================== short test summary info ============================
ERROR tests/integration/test_quickstart_validation.py - TypeError: setup_logg...
ERROR tests/models/test_models.py
ERROR tests/unit/test_cleanup_refactor.py
ERROR tests/unit/test_data_hygiene.py - NameError: name 'List' is not defined
ERROR tests/unit/test_env_manager.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_models.py
ERROR tests/unit/test_project_structure.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 8 errors in 0.95s ===============================



## Declared deliverables still missing

- data/metadata/checksums.json
- data/processed/aligned_matrix.csv
- data/processed/phylo_covariance.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metadata/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/utils/citation_validator.py` — NOT invoked by the run-book
    - `code/utils/data_hygiene.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metadata/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/aligned_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cli/main.py` — IS a run-book command
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/refactored_align.py` — NOT invoked by the run-book
    - `code/modeling/optimization.py` — NOT invoked by the run-book
    - `code/modeling/phylo_compute.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/scripts/apply_pca_optimization.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/phylo_covariance.npy` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/phylo_compute.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/phylo_covariance.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
