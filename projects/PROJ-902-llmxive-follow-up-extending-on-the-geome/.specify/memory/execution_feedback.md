# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.data.download_gsm8k (rc=1); python -m src.cli.run_experiment  --condition frozen_opd  --seed 42  --dry-run (rc=1); python -m src.analysis.generate_report --state results/state.yaml (rc=1)

## Failing / missing run-book commands

- python -m src.data.download_gsm8k -> rc=1
    Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/src/data/download_gsm8k.py", line 21, in <module>
    from src.data.checksums import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/code/src/data/checksums.py", line 27, in <module>
    from src.data.download_gsm8k import compute_sha256, save_checksums, load_checksums
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/src/data/download_gsm8k.py", line 21, in <module>
    from src.data.checksums import (
ImportError: cannot import name 'compute_all_checksums' from partially initialized module 'src.data.checksums' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/code/src/data/checksums.py)
- python -m src.cli.run_experiment  --condition frozen_opd  --seed 42  --dry-run -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/code/.venv/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src.cli')
- python -m src.analysis.generate_report --state results/state.yaml -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/code/.venv/bin/python: Error while finding module specification for 'src.analysis.generate_report' (ModuleNotFoundError: No module named 'src.analysis')
- python -m src.cli.run_experiment  --condition frozen_opd  --variance-threshold 0.90  --seed-list 1 2 3... 30 -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-902-llmxive-follow-up-extending-on-the-geome/code/.venv/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src.cli')
