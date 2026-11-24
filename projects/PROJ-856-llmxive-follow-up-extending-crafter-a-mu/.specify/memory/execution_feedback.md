# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.curators.curate_failed_figures  --download  --output-dir data/`
  - script usage: `curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]`
  - argparse error: `curate_failed_figures.py: error: unrecognized arguments: --download`
- run-book command: `python -m src.simulation.power_analysis  --effect-size 0.5  --alpha 0.025  --test mixed_effects`
  - script usage: `power_analysis.py [-h] [--effect-size EFFECT_SIZE] [--alpha ALPHA]`
  - argparse error: `power_analysis.py: error: argument --test: invalid choice: 'mixed_effects' (choose from 'wilcoxon', 't-test')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.curators.curate_failed_figures  --download  --output-dir data/ (rc=2); python -m src.simulation.power_analysis  --effect-size 0.5  --alpha 0.025  --test mixed_effects (rc=2)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures  --download  --output-dir data/ -> rc=2

usage: curate_failed_figures.py [-h] [--num NUM] [--num-tasks NUM]
                                [-o OUTPUT_DIR]
curate_failed_figures.py: error: unrecognized arguments: --download

- python -m src.simulation.power_analysis  --effect-size 0.5  --alpha 0.025  --test mixed_effects -> rc=2

usage: power_analysis.py [-h] [--effect-size EFFECT_SIZE] [--alpha ALPHA]
                         [--power POWER] [--test {wilcoxon,t-test}]
power_analysis.py: error: argument --test: invalid choice: 'mixed_effects' (choose from 'wilcoxon', 't-test')

