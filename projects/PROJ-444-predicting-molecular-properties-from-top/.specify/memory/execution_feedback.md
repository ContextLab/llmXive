# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/06_diagnostics.py; python code/05_sensitivity_analysis.py --resolutions 10 20 30; 4 command(s) failed: python code/01_data_ingestion.py --source pubchem (rc=1); python code/02_tda_computation.py --resolution 10 (rc=1); python code/04_model_training.py (rc=1); 6 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/filtered_esol.csv; data/processed/power_analysis_report.json

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source pubchem -> rc=1
2026-10-12 20:17:10,936 - data_ingestion - ERROR - Unknown source 'pubchem'. Use 'skfp' or 'url'.


- python code/02_tda_computation.py --resolution 10 -> rc=1
Error: Expected filtered dataset at /home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/data/processed/filtered_esol.csv (produced by T001).


- python code/04_model_training.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/04_model_training.py", line 21, in <module>
    from sklearn.metrics import r2_score, rmse
ImportError: cannot import name 'rmse' from 'sklearn.metrics' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/lib/python3.11/site-packages/sklearn/metrics/__init__.py)

- python code/06_diagnostics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/06_diagnostics.py': [Errno 2] No such file or directory

- python code/05_sensitivity_analysis.py --resolutions 10 20 30 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-444-predicting-molecular-properties-from-top/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/05_sensitivity_analysis.py': [Errno 2] No such file or directory

- python code/07_resource_monitor.py -> rc=1
2026-10-12 20:17:12,687 - ERROR - No command provided to monitor.



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/filtered_esol.csv
- data/processed/power_analysis_report.json
- data/processed/scaffold_counts.json
- data/processed/splits.json
- data/processed/traditional_descriptors.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scikit-fingerprints` to the project's `requirements.txt` and `pip install scikit-fingerprints`.
- **Verified**: this loads **4200** real records with fields: smiles, logP, molecule_id.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from skfp.datasets import moleculenet as mn

# Load the dataset (returns a tuple of features and targets)
X, y = mn.load_lipophilicity()

# Construct a DataFrame with the expected columns
df = pd.DataFrame({"smiles": X, "logP": y})
df["molecule_id"] = df.index.astype(str)

print(f"RECORDS={len(df)}")
print("FIELDS=" + ",".join(df.columns))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/combined_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — NOT invoked by the run-book
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/combined_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_esol.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/02_tda_computation.py` — IS a run-book command
    - `code/tests/test_tda_feature_matrix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_esol.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/power_analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaffold_counts.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/scaffold_counts.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/splits.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_ingestion.py` — IS a run-book command
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/splits.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/traditional_descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/traditional_descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
