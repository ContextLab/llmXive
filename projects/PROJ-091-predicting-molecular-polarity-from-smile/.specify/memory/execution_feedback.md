# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --step fetch_and_preprocess`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step fetch_and_preprocess`
- run-book command: `python code/main.py --step feature_selection`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step feature_selection`
- run-book command: `python code/main.py --step train`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step train`
- run-book command: `python code/main.py --step analyze`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step analyze`
- run-book command: `python code/main.py --step verify`
  - script usage: `main.py [-h] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --step verify`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --step fetch_and_preprocess (rc=2); python code/main.py --step feature_selection (rc=2); python code/main.py --step train (rc=2); 2 declared deliverable(s) absent: data/processed/cluster_map.csv; data/processed/descriptors.parquet

## Failing / missing run-book commands

- python code/main.py --step fetch_and_preprocess -> rc=2

usage: main.py [-h] [--config CONFIG]
main.py: error: unrecognized arguments: --step fetch_and_preprocess

- python code/main.py --step feature_selection -> rc=2

usage: main.py [-h] [--config CONFIG]
main.py: error: unrecognized arguments: --step feature_selection

- python code/main.py --step train -> rc=2

usage: main.py [-h] [--config CONFIG]
main.py: error: unrecognized arguments: --step train

- python code/main.py --step analyze -> rc=2

usage: main.py [-h] [--config CONFIG]
main.py: error: unrecognized arguments: --step analyze

- python code/main.py --step verify -> rc=2

usage: main.py [-h] [--config CONFIG]
main.py: error: unrecognized arguments: --step verify

- python -m pytest tests/ -v -> rc=2
validators.py:26
  /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/contract/validators.py:26: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    class DescriptorMatrix(BaseModel):

tests/contract/validators.py:51
  /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/contract/validators.py:51: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    class ModelOutput(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 2 warnings, 1 error in 0.83s =========================



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
