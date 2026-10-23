# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning`
  - script usage: `agent.py [-h] [--library-size LIBRARY_SIZE] [--pruning {on,off}]`
  - argparse error: `agent.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 2 command(s) failed: python code/generate_data.py --seed 42 --overlap high (rc=1); python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning (rc=2); 2 declared deliverable(s) absent: data/raw/skills.json; data/raw/tasks.json

## Failing / missing run-book commands

- python code/generate_data.py --seed 42 --overlap high -> rc=1

INFO:__main__:Acquiring embedding model (real or dummy)...
INFO:__main__:Generating 100 skills with overlap level: HIGH
INFO:__main__:Achieved Mean Similarity: 0.3162
INFO:__main__:Pct > 0.50: 0.00%, Pct > 0.80: 0.00%
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 272, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 241, in main
    raise RuntimeError(
RuntimeError: HIGH overlap failed: Mean 0.3162 <= 0.80 or Pct > 0.80 0.00% < 30%

- python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning -> rc=2

usage: agent.py [-h] [--library-size LIBRARY_SIZE] [--pruning {on,off}]
                [--overlap {LOW,MEDIUM,HIGH}] [--task-sample TASK_SAMPLE]
agent.py: error: argument --overlap: invalid choice: 'high' (choose from 'LOW', 'MEDIUM', 'HIGH')

- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/skills.json
- data/raw/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/skills.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/skills.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
