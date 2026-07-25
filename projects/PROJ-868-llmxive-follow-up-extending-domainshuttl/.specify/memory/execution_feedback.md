# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/cli.py --phase data_prep (rc=1); python src/cli.py --phase compress (rc=1); python src/cli.py --phase evaluate (rc=1)

## Failing / missing run-book commands

- python src/cli.py --phase data_prep -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-domainshuttl/src/cli.py", line 17, in <module>
    from src.data.loaders import load_webvid_subjects
ModuleNotFoundError: No module named 'src.data.loaders'
- python src/cli.py --phase compress -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-domainshuttl/src/cli.py", line 17, in <module>
    from src.data.loaders import load_webvid_subjects
ModuleNotFoundError: No module named 'src.data.loaders'
- python src/cli.py --phase evaluate -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-domainshuttl/src/cli.py", line 17, in <module>
    from src.data.loaders import load_webvid_subjects
ModuleNotFoundError: No module named 'src.data.loaders'
- python src/cli.py --phase analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-domainshuttl/src/cli.py", line 17, in <module>
    from src.data.loaders import load_webvid_subjects
ModuleNotFoundError: No module named 'src.data.loaders'
- python src/cli.py --phase all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-868-llmxive-follow-up-extending-domainshuttl/src/cli.py", line 17, in <module>
    from src.data.loaders import load_webvid_subjects
ModuleNotFoundError: No module named 'src.data.loaders'
