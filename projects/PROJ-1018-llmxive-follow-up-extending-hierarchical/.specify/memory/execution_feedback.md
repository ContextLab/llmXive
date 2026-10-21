# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): bash ./run_pipeline.sh; python src/sensitivity.py --k-values 50,100,200 --output data/reports/sweep_report.json; 3 command(s) failed: python src/data_loader.py  --dataset deepmind/pg19  --split-ratio 0.05  --seed 42  --min-tokens 32000  --pad-short-docs False (rc=1); python code/src/clustering.py --input data/interim/relevance_profiles.json --k 100 --output data/processed/static_index_k100.json --seed 42 (rc=1); python code/src/evaluation.py --dynamic-checkpoint llmxive/hils-base --static-index data/processed/static_index_k100.json --split test --qa-dataset llamaindex/long-qa --output data/reports/evaluation_report.json (rc=1); 2 declared deliverable(s) absent: data/interim/filtered_pg19.json; data/interim/relevance_profiles.json

## Failing / missing run-book commands

- bash ./run_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
- python src/data_loader.py  --dataset deepmind/pg19  --split-ratio 0.05  --seed 42  --min-tokens 32000  --pad-short-docs False -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/data_loader.py", line 30, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/src/clustering.py --input data/interim/relevance_profiles.json --k 100 --output data/processed/static_index_k100.json --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/src/clustering.py", line 270, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/src/clustering.py", line 241, in main
    profiles_path = os.path.join(config.data_interim_dir, 'relevance_profiles.json')
                                 ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'Config' object has no attribute 'data_interim_dir'. Did you mean: 'interim_dir'?

- python code/src/evaluation.py --dynamic-checkpoint llmxive/hils-base --static-index data/processed/static_index_k100.json --split test --qa-dataset llamaindex/long-qa --output data/reports/evaluation_report.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/src/evaluation.py", line 7, in <module>
    from datasets import load_dataset, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/sensitivity.py --k-values 50,100,200 --output data/reports/sweep_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1018-llmxive-follow-up-extending-hierarchical/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/src/sensitivity.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/interim/filtered_pg19.json
- data/interim/relevance_profiles.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/filtered_pg19.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data_loader.py` — NOT invoked by the run-book
    - `src/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/filtered_pg19.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/relevance_profiles.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_static_inference.py` — NOT invoked by the run-book
    - `code/src/aggregation.py` — IS a run-book command
    - `code/src/clustering.py` — IS a run-book command
    - `code/src/extraction.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/relevance_profiles.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
