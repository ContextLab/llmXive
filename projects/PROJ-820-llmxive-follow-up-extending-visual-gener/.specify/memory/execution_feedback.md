# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/simulation/physics_engine.py --test`
  - script usage: `physics_engine.py [-h] [--input INPUT] [--output OUTPUT] [--log LOG]`
  - argparse error: `physics_engine.py: error: unrecognized arguments: --test`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/simulation/physics_engine.py --test (rc=2); python code/main.py --n 100 --mode full (rc=1); python code/main.py --n 10 --mode full (rc=1); 3 declared deliverable(s) absent: data/derived/seed_manifest.json; data/processed/final_analysis.csv; data/processed/power_analysis_report.json

## Failing / missing run-book commands

- python code/simulation/physics_engine.py --test -> rc=2

usage: physics_engine.py [-h] [--input INPUT] [--output OUTPUT] [--log LOG]
physics_engine.py: error: unrecognized arguments: --test

- python code/main.py --n 100 --mode full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-820-llmxive-follow-up-extending-visual-gener/code/main.py", line 29, in <module>
    from generation.prompt_engine import run_prompt_generation
ImportError: cannot import name 'run_prompt_generation' from 'generation.prompt_engine' (/home/runner/work/llmXive/llmXive/projects/PROJ-820-llmxive-follow-up-extending-visual-gener/code/generation/prompt_engine.py)

- python code/main.py --n 10 --mode full -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-820-llmxive-follow-up-extending-visual-gener/code/main.py", line 29, in <module>
    from generation.prompt_engine import run_prompt_generation
ImportError: cannot import name 'run_prompt_generation' from 'generation.prompt_engine' (/home/runner/work/llmXive/llmXive/projects/PROJ-820-llmxive-follow-up-extending-visual-gener/code/generation/prompt_engine.py)


## Declared deliverables still missing

- data/derived/seed_manifest.json
- data/processed/final_analysis.csv
- data/processed/power_analysis_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/seed_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/generation/__init__.py` — NOT invoked by the run-book
    - `code/generation/diffusion_runner.py` — NOT invoked by the run-book
    - `code/generation/seed_manager.py` — NOT invoked by the run-book
    - `code/generation/seed_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/seed_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/__init__.py` — NOT invoked by the run-book
    - `code/analysis/statistics.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
