# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python code/main.py --action download --config config.yaml (rc=1); python code/main.py --action estimate_noise --config config.yaml (rc=1); python code/main.py --action inject_signals --config config.yaml (rc=1); 4 declared deliverable(s) absent: data/aggregated/convergence_log.json; data/aggregated/split_half_results.json; data/derived/processed_roi/roi_timeseries.csv

## Failing / missing run-book commands

- python code/main.py --action download --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 15, in <module>
    from download.data_validator import main as validate_main
ImportError: cannot import name 'main' from 'download.data_validator' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)

- python code/main.py --action estimate_noise --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 15, in <module>
    from download.data_validator import main as validate_main
ImportError: cannot import name 'main' from 'download.data_validator' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)

- python code/main.py --action inject_signals --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 15, in <module>
    from download.data_validator import main as validate_main
ImportError: cannot import name 'main' from 'download.data_validator' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)

- python code/main.py --action analyze --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 15, in <module>
    from download.data_validator import main as validate_main
ImportError: cannot import name 'main' from 'download.data_validator' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)

- python code/main.py --action report --config config.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/main.py", line 15, in <module>
    from download.data_validator import main as validate_main
ImportError: cannot import name 'main' from 'download.data_validator' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)

- python -m pytest tests/unit/ -v -> rc=2
: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/_pytest/assertion/rewrite.py:178: in exec_module
    exec(co, module.__dict__)
tests/unit/test_timer.py:11: in <module>
    from utils.timer import (
E   ImportError: cannot import name '_run_start_time' from 'utils.timer' (/home/runner/work/llmXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/utils/timer.py)
=========================== short test summary info ============================
ERROR tests/unit/test_alpha_sweep_analyzer.py
ERROR tests/unit/test_create_results_dirs.py - NameError: name 'Optional' is not defined
ERROR tests/unit/test_main_orchestration.py
ERROR tests/unit/test_memory_monitor.py
ERROR tests/unit/test_power_curve_generator.py
ERROR tests/unit/test_split_half_validator.py
ERROR tests/unit/test_timer.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 7 errors in 2.56s ===============================


- python -m pytest tests/integration/test_end_to_end_pipeline.py -v -> rc=1
mXive/llmXive/projects/PROJ-437-statistical-power-analysis-of-openly-ava/code/download/data_validator.py)\n').returncode
FAILED tests/integration/test_end_to_end_pipeline.py::TestEndToEndPipeline::test_pipeline_logs_convergence - AssertionError: Convergence log file not found. This indicates T016 (GLM fitting) or T016b (logging) may not be implemented.
assert False
 +  where False = <bound method Path.exists of PosixPath('data/aggregated/convergence_log.json')>()
 +    where <bound method Path.exists of PosixPath('data/aggregated/convergence_log.json')> = PosixPath('data/aggregated/convergence_log.json').exists
FAILED tests/integration/test_end_to_end_pipeline.py::TestEndToEndPipeline::test_pipeline_creates_traceability_config - AssertionError: Pipeline configuration log not found. This indicates T013c (traceability logger) may not be implemented.
assert False
 +  where False = <bound method Path.exists of PosixPath('results/paper/pipeline_config.json')>()
 +    where <bound method Path.exists of PosixPath('results/paper/pipeline_config.json')> = PosixPath('results/paper/pipeline_config.json').exists
============================== 3 failed in 0.97s ===============================


- python -m pytest tests/contract/ -v -> rc=1
 >= 1'))
 +    where ValueError('num_iterations must be >= 1') = <ExceptionInfo ValueError('num_iterations must be >= 1') tblen=3>.value
FAILED tests/contract/test_simulation_config_schema.py::TestSimulationConfigSchema::test_invalid_num_iterations_negative - AssertionError: assert 'num_iterations must be greater than 0' in 'num_iterations must be >= 1'
 +  where 'num_iterations must be >= 1' = str(ValueError('num_iterations must be >= 1'))
 +    where ValueError('num_iterations must be >= 1') = <ExceptionInfo ValueError('num_iterations must be >= 1') tblen=3>.value
FAILED tests/contract/test_simulation_config_schema.py::TestSimulationConfigSchema::test_apply_seed_with_value - AttributeError: 'SimulationConfig' object has no attribute 'apply_seed'
FAILED tests/contract/test_simulation_config_schema.py::TestSimulationConfigSchema::test_apply_seed_without_value - AttributeError: 'SimulationConfig' object has no attribute 'apply_seed'
FAILED tests/contract/test_simulation_config_schema.py::TestSimulationConfigSchema::test_frozen_dataclass - Failed: DID NOT RAISE <class 'dataclasses.FrozenInstanceError'>
========================= 10 failed, 3 passed in 0.73s =========================



## Declared deliverables still missing

- data/aggregated/convergence_log.json
- data/aggregated/split_half_results.json
- data/derived/processed_roi/roi_timeseries.csv
- data/derived/replication_results/individual_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/aggregated/convergence_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/convergence_logger.py` — NOT invoked by the run-book
    - `code/analysis/glm_fitter.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/convergence_monitor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/aggregated/convergence_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/aggregated/split_half_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/aggregated/split_half_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/processed_roi/roi_timeseries.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
    - `code/preprocess/roi_extractor.py` — NOT invoked by the run-book
    - `code/preprocess/temporal_smoothing.py` — NOT invoked by the run-book
    - `code/simulation/noise_estimator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/processed_roi/roi_timeseries.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/replication_results/individual_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/split_half_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/replication_results/individual_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
