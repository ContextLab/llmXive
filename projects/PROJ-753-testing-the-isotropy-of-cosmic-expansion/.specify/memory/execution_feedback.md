# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/ingestion.py --verify-only; python code/analysis.py; python code/analysis.py --synthetic --inject-dipole 0.05

## Failing / missing run-book commands

- python code/ingestion.py --verify-only -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-753-testing-the-isotropy-of-cosmic-expansion/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/ingestion.py': [Errno 2] No such file or directory

- python code/analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-753-testing-the-isotropy-of-cosmic-expansion/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py': [Errno 2] No such file or directory

- python code/analysis.py --synthetic --inject-dipole 0.05 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-753-testing-the-isotropy-of-cosmic-expansion/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py': [Errno 2] No such file or directory

