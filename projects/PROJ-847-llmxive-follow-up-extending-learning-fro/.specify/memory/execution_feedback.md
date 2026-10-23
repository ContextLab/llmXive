# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.llmxive.data --download (rc=1); python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_baselines.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/adaptive_run.json (rc=1); 1 declared deliverable(s) absent: data/results/fixed_baselines/rho0.5_seed42.json

## Failing / missing run-book commands

- python -m src.llmxive.data --download -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/data.py", line 3, in <module>
    from code.data import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_baselines.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/cli/run_experiments.py", line 5, in <module>
    from code.run_experiments import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/adaptive_run.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/cli/run_experiments.py", line 5, in <module>
    from code.run_experiments import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/control_shuffle.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/cli/run_experiments.py", line 5, in <module>
    from code.run_experiments import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

- python -m src.llmxive.cli.run_experiments  --mode fixed_median  --median_rho 0.55  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_median.json -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/cli/run_experiments.py", line 5, in <module>
    from code.run_experiments import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 40, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'


## Declared deliverables still missing

- data/results/fixed_baselines/rho0.5_seed42.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/fixed_baselines/rho0.5_seed42.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_thin_training.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fixed_baselines/rho0.5_seed42.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
