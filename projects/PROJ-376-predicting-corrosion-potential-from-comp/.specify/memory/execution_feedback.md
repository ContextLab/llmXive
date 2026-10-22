# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/cli/run_pipeline.py --stage download (rc=1); 1 declared deliverable(s) absent: data/logs/download_summary.json

## Failing / missing run-book commands

- python code/cli/run_pipeline.py --stage download -> rc=1
00:00", "logger": "code.utils.exceptions", "level": "ERROR", "message": "DataInsufficientError: NIST‑IR‑8200 URL is missing from configuration; cannot download data."}
{"timestamp": "2026-10-22T22:30:30.389489+00:00", "logger": "__main__", "level": "ERROR", "message": "Stage 'download' failed: NIST‑IR‑8200 URL is missing from configuration; cannot download data."}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 86, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 79, in main
    stage_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 27, in run_download_stage
    download_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/data/download_nist.py", line 246, in main
    raise DataInsufficientError(
code.utils.exceptions.DataInsufficientError: NIST‑IR‑8200 URL is missing from configuration; cannot download data.


## Declared deliverables still missing

- data/logs/download_summary.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/download_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/cli/run_pipeline_download_test.py` — NOT invoked by the run-book
    - `code/data/download_nist.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/download_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
