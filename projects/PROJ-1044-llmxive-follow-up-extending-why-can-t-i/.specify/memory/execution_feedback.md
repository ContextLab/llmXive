# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m src.pipeline.run_all  --num_videos 200  --lambda_values 0.1 0.5 1.0  --seeds $SEED_LIST  --flow_divergence_thresh 0.15  --feature_sim_thresh 0.9  --output_dir ./output (rc=1); 1 declared deliverable(s) absent: data/checksums/manifest.csv

## Failing / missing run-book commands

- python -m src.pipeline.run_all  --num_videos 200  --lambda_values 0.1 0.5 1.0  --seeds $SEED_LIST  --flow_divergence_thresh 0.15  --feature_sim_thresh 0.9  --output_dir ./output -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i/src/pipeline/run_all.py", line 35, in <module>
    from src.data.optical_flow_precompute import main as precompute_flow
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1044-llmxive-follow-up-extending-why-can-t-i/src/data/optical_flow_precompute.py", line 27, in <module>
    import cv2
ModuleNotFoundError: No module named 'cv2'


## Declared deliverables still missing

- data/checksums/manifest.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums/manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `src/data/optical_flow_loader.py` — NOT invoked by the run-book
    - `src/data/optical_flow_precompute.py` — NOT invoked by the run-book
    - `src/pipeline/run_all.py` — IS a run-book command
  Make ONE of these WRITE `data/checksums/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
