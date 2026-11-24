# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; python code/extract_rsa.py --input data/raw/mgb3.parquet --output data/derived/rsametrics.csv; 1 command(s) failed: python code/analysis.py --input data/derived/merged_data.csv --output results/analysis_results.json (rc=1); 4 declared deliverable(s) absent: data/derived/merged_data.csv; data/derived/model_results.csv; data/derived/rsametrics.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-464-predicting-plant-drought-tolerance-from-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-464-predicting-plant-drought-tolerance-from-/code/run_pipeline.py': [Errno 2] No such file or directory

- python code/extract_rsa.py --input data/raw/mgb3.parquet --output data/derived/rsametrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-464-predicting-plant-drought-tolerance-from-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-464-predicting-plant-drought-tolerance-from-/code/extract_rsa.py': [Errno 2] No such file or directory

- python code/analysis.py --input data/derived/merged_data.csv --output results/analysis_results.json -> rc=1
2026-10-22 22:29:34,198 - __main__ - ERROR - Merged data not found at data/derived/merged_data.csv



## Declared deliverables still missing

- data/derived/merged_data.csv
- data/derived/model_results.csv
- data/derived/rsametrics.csv
- data/raw/try_traits.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/cleanup.py` — NOT invoked by the run-book
    - `code/cleanup_utils.py` — NOT invoked by the run-book
    - `code/fetch_phylogeny.py` — NOT invoked by the run-book
    - `code/merge_data.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/model_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleanup.py` — NOT invoked by the run-book
    - `code/cleanup_utils.py` — NOT invoked by the run-book
    - `code/generate_model_results.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/plot_vif_heatmap.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/verify_vif_compliance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/model_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rsametrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cleanup.py` — NOT invoked by the run-book
    - `code/cleanup_utils.py` — NOT invoked by the run-book
    - `code/download_traits.py` — NOT invoked by the run-book
    - `code/generate_rsametrics.py` — NOT invoked by the run-book
    - `code/merge_data.py` — NOT invoked by the run-book
    - `code/preprocess_images.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/rsametrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/try_traits.csv` is declared but was NOT written. Scripts referencing it:
    - `code/merge_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/try_traits.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
