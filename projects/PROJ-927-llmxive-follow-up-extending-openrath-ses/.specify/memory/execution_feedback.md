# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --phase generate --seed 42 --count 500 (rc=1); python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first (rc=1); python code/main.py --phase reconstruct --architectures event_log,session_first (rc=1); 1 declared deliverable(s) absent: data/processed/corruption_map.json

## Failing / missing run-book commands

- python code/main.py --phase generate --seed 42 --count 500 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/code/main.py", line 38, in <module>
    from reconstructors.reconstruction_engine import ReconstructionEngine
ModuleNotFoundError: No module named 'reconstructors.reconstruction_engine'

- python code/main.py --phase simulate --corruption-rates 0.05,0.10,0.20 --architectures event_log,session_first -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/code/main.py", line 38, in <module>
    from reconstructors.reconstruction_engine import ReconstructionEngine
ModuleNotFoundError: No module named 'reconstructors.reconstruction_engine'

- python code/main.py --phase reconstruct --architectures event_log,session_first -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/code/main.py", line 38, in <module>
    from reconstructors.reconstruction_engine import ReconstructionEngine
ModuleNotFoundError: No module named 'reconstructors.reconstruction_engine'

- python code/main.py --phase analyze --test cochrans_q -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-927-llmxive-follow-up-extending-openrath-ses/code/main.py", line 38, in <module>
    from reconstructors.reconstruction_engine import ReconstructionEngine
ModuleNotFoundError: No module named 'reconstructors.reconstruction_engine'


## Declared deliverables still missing

- data/processed/corruption_map.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/corruption_map.json` is declared but was NOT written. Scripts referencing it:
    - `code/exec_corruption.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/simulators/__init__.py` — NOT invoked by the run-book
    - `code/simulators/corruption_log_manager.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corruption_map.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
