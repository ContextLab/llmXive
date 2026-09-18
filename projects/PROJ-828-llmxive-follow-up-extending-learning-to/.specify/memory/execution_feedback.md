# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/src/cli/run_experiment.py --prepare-data (rc=1); python code/src/cli/run_experiment.py --full-pipeline --seeds 10 (rc=1); python code/src/cli/run_experiment.py --variant low_rank_rl --seeds 10 (rc=1)

## Failing / missing run-book commands

- python code/src/cli/run_experiment.py --prepare-data -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-828-llmxive-follow-up-extending-learning-to/code/src/cli/run_experiment.py", line 21, in <module>
    from src.utils.seeds import set_seed, get_seed_config
ModuleNotFoundError: No module named 'src.utils.seeds'
- python code/src/cli/run_experiment.py --full-pipeline --seeds 10 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-828-llmxive-follow-up-extending-learning-to/code/src/cli/run_experiment.py", line 21, in <module>
    from src.utils.seeds import set_seed, get_seed_config
ModuleNotFoundError: No module named 'src.utils.seeds'
- python code/src/cli/run_experiment.py --variant low_rank_rl --seeds 10 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-828-llmxive-follow-up-extending-learning-to/code/src/cli/run_experiment.py", line 21, in <module>
    from src.utils.seeds import set_seed, get_seed_config
ModuleNotFoundError: No module named 'src.utils.seeds'
- python code/src/cli/run_experiment.py --analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-828-llmxive-follow-up-extending-learning-to/code/src/cli/run_experiment.py", line 21, in <module>
    from src.utils.seeds import set_seed, get_seed_config
ModuleNotFoundError: No module named 'src.utils.seeds'
- python code/src/cli/run_experiment.py --verify-alignment --variant low_rank_rl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-828-llmxive-follow-up-extending-learning-to/code/src/cli/run_experiment.py", line 21, in <module>
    from src.utils.seeds import set_seed, get_seed_config
ModuleNotFoundError: No module named 'src.utils.seeds'
