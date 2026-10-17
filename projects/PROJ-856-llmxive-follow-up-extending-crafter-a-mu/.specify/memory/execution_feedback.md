# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/`
  - script usage: `curate_failed_figures.py [-h] [--num NUM] [--output-dir OUTPUT_DIR]`
  - argparse error: `curate_failed_figures.py: error: unrecognized arguments: --num-tasks 50`
- run-book command: `python -m src.run_pipeline --config config.yaml`
  - script usage: `run_pipeline.py [-h] [--num NUM] [--output-dir OUTPUT_DIR]`
  - argparse error: `run_pipeline.py: error: unrecognized arguments: --config config.yaml`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ (rc=2); python -m src.utils.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon (rc=1); python -m src.simulation.simulate_participants  --participants 30  --seed 42  --log-dir data/logs/ (rc=1)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ -> rc=2

usage: curate_failed_figures.py [-h] [--num NUM] [--output-dir OUTPUT_DIR]
curate_failed_figures.py: error: unrecognized arguments: --num-tasks 50

- python -m src.utils.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: Error while finding module specification for 'src.utils.power_analysis' (ModuleNotFoundError: No module named 'src.utils')

- python -m src.simulation.simulate_participants  --participants 30  --seed 42  --log-dir data/logs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: Error while finding module specification for 'src.simulation.simulate_participants' (ModuleNotFoundError: No module named 'src.simulation')

- python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: Error while finding module specification for 'src.utils.check_retention' (ModuleNotFoundError: No module named 'src.utils')

- python -m src.validation.run_validation  --log-dir data/logs/  --ground-truth-dir data/ground_truth/  --output-dir data/validation/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: Error while finding module specification for 'src.validation.run_validation' (ModuleNotFoundError: No module named 'src.validation')

- python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: Error while finding module specification for 'src.analysis.wilcoxon_analysis' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.run_pipeline --config config.yaml -> rc=2

Warning: config file 'config.yaml' not found – proceeding with defaults.
usage: run_pipeline.py [-h] [--num NUM] [--output-dir OUTPUT_DIR]
run_pipeline.py: error: unrecognized arguments: --config config.yaml

