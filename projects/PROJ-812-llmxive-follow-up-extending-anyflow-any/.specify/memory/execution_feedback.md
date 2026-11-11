# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python code/download_curation.py --source <verified_dataset_id> --stratify --output data/raw/; python code/inference_cpu.py --mode pilot --n_clips [selected_count]; python code/inference_cpu.py --mode full --n_clips <NUM_CLIPS>; 10 declared deliverable(s) absent: data/processed/euler_baseline_N500.npy; data/processed/kappa_report.json; data/processed/latents.npy

## Failing / missing run-book commands

- python code/download_curation.py --source <verified_dataset_id> --stratify --output data/raw/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-812-llmxive-follow-up-extending-anyflow-any/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/download_curation.py': [Errno 2] No such file or directory

- python code/inference_cpu.py --mode pilot --n_clips [selected_count] -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-812-llmxive-follow-up-extending-anyflow-any/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/inference_cpu.py': [Errno 2] No such file or directory

- python code/inference_cpu.py --mode full --n_clips <NUM_CLIPS> -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-812-llmxive-follow-up-extending-anyflow-any/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/inference_cpu.py': [Errno 2] No such file or directory

- python code/analysis_stats.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-812-llmxive-follow-up-extending-anyflow-any/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/analysis_stats.py': [Errno 2] No such file or directory

- python code/validation.py --mode synthetic -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-812-llmxive-follow-up-extending-anyflow-any/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/code/validation.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/euler_baseline_N500.npy
- data/processed/kappa_report.json
- data/processed/latents.npy
- data/processed/pilot_correlation.json
- data/processed/runtime_estimate.json
- data/raw/adjudication_log.csv
- data/raw/annotations.csv
- data/raw/calibration_scores.csv
- data/raw/manually_verified_pool.csv
- data/raw/pilot_subset_ids.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/euler_baseline_N500.npy` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/euler_baseline_N500.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/kappa_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
    - `code/data_curation/validate_kappa.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/kappa_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/latents.npy` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/latents.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pilot_correlation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pilot_correlation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/runtime_estimate.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/runtime_estimate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/adjudication_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/define_verification_workflow.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/adjudication_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/annotations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/annotation_tool.py` — NOT invoked by the run-book
    - `code/data_curation/define_verification_workflow.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/annotations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/calibration_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/annotate_pilot.py` — NOT invoked by the run-book
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
    - `code/data_curation/validate_kappa.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/calibration_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/manually_verified_pool.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/annotation_tool.py` — NOT invoked by the run-book
    - `code/data_curation/define_verification_workflow.py` — NOT invoked by the run-book
    - `code/data_curation/download_clips.py` — NOT invoked by the run-book
    - `code/data_curation/download_clips_test.py` — NOT invoked by the run-book
    - `code/data_curation/download_ucf101_manual.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manually_verified_pool.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pilot_subset_ids.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_curation/annotate_pilot.py` — NOT invoked by the run-book
    - `code/data_curation/run_pilot_inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/pilot_subset_ids.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
