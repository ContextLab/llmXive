# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit <maximum_subjects>  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42`
  - script usage: `run_pipeline.py [-h] [--subjects SUBJECTS] [--dry-run]`
  - argparse error: `run_pipeline.py: error: argument --subject-limit: invalid int value: '<maximum_subjects>'`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit <maximum_subjects>  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 (rc=2); python -m pytest -v tests/ (rc=2); 6 declared deliverable(s) absent: data/derived/clean_subjects.parquet; data/derived/entropy_matrix.parquet; data/derived/entropy_metadata.json

## Failing / missing run-book commands

- python -m src.run_pipeline  --hcp-token $HCP_TOKEN  --subject-limit <maximum_subjects>  --fd-threshold 0.2  --entropy-r 0.15  --entropy-m 2  --scales 1 2 3 4 5  --n-permutations 1000  --seed 42 -> rc=2

usage: run_pipeline.py [-h] [--subjects SUBJECTS] [--dry-run]
run_pipeline.py: error: argument --subject-limit: invalid int value: '<maximum_subjects>'

- python -m pytest -v tests/ -> rc=2
it/test_qc.py ____________________
tests/unit/test_qc.py:16: in <module>
    import pandas as pd
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pandas/__init__.py:22: in <module>
    from pandas.compat import (
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pandas/compat/__init__.py:29: in <module>
    from pandas.compat.pyarrow import (
../../.llmxive-venvs/PROJ-754-linking-resting-state-fmri-entropy-to-re/lib/python3.11/site-packages/pandas/compat/pyarrow.py:14: in <module>
    _palv = Version(Version(pa.__version__).base_version)
E   AttributeError: module 'pyarrow' has no attribute '__version__'
=========================== short test summary info ============================
ERROR tests/unit/test_entropy.py - AttributeError: module 'pyarrow' has no at...
ERROR tests/unit/test_power_pre.py - AttributeError: module 'pyarrow' has no ...
ERROR tests/unit/test_qc.py - AttributeError: module 'pyarrow' has no attribu...
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 0.26s ===============================



## Declared deliverables still missing

- data/derived/clean_subjects.parquet
- data/derived/entropy_matrix.parquet
- data/derived/entropy_metadata.json
- data/derived/invalid_parcels.csv
- data/derived/subject_qc.csv
- data/raw/dsrt_scores.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/clean_subjects.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/clean_subjects.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/entropy_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
    - `code/src/stats/model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/entropy_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/entropy_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/entropy_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/invalid_parcels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/analysis/entropy.py` — NOT invoked by the run-book
    - `code/src/compute_entropy.py` — NOT invoked by the run-book
    - `code/tests/unit/test_entropy.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/invalid_parcels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/subject_qc.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/subject_qc.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dsrt_scores.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/download_hcp.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
    - `code/src/pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dsrt_scores.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
