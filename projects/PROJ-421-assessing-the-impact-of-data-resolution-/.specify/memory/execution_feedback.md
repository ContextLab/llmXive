# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python main.py --action ingest --state CO --output data/derived/; python main.py --action analyze --class-id 41 --permutations 1000 --simulations 1000; python main.py --action plot --output figures/power_curve.png

## Failing / missing run-book commands

- python main.py --action ingest --state CO --output data/derived/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory
- python main.py --action analyze --class-id 41 --permutations 1000 --simulations 1000 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory
- python main.py --action plot --output figures/power_curve.png -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-421-assessing-the-impact-of-data-resolution-/main.py': [Errno 2] No such file or directory
