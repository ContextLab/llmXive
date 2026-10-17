# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python code/download_cod.py --output data/raw/cod.jsonl; python code/generate_smiles.py  --input data/raw/cod.jsonl  --output data/processed/with_smiles.csv; python code/compute_descriptors.py  --input data/processed/with_smiles.csv  --output data/processed/with_descriptors.csv; 1 command(s) failed: python -m pytest tests/ (rc=2); 1 declared deliverable(s) absent: data/dataset_filtered.csv

## Failing / missing run-book commands

- python code/download_cod.py --output data/raw/cod.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/download_cod.py': [Errno 2] No such file or directory

- python code/generate_smiles.py  --input data/raw/cod.jsonl  --output data/processed/with_smiles.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/generate_smiles.py': [Errno 2] No such file or directory

- python code/compute_descriptors.py  --input data/processed/with_smiles.csv  --output data/processed/with_descriptors.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/compute_descriptors.py': [Errno 2] No such file or directory

- python code/encode_smiles.py  --input data/processed/with_descriptors.csv  --output data/processed/full_feature_matrix.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/encode_smiles.py': [Errno 2] No such file or directory

- python code/train_model.py  --data data/processed/full_feature_matrix.csv  --model-primary data/artifacts/model_primary.pt  --model-full data/artifacts/model_full.pt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/train_model.py': [Errno 2] No such file or directory

- python code/evaluate_model.py  --model data/artifacts/model_primary.pt  --data data/processed/full_feature_matrix.csv  --output data/artifacts/validation_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/evaluate_model.py': [Errno 2] No such file or directory

- python code/sensitivity_analysis.py  --model data/artifacts/model_primary.pt  --data data/processed/full_feature_matrix.csv  --output data/artifacts/sensitivity_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/sensitivity_analysis.py': [Errno 2] No such file or directory

- python code/report_generator.py  --validation data/artifacts/validation_report.json  --output data/artifacts/report.html -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-511-predicting-molecular-packing-efficiency-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/report_generator.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
 named 'evaluate'
_ ERROR collecting projects/PROJ-511-predicting-molecular-packing-efficiency-/tests/unit/test_add_3d_descriptors.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/tests/unit/test_add_3d_descriptors.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_add_3d_descriptors.py:13: in <module>
    from add_3d_descriptors import (
E   ImportError: cannot import name 'generate_conformer' from 'add_3d_descriptors' (/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/tests/unit/../../code/add_3d_descriptors.py)
=========================== short test summary info ============================
ERROR tests/integration/test_train_evaluate.py
ERROR tests/unit/test_add_3d_descriptors.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 2.47s ===============================



## Declared deliverables still missing

- data/dataset_filtered.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/dataset_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/add_3d_descriptors.py` — NOT invoked by the run-book
    - `code/filter_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/dataset_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
