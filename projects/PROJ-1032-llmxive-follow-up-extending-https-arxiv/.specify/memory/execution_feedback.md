# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_experiment.py  --mode baseline  --model microsoft/phi-2  --seeds 2 3 4 5  --steps multiple epochs  --output data/processed/manifests; python src/cli/run_experiment.py  --mode experiment  --model microsoft/phi-2  --staleness 10  --seeds 1 2 3 4 5  --steps 500  --baseline-dir data/processed/manifests  --output data/processed/run_logs; python src/cli/run_experiment.py  --mode analyze  --input-dir data/processed/run_logs  --output data/processed/summary_results.json

## Failing / missing run-book commands

- python src/cli/run_experiment.py  --mode baseline  --model microsoft/phi-2  --seeds 2 3 4 5  --steps multiple epochs  --output data/processed/manifests -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/src/cli/run_experiment.py': [Errno 2] No such file or directory
- python src/cli/run_experiment.py  --mode experiment  --model microsoft/phi-2  --staleness 10  --seeds 1 2 3 4 5  --steps 500  --baseline-dir data/processed/manifests  --output data/processed/run_logs -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/src/cli/run_experiment.py': [Errno 2] No such file or directory
- python src/cli/run_experiment.py  --mode analyze  --input-dir data/processed/run_logs  --output data/processed/summary_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/src/cli/run_experiment.py': [Errno 2] No such file or directory
- python src/cli/generate_plots.py  --input data/processed/summary_results.json  --output data/artifacts/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1032-llmxive-follow-up-extending-https-arxiv/src/cli/generate_plots.py': [Errno 2] No such file or directory
