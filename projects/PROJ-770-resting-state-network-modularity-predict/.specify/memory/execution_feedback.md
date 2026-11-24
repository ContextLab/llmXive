# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/download_data.py --sample-size`
  - script usage: `download_data.py [-h] [--sample-size SAMPLE_SIZE]`
  - argparse error: `download_data.py: error: argument --sample-size: expected one argument`
- run-book command: `python code/build_graphs.py --threshold-range "10,30,5"`
  - script usage: `build_graphs.py [-h] [--threshold THRESHOLD] [--matrix-dir MATRIX_DIR]`
  - argparse error: `build_graphs.py: error: unrecognized arguments: --threshold-range 10,30,5`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/preprocess_fmri.py; python code/analyze_stats.py; 2 command(s) failed: python code/download_data.py --sample-size (rc=2); python code/build_graphs.py --threshold-range "10,30,5" (rc=2); 2 declared deliverable(s) absent: data/processed/behavioral_clean.csv; data/processed/subject_modularity.csv

## Failing / missing run-book commands

- python code/download_data.py --sample-size -> rc=2

usage: download_data.py [-h] [--sample-size SAMPLE_SIZE]
download_data.py: error: argument --sample-size: expected one argument

- python code/preprocess_fmri.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-770-resting-state-network-modularity-predict/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-770-resting-state-network-modularity-predict/code/preprocess_fmri.py': [Errno 2] No such file or directory

- python code/build_graphs.py --threshold-range "10,30,5" -> rc=2

usage: build_graphs.py [-h] [--threshold THRESHOLD] [--matrix-dir MATRIX_DIR]
build_graphs.py: error: unrecognized arguments: --threshold-range 10,30,5

- python code/analyze_stats.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-770-resting-state-network-modularity-predict/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-770-resting-state-network-modularity-predict/code/analyze_stats.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/behavioral_clean.csv
- data/processed/subject_modularity.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/behavioral_clean.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_data.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/behavioral_clean.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/subject_modularity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/build_graphs.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/subject_modularity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
