# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --step fetch_and_preprocess (rc=1); python code/main.py --step feature_selection (rc=1); python code/main.py --step train (rc=1); 2 declared deliverable(s) absent: data/processed/cluster_map.csv; data/processed/descriptors.parquet

## Failing / missing run-book commands

- python code/main.py --step fetch_and_preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 248, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 219, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python code/main.py --step feature_selection -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 248, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 219, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python code/main.py --step train -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 248, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 219, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python code/main.py --step analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 248, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 219, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python code/main.py --step verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 248, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/main.py", line 219, in main
    setup_logging(level=logging.INFO)
TypeError: setup_logging() got an unexpected keyword argument 'level'

- python -m pytest tests/ -v -> rc=2
ERRORS ====================================
_ ERROR collecting projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/integration/test_full_pipeline.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/integration/test_full_pipeline.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_full_pipeline.py:34: in <module>
    from models.train_lightgbm import train_lightgbm_model
E   ImportError: cannot import name 'train_lightgbm_model' from 'models.train_lightgbm' (/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/train_lightgbm.py)
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.35s ===============================



## Declared deliverables still missing

- data/processed/cluster_map.csv
- data/processed/descriptors.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `qm9pack` to the project's `requirements.txt` and `pip install qm9pack`.
- **Verified**: this loads **130831** real records with fields: XYZ_file, Index, SMILES, InChi, N_atoms, Stoichiometry, Elements, XYZ_Ang, Mulliken_pop, Harmonic_Freq_cmi, RotA_GHz, RotB_GHz, RotC_GHz, Dipole_debye, Polarizability_bohr3, HOMO_au, LUMO_au, HOMO_LUMO_gap_au, R2_bohr2, ZPVE_au, InternalEnergy_0K_au, InternalEnergy_298K_au, Enthalphy_298K_au, GibbsFreeEnergy_298K_au, Heatcapacity_Cv_cal_mol_K, A_xx, A_xy, A_yy, A_xz, A_yz, A_zz.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from qm9pack import get_data

# Load the full QM9 dataset (the typical dataset identifier)
data = get_data('qm9')

if hasattr(data, "shape"):  # likely a pandas DataFrame or similar array-like
    count = len(data)
    fields = list(data.columns)
elif isinstance(data, (list, tuple)):
    count = len(data)
    fields = list(data[0].keys()) if count else []
elif isinstance(data, dict):
    count = len(data)
    first = next(iter(data.values()))
    fields = list(first.keys()) if isinstance(first, dict) else []
else:
    raise TypeError(f"Unsupported data type returned by get_data: {type(data)}")

print(f"RECORDS={count}")
print("FIELDS=" + ",".join(fields))
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
- `data/processed/descriptors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/compute_correlation.py` — NOT invoked by the run-book
    - `code/data/generate_descriptors.py` — NOT invoked by the run-book
    - `code/data/preprocess_2d.py` — NOT invoked by the run-book
    - `code/data/save_descriptors.py` — NOT invoked by the run-book
    - `code/data/split_data.py` — NOT invoked by the run-book
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/models/generate_shap_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
