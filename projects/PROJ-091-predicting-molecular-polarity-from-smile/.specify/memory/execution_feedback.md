# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/descriptor_names.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/descriptor_names.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/main.py --step fetch_and_preprocess (rc=-1); python code/main.py --step feature_selection (rc=1); python code/main.py --step train (rc=1); 2 declared deliverable(s) absent: data/processed/cluster_map.csv; data/processed/descriptors.parquet

## Failing / missing run-book commands

- python code/main.py --step fetch_and_preprocess -> rc=-1
2026-10-22 02:16:16,395 - main - INFO - Starting pipeline...
2026-10-22 02:16:16,395 - main - INFO - Running data preprocessing (descriptor generation)...
2026-10-22 02:16:16,396 - data.generate_descriptors - INFO - Found 412 total RDKit descriptors, 411 after filtering.
2026-10-22 02:16:16,396 - data.generate_descriptors - INFO - Descriptor names written to /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/data/processed/descriptor_names.json
2026-10-22 02:16:16,396 - data.generate_descriptors - INFO - Downloading QM9 dataset from https://huggingface.co/datasets/n0w0f/qm9-csv/resolve/main/qm9_dataset.csv
2026-10-22 02:16:47,325 - data.generate_descriptors - INFO - Processed 5000 records – Current RSS 327.9 MiB
2026-10-22 02:17:18,852 - data.generate_descriptors - INFO - Processed 10000 records – Current RSS 453.0 MiB
2026-10-22 02:17:50,996 - data.generate_descriptors - INFO - Processed 15000 records – Current RSS 578.0 MiB


[TIMEOUT after 120s]
- python code/main.py --step feature_selection -> rc=1
2026-10-22 02:18:16,471 - main - INFO - Starting pipeline...
2026-10-22 02:18:16,471 - main - INFO - Running feature selection (VIF pruning & clustering)...
2026-10-22 02:18:16,471 - main - ERROR - Feature selection module not found (data/feature_selection.py).
2026-10-22 02:18:16,471 - main - ERROR - Pipeline failed.


- python code/main.py --step train -> rc=1
2026-10-22 02:18:17,057 - main - INFO - Starting pipeline...
2026-10-22 02:18:17,057 - main - ERROR - Training step not yet implemented.
2026-10-22 02:18:17,057 - main - ERROR - Pipeline failed.


- python code/main.py --step analyze -> rc=1
2026-10-22 02:18:17,635 - main - INFO - Starting pipeline...
2026-10-22 02:18:17,635 - main - ERROR - Analysis step not yet implemented.
2026-10-22 02:18:17,635 - main - ERROR - Pipeline failed.


- python code/main.py --step verify -> rc=1
2026-10-22 02:18:18,218 - main - INFO - Starting pipeline...
2026-10-22 02:18:18,218 - main - INFO - Validating artifact integrity (checksums)...
2026-10-22 02:18:18,218 - main - ERROR - Manifest missing 'checksums' key.
2026-10-22 02:18:18,218 - main - ERROR - Pipeline failed.


- python -m pytest tests/ -v -> rc=2
tests/integration/test_full_pipeline.py:34: in <module>
    from models.train_lightgbm import train_lightgbm_model
E   ImportError: cannot import name 'train_lightgbm_model' from 'models.train_lightgbm' (/home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/code/models/train_lightgbm.py)
=============================== warnings summary ===============================
tests/contract/validators.py:55
  /home/runner/work/llmXive/llmXive/projects/PROJ-091-predicting-molecular-polarity-from-smile/tests/contract/validators.py:55: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.14/migration/
    class DescriptorMatrix(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_full_pipeline.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 1 error in 1.74s ==========================



## Declared deliverables still missing

- data/processed/cluster_map.csv
- data/processed/descriptors.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `qm9pack` to the project's `requirements.txt` and `pip install qm9pack`.
- **Verified**: this loads **130831** real records with fields: XYZ_file, Index, SMILES, InChi, N_atoms, Stoichiometry, Elements, XYZ_Ang, Mulliken_pop, Harmonic_Freq_cmi, RotA_GHz, RotB_GHz, RotC_GHz, Dipole_debye, Polarizability_bohr3, HOMO_au, LUMO_au, HOMO_LUMO_gap_au, R2_bohr2, ZPVE_au, InternalEnergy_0K_au, InternalEnergy_298K_au, Enthalphy_298K_au, GibbsFreeEnergy_298K_au, Heatcapacity_Cv_cal_mol_K, A_xx, A_xy, A_yy, A_xz, A_yz, A_zz.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import qm9pack

data = qm9pack.get_data('qm9')
print(f"RECORDS={len(data)}")
print(f"FIELDS={','.join(data.columns)}")
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
