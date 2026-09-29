# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/dataset_metadata.json, data/raw/pubchem_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/dataset_metadata.json, data/raw/pubchem_raw.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/data/preprocess.py (rc=1); python code/data/fingerprint.py (rc=1); python code/models/baseline.py (rc=1); 7 declared deliverable(s) absent: data/derived/baseline_test_predictions.csv; data/derived/data_quality_report.csv; data/derived/deviation_contexts.csv

## Failing / missing run-book commands

- python code/data/preprocess.py -> rc=1
    gh_confidence(df)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/data/preprocess.py", line 99, in filter_high_confidence
    valid_rows = df[TARGET_PROPS].notna().any(axis=1)
                 ~~^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/.venv/lib/python3.11/site-packages/pandas/core/frame.py", line 4384, in __getitem__
    indexer = self.columns._get_indexer_strict(key, "columns")[1]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/.venv/lib/python3.11/site-packages/pandas/core/indexes/base.py", line 6302, in _get_indexer_strict
    self._raise_if_missing(keyarr, indexer, axis_name)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/.venv/lib/python3.11/site-packages/pandas/core/indexes/base.py", line 6355, in _raise_if_missing
    raise KeyError(f"{not_found} not in index")
KeyError: "['Solubility', 'Boiling Point'] not in index"
- python code/data/fingerprint.py -> rc=1
    2026-09-29 01:29:18,094 - __main__ - INFO - Ensured output directory: /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/processed
2026-09-29 01:29:18,094 - __main__ - ERROR - Training set not found at /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/train_set.csv. Please ensure T011.5 (Split Dataset) and T010.1 (MaxMin Sampling) are completed.
- python code/models/baseline.py -> rc=1
    2026-09-29 01:29:18,536 - ERROR - Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/diverse_subset.csv
2026-09-29 01:29:18,536 - ERROR - Please ensure T010.1 (Execute MaxMin Sampling) has been completed.
- python code/models/rf.py -> rc=1
    2026-09-29 01:29:20,264 - __main__ - INFO - Loading fingerprints from /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/processed/train_fingerprints.parquet
2026-09-29 01:29:20,264 - __main__ - ERROR - Failed to load training data: Fingerprint file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/processed/train_fingerprints.parquet
- python code/analysis/stats.py -> rc=1
    2026-09-29 01:29:21,426 - __main__ - INFO - Ensured directories exist: data/derived, data/raw, data/processed
2026-09-29 01:29:21,426 - __main__ - INFO - Generating Measurement Standards Audit
2026-09-29 01:29:21,426 - __main__ - INFO - Loaded metadata from data/raw/dataset_metadata.json
2026-09-29 01:29:21,426 - __main__ - ERROR - Required file not found: Test set file not found: data/derived/test_set.csv
2026-09-29 01:29:21,426 - __main__ - ERROR - This task depends on T031, T011.5, T014.5, and T020.1 being completed first.
- python code/analysis/explainability.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 24, in <module>
    logging.FileHandler('logs/explainability.log', mode='a')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/logs/explainability.log'

## Declared deliverables still missing

- data/derived/baseline_test_predictions.csv
- data/derived/data_quality_report.csv
- data/derived/deviation_contexts.csv
- data/derived/rf_test_predictions.csv
- data/derived/shap_interactions.png
- data/derived/test_set.csv
- data/derived/train_set.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PubChemPy` to the project's `requirements.txt` and `pip install PubChemPy`.
- **Verified**: this loads **10** real records with fields: atom_stereo_count, atoms, bond_stereo_count, bonds, cactvs_fingerprint, charge, cid, complexity, conformer_id_3d, conformer_rmsd_3d, connectivity_smiles, coordinate_type, covalent_unit_count, defined_atom_stereo_count, defined_bond_stereo_count, effective_rotor_count_3d, elements, exact_mass, feature_selfoverlap_3d, fingerprint, h_bond_acceptor_count, h_bond_donor_count, heavy_atom_count, inchi, inchikey, isotope_atom_count, iupac_name, mmff94_energy_3d, mmff94_partial_charges_3d, molecular_formula, molecular_weight, monoisotopic_mass, multipoles_3d, pharmacophore_features_3d, rotatable_bond_count, shape_fingerprint_3d, shape_selfoverlap_3d, smiles, tpsa, undefined_atom_stereo_count, undefined_bond_stereo_count, volume_3d, xlogp.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp

cids = [2244, 3672, 5957, 702, 1234, 5281, 5280, 5282, 5283, 5284]
compounds = pcp.get_compounds(cids, 'cid')

print(f"RECORDS={len(compounds)}")
if compounds:
    fields = sorted(compounds[0].to_dict().keys())
    print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/baseline_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/baseline_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/data_quality_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/data_quality_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/deviation_contexts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/deviation_contexts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rf_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/rf.py` — IS a run-book command
    - `code/analysis/explainability.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/rf_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/shap_interactions.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/shap_interactions.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/rf.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/random_forest.py` — NOT invoked by the run-book
    - `code/models/rf.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/fingerprint.py` — IS a run-book command
    - `code/data/fingerprints.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/derived/data_quality_report.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[not_found, Solubility, Boiling Point]`
- PRODUCER(s) to edit: `code/data/preprocess.py`
- CONSUMER(s) that read it: `code/data/preprocess.py`
  → Edit the producer so every required name [not_found, Solubility, Boiling Point] is in `data/derived/data_quality_report.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/derived/test_set.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/rf.py`, `code/data/preprocess.py`, `code/analysis/stats.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/test_set.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/rf.py`, `code/data/preprocess.py`, `code/analysis/stats.py`.

### `data/derived/train_set.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/random_forest.py`, `code/models/rf.py`, `code/data/preprocess.py`, `code/data/fingerprint.py`, `code/data/fingerprints.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/derived/train_set.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/random_forest.py`, `code/models/rf.py`, `code/data/preprocess.py`, `code/data/fingerprint.py`, `code/data/fingerprints.py`.

### `data/raw/chembl_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/chembl_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/preprocess.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/baseline_test_predictions.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/explainability.py`, `code/analysis/stats.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/baseline_test_predictions.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/explainability.py`, `code/analysis/stats.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/diverse_subset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/baseline.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/derived/diverse_subset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/baseline.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/processed/train_fingerprints.parquet`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/random_forest.py`, `code/models/rf.py`, `code/data/fingerprint.py`, `code/data/fingerprints.py`, `code/analysis/explainability.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/data/processed/train_fingerprints.parquet`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/models/random_forest.py`, `code/models/rf.py`, `code/data/fingerprint.py`, `code/data/fingerprints.py`, `code/analysis/explainability.py`.
