# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.pipeline.run_all  --dataset_name something-something-v2  --subset_size 200  --train_split 0.8  --val_split 0.1  --test_split 0.1  --lambda_values 0.1 0.5 1.0  --seeds 1 2 3 4 5 6 7 8 9 10  --optical_flow_divergence_threshold 0.15  --feature_similarity_threshold 0.9  --output_dir ./output`
  - script usage: `run_all.py [-h] --config CONFIG`
  - argparse error: `run_all.py: error: the following arguments are required: --config`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipeline.run_all  --dataset_name something-something-v2  --subset_size 200  --train_split 0.8  --val_split 0.1  --test_split 0.1  --lambda_values 0.1 0.5 1.0  --seeds 1 2 3 4 5 6 7 8 9 10  --optical_flow_divergence_threshold 0.15  --feature_similarity_threshold 0.9  --output_dir ./output (rc=2); 4 declared deliverable(s) absent: data/checksums/manifest.csv; data/counterfactuals/metadata.csv; figures/bootstrap_hist.png

## Failing / missing run-book commands

- python -m src.pipeline.run_all  --dataset_name something-something-v2  --subset_size 200  --train_split 0.8  --val_split 0.1  --test_split 0.1  --lambda_values 0.1 0.5 1.0  --seeds 1 2 3 4 5 6 7 8 9 10  --optical_flow_divergence_threshold 0.15  --feature_similarity_threshold 0.9  --output_dir ./output -> rc=2

usage: run_all.py [-h] --config CONFIG
run_all.py: error: the following arguments are required: --config


## Declared deliverables still missing

- data/checksums/manifest.csv
- data/counterfactuals/metadata.csv
- figures/bootstrap_hist.png
- figures/delta_acc_vs_lambda.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums/manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/optical_flow_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/counterfactuals/metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/counterfactuals/metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/bootstrap_hist.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/delta_acc_vs_lambda.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
