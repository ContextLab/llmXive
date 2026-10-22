# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --step fetch_and_preprocess (rc=1); python code/main.py --step feature_selection (rc=1); python code/main.py --step train (rc=1); 1 declared deliverable(s) absent: data/processed/cluster_map.csv

## Failing / missing run-book commands

- python code/main.py --step fetch_and_preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 19, in <module>
    from data.feature_selection import main as feature_selection_main
ModuleNotFoundError: No module named 'data.feature_selection'

- python code/main.py --step feature_selection -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 19, in <module>
    from data.feature_selection import main as feature_selection_main
ModuleNotFoundError: No module named 'data.feature_selection'

- python code/main.py --step train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 19, in <module>
    from data.feature_selection import main as feature_selection_main
ModuleNotFoundError: No module named 'data.feature_selection'

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 19, in <module>
    from data.feature_selection import main as feature_selection_main
ModuleNotFoundError: No module named 'data.feature_selection'

- python code/main.py --step verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 19, in <module>
    from data.feature_selection import main as feature_selection_main
ModuleNotFoundError: No module named 'data.feature_selection'

- python -m pytest tests/ -v -> rc=2
 V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("rmse")

tests/contract/validators.py:100
  /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/contract/validators.py:100: PydanticDeprecatedSince20: Pydantic V1 style `@validator` validators are deprecated. You should migrate to Pydantic V2 style `@field_validator` validators, see the migration guide for more details. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    @validator("baseline_r2")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 5 warnings, 1 error in 0.84s =========================



## Declared deliverables still missing

- data/processed/cluster_map.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Download / stream** this exact data URL directly (do NOT `pip install` it — it is a data file, not a package): `https://huggingface.co/datasets/n0w0f/qm9-csv/resolve/main/qm9_dataset.csv`
- **Verified**: streaming a sample yielded **1376** real records with fields: inchi, smiles, rotational_constant_a, rotational_constant_b, rotational_constant_c, dipole_moment, polarizability, homo, lumo, gap, r2, zero_point_energy, u0, u298, h298, g298, heat_capacity.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
url = 'https://huggingface.co/datasets/n0w0f/qm9-csv/resolve/main/qm9_dataset.csv'
# Load the QM9 CSV directly from the raw URL
df = pd.read_csv(url)
print(f"RECORDS={len(df)}")
# Identify the requested fields (case‑insensitive match)
desired = {'smiles', 'molecule_id'}
found = [c for c in df.columns if c.lower() in desired]
print(f"FIELDS={','.join(found)}")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cluster_map.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/feature_clustering.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/models/generate_shap_report.py` — NOT invoked by the run-book
    - `code/models/generate_stability_report.py` — NOT invoked by the run-book
    - `code/models/interpret.py` — NOT invoked by the run-book
    - `code/models/stability_analysis.py` — NOT invoked by the run-book
    - `code/utils/checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cluster_map.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
