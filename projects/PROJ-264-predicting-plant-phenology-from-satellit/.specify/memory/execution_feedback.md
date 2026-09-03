# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_pipeline.py --mode ingestion --sites SITE_001 --year 2020; python src/cli/run_pipeline.py --mode train --folds 5 --sites SITE_001..SITE_015 --cv-type spatial; python src/cli/run_pipeline.py --mode sensitivity --alpha 0.01,0.05,0.1

## Failing / missing run-book commands

- python src/cli/run_pipeline.py --mode ingestion --sites SITE_001 --year 2020 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/src/cli/run_pipeline.py': [Errno 2] No such file or directory
- python src/cli/run_pipeline.py --mode train --folds 5 --sites SITE_001..SITE_015 --cv-type spatial -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/src/cli/run_pipeline.py': [Errno 2] No such file or directory
- python src/cli/run_pipeline.py --mode sensitivity --alpha 0.01,0.05,0.1 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/src/cli/run_pipeline.py': [Errno 2] No such file or directory
- python src/cli/run_pipeline.py --mode evaluate --model artifacts/models/best_model.pkl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-264-predicting-plant-phenology-from-satellit/src/cli/run_pipeline.py': [Errno 2] No such file or directory
