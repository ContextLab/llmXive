# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 12 command(s) failed: python -m src.data.acquire_real   # downloads, verifies SHA‑256, maps to binary ground_truth_label (rc=1); python -m src.features.extract   # reads all .py files, estimates depth/scope, writes data/features.csv (includes sha256) (rc=1); python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (rc=1)

## Failing / missing run-book commands

- python -m src.data.acquire_real   # downloads, verifies SHA‑256, maps to binary ground_truth_label -> rc=1
unner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/src/data/acquire_real.py", line 7, in <module>
    from code.data.download_real import main as _download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-889-llmxive-follow-up-extending-tide-proacti/code/data/download_real.py", line 21, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.features.extract   # reads all .py files, estimates depth/scope, writes data/features.csv (includes sha256) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.features.extract' (ModuleNotFoundError: No module named 'src.features')

- python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_lite' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_original' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.pipelines.consolidate   # creates data/merged_results.csv (SSoT) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.consolidate' (ModuleNotFoundError: No module named 'src.pipelines')

- python -m src.data.split_data          # writes train/validation index files (seed=42) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: No module named src.data.split_data

- python -m src.analysis.logistic        # logistic regression, EPV check, PDP threshold + bootstrap CI -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.logistic' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.mcnemar         # stratified McNemar tests + Holm‑Bonferroni -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.mcnemar' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.sensitivity     # probability‑cutoff sweep & variance reporting -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.sensitivity' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.efficiency      # total runtime & CPU utilisation check -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.efficiency' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.visualize   # writes PNGs under outputs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.visualize' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


