# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1)

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 13:26:01,854 ERROR src.data.featurize: Failed to read raw CSV at data/raw/materials_defects.csv: [Errno 2] No such file or directory: 'data/raw/materials_defects.csv'
2026-10-22 13:26:01,854 ERROR src.data.featurize: Feature computation failed: [Errno 2] No such file or directory: 'data/raw/materials_defects.csv'

- python -m src.validate data/processed/features.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 23, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 20, in main
    _impl_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/data/validate.py", line 40, in main
    raise ValueError("Insufficient rows (<50) for 5-fold CV")
ValueError: Insufficient rows (<50) for 5-fold CV

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

projects/PROJ-542-predicting-defect-formation-energies-in-/code/tests/test_pipeline_entry.py::test_pipeline_entry
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_pipeline_entry.py::test_pipeline_entry - SystemExit: 2
FAILED src/tests/test_descriptor_gaps.py::test_check_descriptor_gaps_with_missing
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - AssertionErro...
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
FAILED tests/test_split.py::test_split_dataset_basic - assert 2 <= 1
FAILED tests/test_split.py::test_cli_execution - AssertionError: assert False
6 failed, 5 passed, 14 warnings in 3.20s



## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Download / stream** this exact data URL directly (do NOT `pip install` it — it is a data file, not a package): `https://zenodo.org/records/10028980/files/Data.csv?download=1`
- **Verified**: streaming a sample yielded **178** real records with fields: OQMD_ID_pristine, 0-norm, 2-norm, 3-norm, 5-norm, 7-norm, 10-norm, MagpieData minimum Number, MagpieData maximum Number, MagpieData range Number, MagpieData mean Number, MagpieData avg_dev Number, MagpieData mode Number, MagpieData minimum MendeleevNumber, MagpieData maximum MendeleevNumber, MagpieData range MendeleevNumber, MagpieData mean MendeleevNumber, MagpieData avg_dev MendeleevNumber, MagpieData mode MendeleevNumber, MagpieData minimum AtomicWeight, MagpieData maximum AtomicWeight, MagpieData range AtomicWeight, MagpieData mean AtomicWeight, MagpieData avg_dev AtomicWeight, MagpieData mode AtomicWeight, MagpieData minimum MeltingT, MagpieData maximum MeltingT, MagpieData range MeltingT, MagpieData mean MeltingT, MagpieData avg_dev MeltingT, MagpieData mode MeltingT, MagpieData minimum Column, MagpieData maximum Column, MagpieData range Column, MagpieData mean Column, MagpieData avg_dev Column, MagpieData mode Column, MagpieData minimum Row, MagpieData maximum Row, MagpieData range Row, MagpieData mean Row, MagpieData avg_dev Row, MagpieData mode Row, MagpieData minimum CovalentRadius, MagpieData maximum CovalentRadius, MagpieData range CovalentRadius, MagpieData mean CovalentRadius, MagpieData avg_dev CovalentRadius, MagpieData mode CovalentRadius, MagpieData minimum Electronegativity, MagpieData maximum Electronegativity, MagpieData range Electronegativity, MagpieData mean Electronegativity, MagpieData avg_dev Electronegativity, MagpieData mode Electronegativity, MagpieData minimum NsValence, MagpieData maximum NsValence, MagpieData range NsValence, MagpieData mean NsValence, MagpieData avg_dev NsValence, MagpieData mode NsValence, MagpieData minimum NpValence, MagpieData maximum NpValence, MagpieData range NpValence, MagpieData mean NpValence, MagpieData avg_dev NpValence, MagpieData mode NpValence, MagpieData minimum NdValence, MagpieData maximum NdValence, MagpieData range NdValence, MagpieData mean NdValence, MagpieData avg_dev NdValence, MagpieData mode NdValence, MagpieData minimum NfValence, MagpieData maximum NfValence, MagpieData range NfValence, MagpieData mean NfValence, MagpieData avg_dev NfValence, MagpieData mode NfValence, MagpieData minimum NValence, MagpieData maximum NValence, MagpieData range NValence, MagpieData mean NValence, MagpieData avg_dev NValence, MagpieData mode NValence, MagpieData minimum NsUnfilled, MagpieData maximum NsUnfilled, MagpieData range NsUnfilled, MagpieData mean NsUnfilled, MagpieData avg_dev NsUnfilled, MagpieData mode NsUnfilled, MagpieData minimum NpUnfilled, MagpieData maximum NpUnfilled, MagpieData range NpUnfilled, MagpieData mean NpUnfilled, MagpieData avg_dev NpUnfilled, MagpieData mode NpUnfilled, MagpieData minimum NdUnfilled, MagpieData maximum NdUnfilled, MagpieData range NdUnfilled, MagpieData mean NdUnfilled, MagpieData avg_dev NdUnfilled, MagpieData mode NdUnfilled, MagpieData minimum NfUnfilled, MagpieData maximum NfUnfilled, MagpieData range NfUnfilled, MagpieData mean NfUnfilled, MagpieData avg_dev NfUnfilled, MagpieData mode NfUnfilled, MagpieData minimum NUnfilled, MagpieData maximum NUnfilled, MagpieData range NUnfilled, MagpieData mean NUnfilled, MagpieData avg_dev NUnfilled, MagpieData mode NUnfilled, MagpieData minimum GSvolume_pa, MagpieData maximum GSvolume_pa, MagpieData range GSvolume_pa, MagpieData mean GSvolume_pa, MagpieData avg_dev GSvolume_pa, MagpieData mode GSvolume_pa, MagpieData minimum GSbandgap, MagpieData maximum GSbandgap, MagpieData range GSbandgap, MagpieData mean GSbandgap, MagpieData avg_dev GSbandgap, MagpieData mode GSbandgap, MagpieData minimum GSmagmom, MagpieData maximum GSmagmom, MagpieData range GSmagmom, MagpieData mean GSmagmom, MagpieData avg_dev GSmagmom, MagpieData mode GSmagmom, MagpieData minimum SpaceGroupNumber, MagpieData maximum SpaceGroupNumber, MagpieData range SpaceGroupNumber, MagpieData mean SpaceGroupNumber, MagpieData avg_dev SpaceGroupNumber, MagpieData mode SpaceGroupNumber, avg s valence electrons, avg p valence electrons, avg d valence electrons, avg f valence electrons, compound possible, max ionic char, avg ionic char, NN_binary_Evf_avg_weighted, tot_binary_Evf_min, NN_binary_Evf_avg_weighted_bl, OpCOM_site_plus_bandgap, formation_energy, redox_pot_max, bond_dissociation_energy_sum, electronegativity_avg, electronegativity_1stNN, fraction_O_electrons, n_O_atoms, tot_n_electrons, tot_n_atoms, fraction_O_atoms, bandgap, OpCOM_tot_plus_tq_bandgap, stability, OQMD_ID_defect, evf.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
url = "https://zenodo.org/records/10028980/files/Data.csv?download=1"
df = pd.read_csv(url)
print(f"RECORDS={len(df)}")
print("FIELDS=" + ",".join(df.columns.tolist()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
