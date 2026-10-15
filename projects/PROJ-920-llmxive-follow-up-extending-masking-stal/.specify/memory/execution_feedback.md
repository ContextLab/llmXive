# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity; 3 command(s) failed: python code/generate_trajectories.py  --num-trajectories 500  --output data/raw/trajectories.json  --seed 42 (rc=1); python code/validate_trajectories.py  --input data/raw/trajectories.json (rc=1); python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 (rc=1); 1 declared deliverable(s) absent: data/raw/trajectories.json

## Failing / missing run-book commands

- python code/generate_trajectories.py  --num-trajectories 500  --output data/raw/trajectories.json  --seed 42 -> rc=1
ve/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py", line 204, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py", line 163, in main
    turns.append(build_turn(turn_idx, turn_idx == crit_idx, target_entropy, terms))
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py", line 114, in build_turn
    text = generate_text_for_target_entropy(target_entropy, terms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/generate_trajectories.py", line 81, in generate_text_for_target_entropy
    text_parts.append(random.choice(terms))
                      ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/random.py", line 374, in choice
    return seq[self._randbelow(len(seq))]
           ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyError: 0

- python code/validate_trajectories.py  --input data/raw/trajectories.json -> rc=1

2026-10-15 12:12:15,936 - ERROR - Trajectory file not found: data/raw/trajectories.json

- python code/simulate_agent.py  --input data/raw/trajectories.json  --output data/logs/simulation_results.csv  --seed 42 -> rc=1

2026-10-15 12:12:15,980 - INFO - Starting simulation (seed=42)
2026-10-15 12:12:15,980 - INFO - Loading trajectories from data/raw/trajectories.json
2026-10-15 12:12:15,980 - ERROR - Data Flow Violation: Trajectory generation not complete

- python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/trajectories.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/trajectories.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_trajectories.py` — IS a run-book command
    - `code/simulate_agent.py` — IS a run-book command
    - `code/validate_grounding_config.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate_simulation.py` — NOT invoked by the run-book
    - `code/validate_trajectories.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/trajectories.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
