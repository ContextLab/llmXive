# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.llmxive.data --download (rc=1); python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json (rc=1)

## Failing / missing run-book commands

- python -m src.llmxive.data --download -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: Error while finding module specification for 'src.llmxive.data' (ModuleNotFoundError: No module named 'src')

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44  --output outputs/fixed_baselines.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: Error while finding module specification for 'src.llmxive.cli.run_experiments' (ModuleNotFoundError: No module named 'src')

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44  --output outputs/adaptive_run.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: Error while finding module specification for 'src.llmxive.cli.run_experiments' (ModuleNotFoundError: No module named 'src')

- python -m src.llmxive.analysis  --fixed outputs/fixed_baselines.csv  --adaptive outputs/adaptive_run.json  --outdir outputs/statistics -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/bin/python: Error while finding module specification for 'src.llmxive.analysis' (ModuleNotFoundError: No module named 'src')

