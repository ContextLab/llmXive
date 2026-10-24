# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 3 command(s) failed: python code/data/preprocess.py (rc=1); python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); 1 declared deliverable(s) absent: data/raw/checksums.json

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/data/preprocess.py", line 225, in <module>
    processor.run_from_cli()
    ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'MoleculeProcessor' object has no attribute 'run_from_cli'

- python code/analysis/train.py --config config.yaml -> rc=1
{"timestamp": "2026-10-24T20:11:05.512038+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 321}
{"timestamp": "2026-10-24T20:11:05.512146+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "Molecular Permeability \u2013 Training Pipeline", "module": "train", "function": "main", "line": 322}
{"timestamp": "2026-10-24T20:11:05.512200+00:00", "level": "INFO", "task_id": "T004", "logger": "root", "message": "============================================================", "module": "train", "function": "main", "line": 323}
{"timestamp": "2026-10-24T20:11:05.512468+00:00", "level": "ERROR", "task_id": "T004", "logger": "root", "message": "Training or test split not found. Ensure the split step has run.", "module": "train", "function": "main", "line": 338}


- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-24T20:11:08.938437+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
