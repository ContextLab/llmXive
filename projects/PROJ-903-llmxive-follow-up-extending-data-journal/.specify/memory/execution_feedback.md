# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data_loader.py --dataset uci_har --mode download (rc=1); python code/main.py --dataset uci_har --seed 42 (rc=1); python -m pytest tests/unit/ -v (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py --dataset uci_har --mode download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data_loader.py", line 11, in <module>
    from data.loader import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data/__init__.py", line 5, in <module>
    from .loader import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data/loader.py", line 7, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python code/main.py --dataset uci_har --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/main.py", line 11, in <module>
    from data.loader import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data/__init__.py", line 5, in <module>
    from .loader import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/data/loader.py", line 7, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'

- python -m pytest tests/unit/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/.venv/bin/python: No module named pytest

- python -m pytest tests/integration/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-903-llmxive-follow-up-extending-data-journal/code/.venv/bin/python: No module named pytest


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scikit-learn` to the project's `requirements.txt` and `pip install scikit-learn`.
- **Verified**: this loads **20640** real records with fields: MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from sklearn.datasets import fetch_california_housing

data = fetch_california_housing()
print(f"RECORDS={len(data.data)}")
print(f"FIELDS={','.join(data.feature_names)}")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
