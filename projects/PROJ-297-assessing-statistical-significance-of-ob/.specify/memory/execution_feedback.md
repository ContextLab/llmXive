# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/loaders.py --output data/processed/ (rc=1); python code/main.py --permutations [variable] --threshold 0.3 --sweep (rc=1)

## Failing / missing run-book commands

- python code/loaders.py --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/loaders.py", line 12, in <module>
    import openpyxl
ModuleNotFoundError: No module named 'openpyxl'
- python code/main.py --permutations [variable] --threshold 0.3 --sweep -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/main.py", line 12, in <module>
    from config import get_config, ensure_dirs
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-297-assessing-statistical-significance-of-ob/code/config.py", line 4, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **699** real records with fields: dataset_name, original_feature_names, continuous_feature_names, num_samples, num_continuous_features, source_repository, download_method.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd

dataset = openml.datasets.get_dataset(15)
X, y, _, _ = dataset.get_data(dataset_format='dataframe')
df = pd.concat([X, y], axis=1)

original_feature_names = list(df.columns)
continuous_feature_names = [c for c in original_feature_names if pd.api.types.is_numeric_dtype(df[c])]
num_samples = df.shape[0]
num_continuous_features = len(continuous_feature_names)
source_repository = getattr(dataset, 'origin', None) or getattr(dataset, 'source', None) or ''
download_method = 'openml.datasets.get_dataset'

print(f"RECORDS={num_samples}")
print("FIELDS=dataset_name,original_feature_names,continuous_feature_names,num_samples,num_continuous_features,source_repository,download_method")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
