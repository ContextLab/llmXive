# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/unit/ -v`
  - argparse error: `__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html`
- run-book command: `python -m pytest tests/integration/test_end_to_end_pipeline.py -v`
  - argparse error: `__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html`
- run-book command: `python -m pytest tests/contract/ -v`
  - argparse error: `__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python code/main.py --action download --config config.yaml (rc=1); python code/main.py --action estimate_noise --config config.yaml (rc=1); python code/main.py --action inject_signals --config config.yaml (rc=1); 5 declared deliverable(s) absent: data/aggregated/convergence_log.json; data/aggregated/split_half_results.json; data/derived/noise_parameters.json

## Failing / missing run-book commands

- python code/main.py --action download --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 14, in <module>
    from download.openneuro_fetcher import main as fetch_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/__init__.py", line 7, in <module>
    from .openneuro_fetcher import fetch_paradigm_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/openneuro_fetcher.py", line 46, in <module>
    from utils.resource_guard import enforce_memory_limit
ModuleNotFoundError: No module named 'utils.resource_guard'

- python code/main.py --action estimate_noise --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 14, in <module>
    from download.openneuro_fetcher import main as fetch_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/__init__.py", line 7, in <module>
    from .openneuro_fetcher import fetch_paradigm_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/openneuro_fetcher.py", line 46, in <module>
    from utils.resource_guard import enforce_memory_limit
ModuleNotFoundError: No module named 'utils.resource_guard'

- python code/main.py --action inject_signals --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 14, in <module>
    from download.openneuro_fetcher import main as fetch_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/__init__.py", line 7, in <module>
    from .openneuro_fetcher import fetch_paradigm_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/openneuro_fetcher.py", line 46, in <module>
    from utils.resource_guard import enforce_memory_limit
ModuleNotFoundError: No module named 'utils.resource_guard'

- python code/main.py --action analyze --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 14, in <module>
    from download.openneuro_fetcher import main as fetch_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/__init__.py", line 7, in <module>
    from .openneuro_fetcher import fetch_paradigm_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/openneuro_fetcher.py", line 46, in <module>
    from utils.resource_guard import enforce_memory_limit
ModuleNotFoundError: No module named 'utils.resource_guard'

- python code/main.py --action report --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 14, in <module>
    from download.openneuro_fetcher import main as fetch_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/__init__.py", line 7, in <module>
    from .openneuro_fetcher import fetch_paradigm_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/openneuro_fetcher.py", line 46, in <module>
    from utils.resource_guard import enforce_memory_limit
ModuleNotFoundError: No module named 'utils.resource_guard'

- python -m pytest tests/unit/ -v -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava


- python -m pytest tests/integration/test_end_to_end_pipeline.py -v -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava


- python -m pytest tests/contract/ -v -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --cov=code --cov-report=term-missing --cov-report=html
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava



## Declared deliverables still missing

- data/aggregated/convergence_log.json
- data/aggregated/split_half_results.json
- data/derived/noise_parameters.json
- data/derived/processed_roi/roi_timeseries.csv
- data/derived/replication_results/individual_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/convergence_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/convergence_logger.py` — NOT invoked by the run-book
    - `code/analysis/glm_fitter.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/convergence_monitor.py` — NOT invoked by the run-book
    - `code/utils/execution_order_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/convergence_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/aggregated/split_half_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/execution_order_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/split_half_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/noise_parameters.json` is declared but was NOT written. Scripts referencing it:
    - `code/simulation/noise_estimator.py` — NOT invoked by the run-book
    - `code/utils/execution_order_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/noise_parameters.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/processed_roi/roi_timeseries.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
    - `code/preprocess/roi_extractor.py` — NOT invoked by the run-book
    - `code/preprocess/temporal_smoothing.py` — NOT invoked by the run-book
    - `code/simulation/noise_estimator.py` — NOT invoked by the run-book
    - `code/utils/execution_order_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/processed_roi/roi_timeseries.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/replication_results/individual_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/replication_results/individual_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
