# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/graph_generator.py  --count 500  --depth-min 1  --depth-max 10  --branch-min 1  --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 (rc=1); python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu (rc=1); python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 (rc=1); 2 declared deliverable(s) absent: data/processed/execution_log.csv; data/processed/extended_budget_log.csv

## Failing / missing run-book commands

- python code/graph_generator.py  --count 500  --depth-min 1  --depth-max 10  --branch-min 1  --branch-max 5  --output data/raw/synthetic_puzzles.jsonl  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 418, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 381, in main
    primary_records = generate_batch(
                      ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 177, in generate_batch
    generator = LogicalPuzzleGenerator(seed=seed)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/graph_generator.py", line 30, in __init__
    nx.set_seed(seed)
    ^^^^^^^^^^^
AttributeError: module 'networkx' has no attribute 'set_seed'

- python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu -> rc=1

MODEL_PATH not found in .env. Please set it.

- python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 -> rc=1

2026-10-14 06:27:31,801 - __main__ - ERROR - Analysis failed: Execution results file not found: data/processed/execution_log.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 213, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 185, in main
    df = load_execution_results(args.results)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 38, in load_execution_results
    raise FileNotFoundError(f"Execution results file not found: {filepath}")
FileNotFoundError: Execution results file not found: data/processed/execution_log.csv

- python -c "import json; data = [json.loads(l) for l in open('data/raw/synthetic_puzzles.jsonl')]; print(f'Count: {len(data)}'); print(f'Depth Range: {min(d[\"nesting_depth\"] for d in data)}-{max(d[\"nesting_depth\"] for d in data)}')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/synthetic_puzzles.jsonl'


## Declared deliverables still missing

- data/processed/execution_log.csv
- data/processed/extended_budget_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/execution_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/batch_processor.py` — NOT invoked by the run-book
    - `code/execution_metrics.py` — NOT invoked by the run-book
    - `code/extended_budget_analysis.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — NOT invoked by the run-book
    - `code/verify_divergence_metric.py` — NOT invoked by the run-book
    - `code/write_execution_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/execution_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/extended_budget_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/extended_budget_analysis.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/generate_checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extended_budget_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
