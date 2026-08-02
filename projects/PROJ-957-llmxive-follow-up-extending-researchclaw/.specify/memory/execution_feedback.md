# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python code/data/loader.py --fetch; python code/main.py --run_experiment; python code/scoring/engine.py; 1 command(s) failed: python code/run_filter.py --mode protocol_mismatch --limit 10 (rc=1)

## Failing / missing run-book commands

- python code/data/loader.py --fetch -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/data/loader.py': [Errno 2] No such file or directory
- python code/run_filter.py --mode protocol_mismatch --limit 10 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/run_filter.py", line 13, in <module>
    from src.data.filter import main
ModuleNotFoundError: No module named 'src.data.filter'
- python code/main.py --run_experiment -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/main.py': [Errno 2] No such file or directory
- python code/scoring/engine.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/scoring/engine.py': [Errno 2] No such file or directory
- python code/analysis/stats.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/analysis/stats.py': [Errno 2] No such file or directory
- python code/analysis/report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/analysis/report.py': [Errno 2] No such file or directory
- python code/scoring/dummy_test.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/scoring/dummy_test.py': [Errno 2] No such file or directory
