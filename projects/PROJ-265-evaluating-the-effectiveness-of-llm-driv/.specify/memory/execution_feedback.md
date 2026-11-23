# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py --pilot; 5 command(s) failed: python code/data/download.py (rc=1); python code/data/validate.py (rc=1); python code/models/simplify.py (rc=1)

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
Error: 'datasets' library not found. Install with: pip install datasets


- python code/data/validate.py -> rc=1
Usage: python -m data.validate <input_path> <output_dir>


- python code/models/simplify.py -> rc=1
Error: Input file data/processed/validated_functions.jsonl not found. Please run data pipeline first.


- python code/benchmark/runner.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-265-evaluating-the-effectiveness-of-llm-driv/code/benchmark/runner.py", line 287, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-265-evaluating-the-effectiveness-of-llm-driv/code/benchmark/runner.py", line 279, in main
    log_stage_error(logger, f"Input file not found: {input_path}")
TypeError: log_stage_error() missing 1 required positional argument: 'error'

- python code/benchmark/stats.py -> rc=1
Usage: python -m benchmark.stats <input_results.json> <output_summary.json>


- python code/main.py --pilot -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-265-evaluating-the-effectiveness-of-llm-driv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-265-evaluating-the-effectiveness-of-llm-driv/code/main.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
