# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download_data.py --output data/raw/ (rc=1); python code/generate_descriptors.py --input data/raw/ --output data/processed/ (rc=1); python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv (rc=1)

## Failing / missing run-book commands

- python code/download_data.py --output data/raw/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/download_data.py", line 9, in <module>
    from huggingface_hub import HfApi, hf_hub_download, list_repo_files
ModuleNotFoundError: No module named 'huggingface_hub'
- python code/generate_descriptors.py --input data/raw/ --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/generate_descriptors.py", line 8, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/train_learning_curves.py --features data/processed/magpie_features.csv --output data/processed/learning_curves.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/train_learning_curves.py", line 8, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/fit_scaling_laws.py --input data/processed/learning_curves.csv --output data/processed/scaling_results.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/fit_scaling_laws.py", line 18, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/analyze_physics.py --input data/processed/scaling_results.csv --output data/processed/final_analysis.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/analyze_physics.py", line 7, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/visualize_results.py --input data/processed/final_analysis.csv --output figures/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-526-quantifying-the-impact-of-dataset-size-o/code/visualize_results.py", line 13, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
