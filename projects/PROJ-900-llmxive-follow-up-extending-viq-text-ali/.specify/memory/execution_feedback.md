# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/eval.py --checkpoint code/codebook.pt; 3 command(s) failed: python code/data_loader.py --download-only (rc=1); python code/train.py --config code/config.py (rc=1); python code/correlation_analysis.py (rc=1); 2 declared deliverable(s) absent: data/results/embeddings_high_res.h5; data/results/fidelity_metrics.json

## Failing / missing run-book commands

- python code/data_loader.py --download-only -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/data_loader.py", line 4, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/train.py --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/train.py", line 6, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'
- python code/eval.py --checkpoint code/codebook.pt -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/eval.py': [Errno 2] No such file or directory
- python code/correlation_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-900-llmxive-follow-up-extending-viq-text-ali/code/correlation_analysis.py", line 22, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'

## Declared deliverables still missing

- data/results/embeddings_high_res.h5
- data/results/fidelity_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/embeddings_high_res.h5` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
    - `code/eval_high_res.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/embeddings_high_res.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/aggregate_fidelity_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fidelity_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
