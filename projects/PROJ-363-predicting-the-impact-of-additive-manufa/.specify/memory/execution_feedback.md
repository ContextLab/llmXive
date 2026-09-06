# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_data.py (rc=1); python code/preprocess.py (rc=1); python code/train_models.py (rc=1)

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    2026-09-06 02:56:42,451 - llmXive_pipeline - INFO - Starting 316L LPBF dataset download
2026-09-06 02:56:42,451 - llmXive_pipeline - INFO - Fetching metadata from Zenodo record 6826006
2026-09-06 02:56:43,114 - llmXive_pipeline - INFO - Verifying material type is 316L

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 193, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 138, in main
    verify_material_type(metadata)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 67, in verify_material_type
    raise ValueError("Dataset does not appear to be for 316L stainless steel")
ValueError: Dataset does not appear to be for 316L stainless steel
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/preprocess.py", line 4, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/train_models.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/train_models.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analyze_explainability.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/analyze_explainability.py", line 8, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
