# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/persistence_images_10x10.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/persistence_images_10x10.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/persistence_images_10x10.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/persistence_images_10x10.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/06_diagnostics.py; python code/05_sensitivity_analysis.py --resolutions 10 20 30; 4 command(s) failed: python code/01_data_ingestion.py --source pubchem (rc=1); python code/02_tda_computation.py --resolution 10 (rc=1); python code/04_model_training.py (rc=1); 2 declared deliverable(s) absent: data/processed/combined_features.csv; data/processed/traditional_descriptors.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py --source pubchem -> rc=1
2026-10-12 21:14:10,872 - data_ingestion - ERROR - Unknown source 'pubchem'. Use 'skfp' or 'url'.


- python code/02_tda_computation.py --resolution 10 -> rc=1
^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/utils/persistence_utils.py", line 121, in build_shortest_path_filtration
    nodes = list(graph.nodes())
                 ^^^^^^^^^^^
AttributeError: 'numpy.ndarray' object has no attribute 'nodes'

2026-10-12 21:14:18,251 - tda_computation - ERROR - Unhandled exception for 4196: Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/02_tda_computation.py", line 181, in process_molecule
    filtration = build_shortest_path_filtration(sp_matrix)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-444-predicting-molecular-properties-from-top/code/utils/persistence_utils.py", line 121, in build_shortest_path_filtration
    nodes = list(graph.nodes())
                 ^^^^^^^^^^^
AttributeError: 'numpy.ndarray' object has no attribute 'nodes'

2026-10-12 21:14:18,254 - tda_computation - WARNING - No valid molecules processed; created empty CSV with header.
TDA feature generation completed in 6.67s – processed: 0, failed: 4197


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
2026-10-12 21:14:19,332 - ERROR - No command provided to monitor.



## Declared deliverables still missing

- data/processed/combined_features.csv
- data/processed/traditional_descriptors.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scikit-fingerprints` to the project's `requirements.txt` and `pip install scikit-fingerprints`.
- **Verified**: this loads **4200** real records with fields: SMILES, logP, MoleculeID.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from skfp.datasets.moleculenet import load_lipophilicity

# Load the dataset (returns a tuple: (features, targets))
features, targets = load_lipophilicity()

# Ensure features are in a pandas Series/DataFrame with a SMILES column
if isinstance(features, pd.DataFrame):
    if 'smiles' in features.columns:
        smiles_series = features['smiles']
    else:
        # If the DataFrame itself is just a single column of SMILES
        smiles_series = features.iloc[:, 0]
elif isinstance(features, pd.Series):
    smiles_series = features
else:
    # Fallback: try to convert to a Series
    smiles_series = pd.Series(features)

# Construct a unified DataFrame
df = pd.DataFrame({
    'smiles': smiles_series,
    'exp': pd.Series(targets)
})

# Verify required columns exist
if 'smiles' not in df.columns:
    raise KeyError('Column "smiles" not found in dataset')
if 'exp' not in df.columns:
    raise KeyError('Column "exp" (logP) not found in dataset')

# Rename to match required field names
df = df.rename(columns={'smiles': 'SMILES', 'exp': 'logP'})

# Add MoleculeID if missing
if 'MoleculeID' not in df.columns:
    df['MoleculeID'] = df.index.astype(str)

print(f'RECORDS={len(df)}')
print('FIELDS=' + ','.join(df.columns.tolist()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/combined_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — NOT invoked by the run-book
    - `code/04_model_training.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/combined_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/traditional_descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_feature_engineering.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/traditional_descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
