# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/validation_audit.py; 8 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/data/fingerprint.py (rc=1); 13 declared deliverable(s) absent: data/derived/baseline_metrics.csv; data/derived/baseline_residuals.png; data/derived/baseline_test_predictions.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
:22:01,742 - __main__ - WARNING - Failed to fetch WaterSolubility for CID 1964: 'Compound' object has no attribute 'water_solubility'
2026-10-19 13:22:01,742 - __main__ - WARNING - Failed to fetch BoilingPoint for CID 1964: 'Compound' object has no attribute 'boiling_point'
2026-10-19 13:22:01,742 - __main__ - WARNING - Failed to fetch RecordType for CID 1964: 'Compound' object has no attribute 'record_type'
2026-10-19 13:22:01,743 - __main__ - ERROR - Failed to fetch data for CID 1964: 'Compound' object has no attribute 'record_type'
2026-10-19 13:22:02,072 - __main__ - WARNING - Failed to fetch WaterSolubility for CID 1973: 'Compound' object has no attribute 'water_solubility'
2026-10-19 13:22:02,073 - __main__ - WARNING - Failed to fetch BoilingPoint for CID 1973: 'Compound' object has no attribute 'boiling_point'
2026-10-19 13:22:02,073 - __main__ - WARNING - Failed to fetch RecordType for CID 1973: 'Compound' object has no attribute 'record_type'
2026-10-19 13:22:02,073 - __main__ - ERROR - Failed to fetch data for CID 1973: 'Compound' object has no attribute 'record_type'
2026-10-19 13:22:02,074 - __main__ - ERROR - No data fetched. Check CID list and PubChemPy connectivity.

- python code/data/preprocess.py -> rc=1

2026-10-19 13:22:02,537 - __main__ - ERROR - Raw data file not found: data/raw/pubchem_raw.csv. Run T008 first.

- python code/data/fingerprint.py -> rc=1

2026-10-19 13:22:03,496 - __main__ - INFO - Ensured output directories: [PosixPath('data/processed'), PosixPath('data/derived')]
2026-10-19 13:22:03,497 - __main__ - ERROR - Open Babel (obabel) not found in PATH. Please install it.
2026-10-19 13:22:03,497 - __main__ - ERROR - Open Babel not available. Cannot proceed.

- python code/models/baseline.py -> rc=1
ope/code/models/baseline.py", line 87, in process_dataset
    df = pd.read_csv(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/derived/diverse_subset.csv'

- python code/models/rf.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/models/rf.py", line 33, in <module>
    from code.utils.config import get_runtime_config, get_joblib_parallel_backend
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/utils/config.py", line 20, in <module>
    from data.preprocess import load_preprocessed_data
ModuleNotFoundError: No module named 'data.preprocess'

- python code/analysis/stats.py -> rc=1
2026-10-19 13:22:05,917 - stats - INFO - Generating Experimental Validation Protocol (T058)...
ERROR: Metadata file not found at data/raw/dataset_metadata.json. Run T031 first.


- python code/analysis/explainability.py -> rc=1
):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 490, in main
    model = load_model()
            ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 72, in load_model
    raise FileNotFoundError(f"Model file not found: {model_path}")
FileNotFoundError: Model file not found: data/models/final_model.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 532, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 490, in main
    model = load_model()
            ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/explainability.py", line 72, in load_model
    raise FileNotFoundError(f"Model file not found: {model_path}")
FileNotFoundError: Model file not found: data/models/final_model.pkl

- python code/analysis/validation_audit.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-324-predicting-molecular-properties-from-ope/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/validation_audit.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=4

ImportError while loading conftest '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/tests/conftest.py'.
tests/conftest.py:26: in <module>
    @pytest.fixture(scope="session")
E   NameError: name 'pytest' is not defined


## Declared deliverables still missing

- data/derived/baseline_metrics.csv
- data/derived/baseline_residuals.png
- data/derived/baseline_test_predictions.csv
- data/derived/conformational_limitations.csv
- data/derived/data_quality_report.csv
- data/derived/deviation_contexts.csv
- data/derived/rf_test_predictions.csv
- data/derived/shap_interaction.npy
- data/derived/shap_interactions.png
- data/derived/test_set.csv
- data/derived/train_set.csv
- data/raw/dataset_metadata.json
- data/raw/pubchem_raw.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `PubChemPy` to the project's `requirements.txt` and `pip install PubChemPy`.
- **Verified**: this loads **3** real records with fields: CompoundID, SMILES, MolecularFormula, MolecularWeight, LogP, ExperimentalOrComputedFlag.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pubchempy as pcp
cids = [2244, 5957, 702]
compounds = pcp.get_compounds(cids, 'cid')
records = []
for c in compounds:
    rec = {
        'CompoundID': c.cid,
        'SMILES': getattr(c, 'isomeric_smiles', None),
        'MolecularFormula': getattr(c, 'molecular_formula', None),
        'MolecularWeight': getattr(c, 'molecular_weight', None),
        'LogP': getattr(c, 'xlogp', None),
        'ExperimentalOrComputedFlag': None
    }
    records.append(rec)
print(f"RECORDS={len(records)}")
if records:
    print("FIELDS=" + ",".join(records[0].keys()))
else:
    print("FIELDS=")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/baseline_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/baseline_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/baseline_residuals.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/baseline_residuals.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/baseline_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/baseline_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/conformational_limitations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/conformational_limitations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/data_quality_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/data_quality_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/deviation_contexts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/deviation_contexts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rf_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/models/rf.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/rf_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/shap_interaction.npy` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/shap_interaction.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/shap_interactions.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/shap_interactions.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/fingerprint.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
    - `code/models/rf.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fingerprint.py` — IS a run-book command
    - `code/data/fingerprints.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/models/baseline.py` — IS a run-book command
    - `code/models/random_forest.py` — NOT invoked by the run-book
    - `code/models/rf.py` — IS a run-book command
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dataset_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/dataset_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pubchem_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/pubchem_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
