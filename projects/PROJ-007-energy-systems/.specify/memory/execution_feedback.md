# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/src/main.py (rc=1)

## Failing / missing run-book commands

- python -c "from src.data.ingest import download_datasets; download_datasets()" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/data/ingest.py", line 16, in <module>
    from src.utils.logging import get_logger
ImportError: cannot import name 'get_logger' from 'src.utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/utils/logging.py)
- python code/src/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/code/src/main.py", line 8, in <module>
    from src.models.schemas import AnalysisResult, GracefulDegradationStatus
ImportError: cannot import name 'GracefulDegradationStatus' from 'src.models.schemas' (/home/runner/work/llmXive/llmXive/projects/PROJ-007-energy-systems/src/models/schemas.py)
