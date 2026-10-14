# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/data_loader.py --prepare; python code/query_generator.py --levels 1 2 3 4 --count 500 --seed 42; python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/data_loader.py': [Errno 2] No such file or directory

- python code/query_generator.py --levels 1 2 3 4 --count 500 --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/query_generator.py': [Errno 2] No such file or directory

- python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/ground_truth_engine.py': [Errno 2] No such file or directory

- python code/benchmark_runner.py --throttle cgroups --timeout 60 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/benchmark_runner.py': [Errno 2] No such file or directory

- python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/visualize.py': [Errno 2] No such file or directory

