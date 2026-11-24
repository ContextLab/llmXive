# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/graph_generator.py  --count <sufficiently large sample>  --depth-min 1 --depth-max 10  --branch-min 1 --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42`
  - script usage: `graph_generator.py [-h] --count COUNT --depth-min DEPTH_MIN --depth-max`
  - argparse error: `graph_generator.py: error: argument --count: invalid int value: '<sufficiently'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/graph_generator.py  --count <sufficiently large sample>  --depth-min 1 --depth-max 10  --branch-min 1 --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 (rc=2); python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu (rc=1); python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log_extended.csv  --max-turns 1000  --batch-size 5  --device cpu (rc=1); 3 declared deliverable(s) absent: data/processed/execution_log.csv; data/processed/execution_log_smoke.csv; data/processed/extended_budget_log.csv

## Failing / missing run-book commands

- python code/graph_generator.py  --count <sufficiently large sample>  --depth-min 1 --depth-max 10  --branch-min 1 --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 -> rc=2

usage: graph_generator.py [-h] --count COUNT --depth-min DEPTH_MIN --depth-max
                          DEPTH_MAX --branch-min BRANCH_MIN --branch-max
                          BRANCH_MAX --output OUTPUT [--seed SEED]
graph_generator.py: error: argument --count: invalid int value: '<sufficiently'

- python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu -> rc=1

MODEL_PATH not found in .env. Please set it.

- python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log_extended.csv  --max-turns 1000  --batch-size 5  --device cpu -> rc=1

MODEL_PATH not found in .env. Please set it.

- python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 -> rc=1

2026-10-25 20:47:05,018 - __main__ - ERROR - Analysis failed: Execution results file not found: data/processed/execution_log.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 213, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 185, in main
    df = load_execution_results(args.results)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 38, in load_execution_results
    raise FileNotFoundError(f"Execution results file not found: {filepath}")
FileNotFoundError: Execution results file not found: data/processed/execution_log.csv


## Declared deliverables still missing

- data/processed/execution_log.csv
- data/processed/execution_log_smoke.csv
- data/processed/extended_budget_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/execution_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/batch_processor.py` — NOT invoked by the run-book
    - `code/execution_metrics.py` — NOT invoked by the run-book
    - `code/extended_budget_analysis.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — NOT invoked by the run-book
    - `code/rm_executor.py` — IS a run-book command
    - `code/tests/test_analyzer.py` — NOT invoked by the run-book
    - `code/tests/test_rm_executor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/execution_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/execution_log_smoke.csv` is declared but was NOT written. Scripts referencing it:
    - `code/rm_executor.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/execution_log_smoke.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/extended_budget_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extended_budget_analysis.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extended_budget_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
