# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/verify_references.py --stage dataset   # checks ds004510 URL (FR‑012‑1)`
  - script usage: `verify_references.py [-h] --stage {dataset,conditions,citations,all}`
  - argparse error: `verify_references.py: error: unrecognized arguments: # checks ds004510 URL (FR‑012‑1)`
- run-book command: `python code/verify_references.py --stage citations # checks bibliography (FR‑012‑3)`
  - script usage: `verify_references.py [-h] --stage {dataset,conditions,citations,all}`
  - argparse error: `verify_references.py: error: unrecognized arguments: # checks bibliography (FR‑012‑3)`
- run-book command: `python code/download.py   # downloads OpenNeuro‑fslr64k, verifies checksum, records hash (FR‑001, FR‑013)`
  - script usage: `download.py [-h] [--subjects SUBJECTS] [--dataset-id DATASET_ID]`
  - argparse error: `download.py: error: unrecognized arguments: # downloads OpenNeuro‑fslr64k, verifies checksum, records hash (FR‑001, FR‑013)`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/preprocess.py   # band‑pass, ICA, mastoid re‑reference, baseline correction, epoching (FR‑002‑FR‑003); python code/analysis.py; python code/visualize.py; 3 command(s) failed: python code/verify_references.py --stage dataset   # checks ds004510 URL (FR‑012‑1) (rc=2); python code/verify_references.py --stage citations # checks bibliography (FR‑012‑3) (rc=2); python code/download.py   # downloads OpenNeuro‑fslr64k, verifies checksum, records hash (FR‑001, FR‑013) (rc=2); 2 declared deliverable(s) absent: data/raw/checksums.json; data/results/citation_verification.json

## Failing / missing run-book commands

- python code/verify_references.py --stage dataset   # checks ds004510 URL (FR‑012‑1) -> rc=2

usage: verify_references.py [-h] --stage {dataset,conditions,citations,all}
                            [--dataset-id DATASET_ID] [--data-dir DATA_DIR]
verify_references.py: error: unrecognized arguments: # checks ds004510 URL (FR‑012‑1)

- python code/verify_references.py --stage citations # checks bibliography (FR‑012‑3) -> rc=2

usage: verify_references.py [-h] --stage {dataset,conditions,citations,all}
                            [--dataset-id DATASET_ID] [--data-dir DATA_DIR]
verify_references.py: error: unrecognized arguments: # checks bibliography (FR‑012‑3)

- python code/download.py   # downloads OpenNeuro‑fslr64k, verifies checksum, records hash (FR‑001, FR‑013) -> rc=2

usage: download.py [-h] [--subjects SUBJECTS] [--dataset-id DATASET_ID]
download.py: error: unrecognized arguments: # downloads OpenNeuro‑fslr64k, verifies checksum, records hash (FR‑001, FR‑013)

- python code/preprocess.py   # band‑pass, ICA, mastoid re‑reference, baseline correction, epoching (FR‑002‑FR‑003) -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/preprocess.py': [Errno 2] No such file or directory

- python code/analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/analysis.py': [Errno 2] No such file or directory

- python code/visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-250-neural-correlates-of-temporal-prediction/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-250-neural-correlates-of-temporal-prediction/code/visualize.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/checksums.json
- data/results/citation_verification.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/citation_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/verify_references.py` — IS a run-book command
  Make ONE of these WRITE `data/results/citation_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
