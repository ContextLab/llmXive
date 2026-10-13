# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 13 command(s) failed: python -m src.data.acquire   # pulls dataset, runs manual mapping to hidden‑problem labels, verifies checksum (rc=1); python -m src.data.generate_synthetic   # creates a set of synthetic .py files under data/synthetic/ (rc=1); python -m src.features.extract   # reads all .py files, writes data/features.csv (includes `origin`) (rc=1)

## Failing / missing run-book commands

- python -m src.data.acquire   # pulls dataset, runs manual mapping to hidden‑problem labels, verifies checksum -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.data.acquire' (ModuleNotFoundError: No module named 'src')

- python -m src.data.generate_synthetic   # creates a set of synthetic .py files under data/synthetic/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.data.generate_synthetic' (ModuleNotFoundError: No module named 'src')

- python -m src.features.extract   # reads all .py files, writes data/features.csv (includes `origin`) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.features.extract' (ModuleNotFoundError: No module named 'src')

- python -m src.pipelines.tide_lite   # outputs data/tide_lite_enriched.csv (full schema) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_lite' (ModuleNotFoundError: No module named 'src')

- python -m src.pipelines.tide_original   # outputs data/tide_original_enriched.csv (full schema) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.tide_original' (ModuleNotFoundError: No module named 'src')

- python -m src.pipelines.consolidate   # creates data/merged_results.csv (full schema, SSoT) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.pipelines.consolidate' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.split_data      # creates train/validation splits (seed=42) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.split_data' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.logistic        # logistic regression + marginal threshold + bootstrap CI -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.logistic' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.mcnemar         # stratified McNemar tests + Holm‑Bonferroni -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.mcnemar' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.sensitivity     # probability‑cutoff sweep & variance reporting -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.sensitivity' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.efficiency      # total runtime & CPU usage report -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.efficiency' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.visualize   # writes PNGs under outputs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-889-llmxive-follow-up-extending-tide-proacti/bin/python: Error while finding module specification for 'src.analysis.visualize' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


