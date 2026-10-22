# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/cli/run_pipeline.py --stage validate`
  - script usage: `run_pipeline.py [-h] --stage {download}`
  - argparse error: `run_pipeline.py: error: argument --stage: invalid choice: 'validate' (choose from 'download')`
- run-book command: `python code/cli/run_pipeline.py --stage preprocess`
  - script usage: `run_pipeline.py [-h] --stage {download}`
  - argparse error: `run_pipeline.py: error: argument --stage: invalid choice: 'preprocess' (choose from 'download')`
- run-book command: `python code/cli/run_pipeline.py --stage train`
  - script usage: `run_pipeline.py [-h] --stage {download}`
  - argparse error: `run_pipeline.py: error: argument --stage: invalid choice: 'train' (choose from 'download')`
- run-book command: `python code/cli/run_pipeline.py --stage evaluate`
  - script usage: `run_pipeline.py [-h] --stage {download}`
  - argparse error: `run_pipeline.py: error: argument --stage: invalid choice: 'evaluate' (choose from 'download')`
- run-book command: `python code/cli/run_pipeline.py --stage interpret`
  - script usage: `run_pipeline.py [-h] --stage {download}`
  - argparse error: `run_pipeline.py: error: argument --stage: invalid choice: 'interpret' (choose from 'download')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/cli/run_pipeline.py --stage download (rc=1); python code/cli/run_pipeline.py --stage validate (rc=2); python code/cli/run_pipeline.py --stage preprocess (rc=2)

## Failing / missing run-book commands

- python code/cli/run_pipeline.py --stage download -> rc=1
2026-10-22T22:28:17.533826+00:00", "logger": "code.data.download_nist", "level": "ERROR", "message": "NIST‑IR‑8200 URL missing from configuration."}
{"timestamp": "2026-10-22T22:28:17.533910+00:00", "logger": "code.utils.exceptions", "level": "ERROR", "message": "DataInsufficientError: NIST‑IR‑8200 URL is missing from configuration; cannot download data."}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 48, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 40, in main
    run_download_stage()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/cli/run_pipeline.py", line 25, in run_download_stage
    download_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-376-predicting-corrosion-potential-from-comp/code/data/download_nist.py", line 246, in main
    raise DataInsufficientError(
code.utils.exceptions.DataInsufficientError: NIST‑IR‑8200 URL is missing from configuration; cannot download data.

- python code/cli/run_pipeline.py --stage validate -> rc=2

usage: run_pipeline.py [-h] --stage {download}
run_pipeline.py: error: argument --stage: invalid choice: 'validate' (choose from 'download')

- python code/cli/run_pipeline.py --stage preprocess -> rc=2

usage: run_pipeline.py [-h] --stage {download}
run_pipeline.py: error: argument --stage: invalid choice: 'preprocess' (choose from 'download')

- python code/cli/run_pipeline.py --stage train -> rc=2

usage: run_pipeline.py [-h] --stage {download}
run_pipeline.py: error: argument --stage: invalid choice: 'train' (choose from 'download')

- python code/cli/run_pipeline.py --stage evaluate -> rc=2

usage: run_pipeline.py [-h] --stage {download}
run_pipeline.py: error: argument --stage: invalid choice: 'evaluate' (choose from 'download')

- python code/cli/run_pipeline.py --stage interpret -> rc=2

usage: run_pipeline.py [-h] --stage {download}
run_pipeline.py: error: argument --stage: invalid choice: 'interpret' (choose from 'download')

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
