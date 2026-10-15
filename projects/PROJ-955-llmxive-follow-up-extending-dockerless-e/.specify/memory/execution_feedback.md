# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed`
  - script usage: `run_pipeline.py [-h] [--dry-run] [--swe_gym_url SWE_GYM_URL]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: ... --sample_fraction 0.1 # 10 % stratified sample, seed fixed`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 (rc=1); python -m pytest -q tests/contract (rc=1); python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed (rc=2); 3 declared deliverable(s) absent: data/patches.csv; data/patches_sample.csv; data/raw_swe_gym.parquet

## Failing / missing run-book commands

- python src/cli/run_pipeline.py  --swe_gym_url https://huggingface.co/datasets/OpenHands/SWE-Gym-code-search/resolve/main/data/train-00000-of-00001.parquet  --multi_swe_rl_url https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-RL/resolve/main/data_20240601_20250331/c/OpenMathLib__OpenBLAS_dataset.jsonl  --output_dir $(pwd)/output  --seed 42 -> rc=1
OJ-955-llmxive-follow-up-extending-dockerless-e/src/cli/run_pipeline.py", line 125, in main
    from src.pipeline.ingest import ingest  # noqa: E402
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-955-llmxive-follow-up-extending-dockerless-e/src/pipeline/ingest.py", line 57, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest -q tests/contract -> rc=1
 _ _ _ _ _ _ 
src/pipeline/ingest.py:57: in <module>
    from datasets import load_dataset
../../.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/datasets/__init__.py:17: in <module>
    from .arrow_dataset import Column, Dataset
../../.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/datasets/arrow_dataset.py:59: in <module>
    import pyarrow as pa
../../.llmxive-venvs/PROJ-955-llmxive-follow-up-extending-dockerless-e/lib/python3.11/site-packages/pyarrow/__init__.py:59: in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

pyarrow/lib.pyx:42: ImportError
=========================== short test summary info ============================
ERROR tests/contract/test_contracts.py::test_raw_files_exist - ImportError: p...
ERROR tests/contract/test_contracts.py::test_patches_csv_structure - ImportEr...
ERROR tests/contract/test_contracts.py::test_execution_logs_exist - ImportErr...
3 errors in 0.64s


- python src/cli/run_pipeline.py  ...  --sample_fraction 0.1   # 10 % stratified sample, seed fixed -> rc=2

2026-10-15 23:17:04,487 INFO __main__: Random seed set to 42
usage: run_pipeline.py [-h] [--dry-run] [--swe_gym_url SWE_GYM_URL]
                       [--multi_swe_rl_url MULTI_SWE_RL_URL]
                       [--output_dir OUTPUT_DIR] [--seed SEED]
run_pipeline.py: error: unrecognized arguments: ... --sample_fraction 0.1 # 10 % stratified sample, seed fixed


## Declared deliverables still missing

- data/patches.csv
- data/patches_sample.csv
- data/raw_swe_gym.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/patches.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/patches.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/patches_sample.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/raw_swe_gym.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/ingest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw_swe_gym.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
