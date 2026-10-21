# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/`
  - script usage: `curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]`
  - argparse error: `curate_failed_figures.py: error: argument --num-tasks: invalid int value: '<appropriate'`
- run-book command: `python -m src.curators.curate_failed_figures --verify-only --num-tasks 50 --output-dir data/`
  - script usage: `curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]`
  - argparse error: `curate_failed_figures.py: error: unrecognized arguments: --verify-only`
- run-book command: `python -m src.simulation.simulate_participants  --participants a sufficient sample size  --seed 42  --log-dir data/logs/`
  - script usage: `simulate_participants.py [-h] [--participants PARTICIPANTS]`
  - argparse error: `simulate_participants.py: error: argument --participants: invalid int value: 'a'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 command(s) failed: python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/ (rc=2); python -m src.curators.curate_failed_figures --verify-only --num-tasks 50 --output-dir data/ (rc=2); python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon (rc=1); 1 declared deliverable(s) absent: data/results/report_metadata.json

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures  --num-tasks <appropriate count>  --output-dir data/ -> rc=2

usage: curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]
                                [-o OUTPUT_DIR]
curate_failed_figures.py: error: argument --num-tasks: invalid int value: '<appropriate'

- python -m src.curators.curate_failed_figures --verify-only --num-tasks 50 --output-dir data/ -> rc=2

usage: curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]
                                [-o OUTPUT_DIR]
curate_failed_figures.py: error: unrecognized arguments: --verify-only

- python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: No module named src.simulation.power_analysis

- python -m src.simulation.simulate_participants  --participants a sufficient sample size  --seed 42  --log-dir data/logs/ -> rc=2

usage: simulate_participants.py [-h] [--participants PARTICIPANTS]
                                [--seed SEED] [--log-dir LOG_DIR]
simulate_participants.py: error: argument --participants: invalid int value: 'a'

- python -m src.analysis.retention_check --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'figure_id': '0', 'vector_match': True, 'semantic_pass': True, 'similarity_score': 1.000000238418579}"

- python -m src.analysis.wilcoxon_analysis --validation-dir data/validation/ --output-dir outputs/ -> rc=1

2026-10-21 00:31:57,336 ERROR __main__: Validation records missing required columns: {'interface', 'time_to_success_ms', 'iteration_count', 'participant_id'}

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


- python -m src.run_pipeline --config config.yaml -> rc=-1
Pipeline started with seed 42...
Running data curation...
Downloading https://cave.cs.toronto.edu/kriz/cifar-10-python.tar.gz to data/raw_cifar10/cifar-10-python.tar.gz

0.0%0.0%0.1%0.1%0.1%0.1%0.1%0.2%0.2%0.2%0.2%0.2%0.2%0.3%0.3%0.3%0.3%0.3%0.4%0.4%0.4%0.4%0.4%0.5%0.5%0.5%0.5%0.5%0.6%0.6%0.6%0.6%0.6%0.7%0.7%0.7%0.7%0.7%0.7%0.8%0.8%0.8%0.8%0.8%0.9%0.9%0.9%0.9%0.9%1.0%1.0%1.0%1.0%1.0%1.1%1.1%1.1%1.1%1.1%1.2%1.2%1.2%1.2%1.2%1.2%1.3%1.3%1.3%1.3%1.3%1.4%1.4%1.4%1.4%1.4%1.5%1.5%1.5%1.5%1.5%1.6%1.6%1.6%1.6%1.6%1.7%1.7%1.7%1.7%1.7%1.7%1.8%1.8%1.8%1.8%1.8%1.9%1.9%1.9%1.9%1.9%2.0%2.0%2.0%2.0%2.0%2.1%2.1%2.1%2.1%2.1%2.2%2.2%2.2%2.2%2.2%2.2%2.3%2.3%2.3%2.3%2.3%2.4%2.4%2.4%2.4%2.4%2.5%2.5%2.5%2.5%2.5%2.6%2.6%2.6%2.6%2.6%2.7%2.7%2.7%2.7%2.7%2.7%2.8%2.8%2.8%2.8%2.8%2.9%2.9%2.9%2.9%2.9%3.0%3.0%3.0%3.0%3.0%3.1%3.1%3.1%3.1%3.1%3.2%3.2%3.2%3.2%3.2%3.2%3.3%3.3%
[TIMEOUT after 120s]

## Declared deliverables still missing

- data/results/report_metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/report_metadata.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
