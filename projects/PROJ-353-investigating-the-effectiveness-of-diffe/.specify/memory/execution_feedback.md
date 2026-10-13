# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python code/analyze.py (rc=1); 2 declared deliverable(s) absent: data/analysis_results.json; data/processed/convergence_logs.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-353-investigating-the-effectiveness-of-diffe/code/main.py", line 26, in <module>
    from models import build_gcn_model, create_normalized_adjacency
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-353-investigating-the-effectiveness-of-diffe/code/models.py", line 8, in <module>
    from torch_geometric import sparse
ImportError: cannot import name 'sparse' from 'torch_geometric' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-353-investigating-the-effectiveness-of-diffe/lib/python3.11/site-packages/torch_geometric/__init__.py)

- python code/analyze.py -> rc=1

Error during aggregation: Input directory not found: data/processed/trajectories


## Declared deliverables still missing

- data/analysis_results.json
- data/processed/convergence_logs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/bonferroni_correction.py` — NOT invoked by the run-book
    - `code/extract_interaction.py` — NOT invoked by the run-book
    - `code/generate_analysis_results.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/convergence_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/cox_ph_analysis.py` — NOT invoked by the run-book
    - `code/tobit_regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/convergence_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
