# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.pipeline.run_all  --num_videos <sufficient number of videos>  --lambda_values 0.1 0.5 1.0  --seeds $SEED_LIST  --flow_divergence_thresh 0.15  --feature_sim_thresh 0.9  --output_dir ./output`
  - script usage: `run_all.py [-h] [--config CONFIG] [--output_dir OUTPUT_DIR]`
  - argparse error: `run_all.py: error: unrecognized arguments: number of videos>`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipeline.run_all  --num_videos <sufficient number of videos>  --lambda_values 0.1 0.5 1.0  --seeds $SEED_LIST  --flow_divergence_thresh 0.15  --feature_sim_thresh 0.9  --output_dir ./output (rc=2); 3 declared deliverable(s) absent: data/counterfactuals/temp_metadata.csv; data/patches/manifest.csv; figures/threshold_retention.png

## Failing / missing run-book commands

- python -m src.pipeline.run_all  --num_videos <sufficient number of videos>  --lambda_values 0.1 0.5 1.0  --seeds $SEED_LIST  --flow_divergence_thresh 0.15  --feature_sim_thresh 0.9  --output_dir ./output -> rc=2

usage: run_all.py [-h] [--config CONFIG] [--output_dir OUTPUT_DIR]
                  [--subset_size SUBSET_SIZE] [--num_videos NUM_VIDEOS]
                  [--lambda_values LAMBDA_VALUES [LAMBDA_VALUES ...]]
                  [--seeds SEEDS [SEEDS ...]]
                  [--flow_divergence_thresh FLOW_DIVERGENCE_THRESH]
                  [--feature_sim_thresh FEATURE_SIM_THRESH]
run_all.py: error: unrecognized arguments: number of videos>


## Declared deliverables still missing

- data/counterfactuals/temp_metadata.csv
- data/patches/manifest.csv
- figures/threshold_retention.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/counterfactuals/temp_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/counterfactual.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/counterfactuals/temp_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/patches/manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/optical_flow_loader.py` — NOT invoked by the run-book
    - `src/data/optical_flow_precompute.py` — NOT invoked by the run-book
    - `src/data/patches_download.py` — NOT invoked by the run-book
    - `src/data/synthetic_generator.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/patches/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `figures/threshold_retention.png` is declared but was NOT written. Scripts referencing it:
    - `src/pipeline/run_all.py` — IS a run-book command
    - `src/report/threshold_retention_plot.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/threshold_retention.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
