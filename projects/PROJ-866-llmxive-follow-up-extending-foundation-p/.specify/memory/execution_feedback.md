# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generators/synthetic_workflow.py --count 500 --seed 42`
  - script usage: `synthetic_workflow.py [-h] [--count COUNT] --output OUTPUT`
  - argparse error: `synthetic_workflow.py: error: the following arguments are required: --output`
- run-book command: `python code/engines/full_context.py --input data/raw/workflows.json`
  - script usage: `full_context.py [-h] --workflow WORKFLOW --output OUTPUT`
  - argparse error: `full_context.py: error: the following arguments are required: --workflow, --output`
- run-book command: `python code/engines/compressed_context.py --input data/raw/workflows.json --depths 2 4 6 8 10`
  - script usage: `compressed_context.py [-h] --workflow WORKFLOW [--depth DEPTH]`
  - argparse error: `compressed_context.py: error: the following arguments are required: --workflow, --output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/generators/synthetic_workflow.py --count 500 --seed 42 (rc=2); python code/engines/full_context.py --input data/raw/workflows.json (rc=2); python code/engines/compressed_context.py --input data/raw/workflows.json --depths 2 4 6 8 10 (rc=2); 3 declared deliverable(s) absent: data/processed/corrected_pvalues.json; data/results/threshold_ci.json; data/results/tradeoff_curve.csv

## Failing / missing run-book commands

- python code/generators/synthetic_workflow.py --count 500 --seed 42 -> rc=2
    usage: synthetic_workflow.py [-h] [--count COUNT] --output OUTPUT
                             [--seed SEED]
synthetic_workflow.py: error: the following arguments are required: --output
- python code/engines/full_context.py --input data/raw/workflows.json -> rc=2
    usage: full_context.py [-h] --workflow WORKFLOW --output OUTPUT
full_context.py: error: the following arguments are required: --workflow, --output
- python code/engines/compressed_context.py --input data/raw/workflows.json --depths 2 4 6 8 10 -> rc=2
    usage: compressed_context.py [-h] --workflow WORKFLOW [--depth DEPTH]
                             [--method {bfs,dfs}] --output OUTPUT
compressed_context.py: error: the following arguments are required: --workflow, --output
- python code/analysis/tradeoff_model.py --full data/processed/full_context_logs.json --compressed data/processed/compressed_context_logs.json -> rc=1
    No logs found for analysis.

## Declared deliverables still missing

- data/processed/corrected_pvalues.json
- data/results/threshold_ci.json
- data/results/tradeoff_curve.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/corrected_pvalues.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bonferroni_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corrected_pvalues.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/threshold_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/threshold_detection.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/threshold_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/tradeoff_curve.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/tradeoff_model.py` — IS a run-book command
    - `code/analysis/generate_regression_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/tradeoff_curve.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
