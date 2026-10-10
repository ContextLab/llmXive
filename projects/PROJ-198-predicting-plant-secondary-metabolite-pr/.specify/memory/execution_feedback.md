# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/quickstart_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# In CI, we might use mock data if no real species are c…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…├── mock_genomes.json # Mock genome data for CI testing │ ├── moc…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…─ mock_metabolites.csv # Mock metabolite data for CI testing │ └── moc…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…(`CI_MODE=true`) - Uses mock data files in `data/raw/` - N…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…scientific analysis  ## Mock Data Files  The mock data fil…”
- data/README.md: synthetic/fake INPUT data not authorized by the spec — “…## Mock Data Files  The mock data files are minimal, curat…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/quickstart_validation.py: synthetic/fake INPUT data not authorized by the spec — “…# In CI, we might use mock data if no real species are c…”; data/README.md: synthetic/fake INPUT data not authorized by the spec — “…├── mock_genomes.json # Mock genome data for CI testing │ ├── moc…”; data/README.md: synthetic/fake INPUT data not authorized by the spec — “…─ mock_metabolites.csv # Mock metabolite data for CI testing │ └── moc…”; 4 command(s) failed: python code/cli/main.py --step download_and_align (rc=1); python code/cli/main.py --step train_and_evaluate (rc=1); python -m pytest tests/ (rc=2); 1 declared deliverable(s) absent: data/processed/aligned_matrix.csv

## Failing / missing run-book commands

- python code/cli/main.py --step download_and_align -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 12, in <module>
    from code.config import get_config, load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
ModuleNotFoundError: No module named 'config.env_manager'; 'config' is not a package

- python code/cli/main.py --step train_and_evaluate -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 12, in <module>
    from code.config import get_config, load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
ModuleNotFoundError: No module named 'config.env_manager'; 'config' is not a package

- python -m pytest tests/ -> rc=2
n.py
ERROR tests/test_config.py
ERROR tests/unit/test_align.py
ERROR tests/unit/test_cleanup_refactor.py - AttributeError: 'NoneType' object...
ERROR tests/unit/test_data_directories.py - NameError: name 'List' is not def...
ERROR tests/unit/test_data_hygiene.py - NameError: name 'List' is not defined
ERROR tests/unit/test_download.py
ERROR tests/unit/test_edge_cases.py - AttributeError: 'NoneType' object has n...
ERROR tests/unit/test_env_manager.py
ERROR tests/unit/test_eval.py - AttributeError: 'NoneType' object has no attr...
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_modeling.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_pca_optimization.py - NameError: name 'Any' is not defined
ERROR tests/unit/test_preprocess.py - AttributeError: 'NoneType' object has n...
ERROR tests/unit/test_project_structure.py
ERROR tests/unit/test_report.py
ERROR tests/unit/test_sensitivity.py - AttributeError: 'NoneType' object has ...
ERROR tests/unit/test_train.py - NameError: name 'Any' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 19 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 2 skipped, 19 errors in 2.27s =========================


- python code/cli/main.py --step download_and_align --limit 5 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/cli/main.py", line 12, in <module>
    from code.config import get_config, load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-198-predicting-plant-secondary-metabolite-pr/code/config.py", line 14, in <module>
    from config.env_manager import get_env_manager
ModuleNotFoundError: No module named 'config.env_manager'; 'config' is not a package


## Declared deliverables still missing

- data/processed/aligned_matrix.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_matrix.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cli/main.py` — IS a run-book command
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/data/refactored_align.py` — NOT invoked by the run-book
    - `code/modeling/optimization.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/scripts/apply_pca_optimization.py` — NOT invoked by the run-book
    - `code/scripts/quickstart_validation.py` — NOT invoked by the run-book
    - `code/scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_matrix.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
