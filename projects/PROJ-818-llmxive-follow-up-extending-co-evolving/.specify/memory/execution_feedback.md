# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python src/cli.py generate --logic 100 --grid 50 --seed 42 --output data/synthetic_dataset.json (rc=1); python src/cli.py run --conditions sequential,mixed,coevolving --generations 50 --runs-per-condition 30 --seed 42 (rc=1); python src/cli.py analyze --input results/forgetting_metrics.csv --output results/statistical_report.json (rc=1); 7 declared deliverable(s) absent: data/batch_config.json; data/checksums.json; data/generated_grids.json

## Failing / missing run-book commands

- python src/cli.py generate --logic 100 --grid 50 --seed 42 --output data/synthetic_dataset.json -> rc=1
    ym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.
Please upgrade to Gymnasium, the maintained drop-in replacement of Gym, or contact the authors of your software and request that they upgrade.
Users of this version of Gym should be able to simply replace 'import gym' with 'import gymnasium as gym' in the vast majority of cases.
See the migration guide at https://gymnasium.farama.org/introduction/migration_guide/ for additional information.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/src/cli.py", line 16, in <module>
    from src.analysis.validate_dataset import validate_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/__init__.py", line 8, in <module>
    from .forgetting_metrics import calculate_accuracy_drop, calculate_retention_rate
ImportError: cannot import name 'calculate_accuracy_drop' from 'src.analysis.forgetting_metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/forgetting_metrics.py)
- python src/cli.py run --conditions sequential,mixed,coevolving --generations 50 --runs-per-condition 30 --seed 42 -> rc=1
    ym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.
Please upgrade to Gymnasium, the maintained drop-in replacement of Gym, or contact the authors of your software and request that they upgrade.
Users of this version of Gym should be able to simply replace 'import gym' with 'import gymnasium as gym' in the vast majority of cases.
See the migration guide at https://gymnasium.farama.org/introduction/migration_guide/ for additional information.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/src/cli.py", line 16, in <module>
    from src.analysis.validate_dataset import validate_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/__init__.py", line 8, in <module>
    from .forgetting_metrics import calculate_accuracy_drop, calculate_retention_rate
ImportError: cannot import name 'calculate_accuracy_drop' from 'src.analysis.forgetting_metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/forgetting_metrics.py)
- python src/cli.py analyze --input results/forgetting_metrics.csv --output results/statistical_report.json -> rc=1
    ym has been unmaintained since 2022 and does not support NumPy 2.0 amongst other critical functionality.
Please upgrade to Gymnasium, the maintained drop-in replacement of Gym, or contact the authors of your software and request that they upgrade.
Users of this version of Gym should be able to simply replace 'import gym' with 'import gymnasium as gym' in the vast majority of cases.
See the migration guide at https://gymnasium.farama.org/introduction/migration_guide/ for additional information.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/src/cli.py", line 16, in <module>
    from src.analysis.validate_dataset import validate_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/__init__.py", line 8, in <module>
    from .forgetting_metrics import calculate_accuracy_drop, calculate_retention_rate
ImportError: cannot import name 'calculate_accuracy_drop' from 'src.analysis.forgetting_metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-818-llmxive-follow-up-extending-co-evolving/code/src/analysis/forgetting_metrics.py)

## Declared deliverables still missing

- data/batch_config.json
- data/checksums.json
- data/generated_grids.json
- data/generated_proofs.json
- data/results/parity_report.json
- data/test_instances.json
- data/validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/batch_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/cli.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/analysis/parity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/batch_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/utils/test_checksums.py` — NOT invoked by the run-book
    - `code/tests/unit/test_data_writer.py` — NOT invoked by the run-book
    - `code/src/cli.py` — NOT invoked by the run-book
    - `code/src/utils/checksums.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/generators/data_writer.py` — NOT invoked by the run-book
    - `code/src/analysis/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/generated_grids.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_validate_dataset.py` — NOT invoked by the run-book
    - `code/tests/unit/test_data_writer.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/generators/grid_generator.py` — NOT invoked by the run-book
    - `code/src/generators/data_writer.py` — NOT invoked by the run-book
    - `code/src/agents/sequential_agent.py` — NOT invoked by the run-book
    - `code/src/analysis/validate_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/generated_grids.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/generated_proofs.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_validate_dataset.py` — NOT invoked by the run-book
    - `code/tests/unit/test_data_writer.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/generators/data_writer.py` — NOT invoked by the run-book
    - `code/src/generators/logic_generator.py` — NOT invoked by the run-book
    - `code/src/agents/mixed_agent.py` — NOT invoked by the run-book
    - `code/src/agents/sequential_agent.py` — NOT invoked by the run-book
    - `code/src/analysis/validate_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/generated_proofs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/parity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_parity_checker_post_run.py` — NOT invoked by the run-book
    - `code/src/cli.py` — NOT invoked by the run-book
    - `code/src/analysis/parity_checker.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/parity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/test_instances.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_test_generator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_agent_conditions.py` — NOT invoked by the run-book
    - `code/tests/unit/test_coevolving_agent.py` — NOT invoked by the run-book
    - `code/tests/unit/test_forgetting_metrics.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/generators/test_generator.py` — NOT invoked by the run-book
    - `code/src/agents/coevolving_agent.py` — NOT invoked by the run-book
    - `code/src/analysis/forgetting_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/test_instances.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_validate_dataset.py` — NOT invoked by the run-book
    - `code/src/cli.py` — NOT invoked by the run-book
    - `code/src/utils/config.py` — NOT invoked by the run-book
    - `code/src/analysis/validate_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
