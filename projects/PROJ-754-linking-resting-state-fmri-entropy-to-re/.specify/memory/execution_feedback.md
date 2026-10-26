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
k/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 34 items / 1 error

==================================== ERRORS ====================================
_________________ ERROR collecting tests/unit/test_entropy.py __________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-754-linking-resting-state-fmri-entropy-to-re/tests/unit/test_entropy.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_entropy.py:21: in <module>
    from src.analysis.entropy import multiscale_entropy, _row_checksum
E   ModuleNotFoundError: No module named 'src.analysis.entropy'
=========================== short test summary info ============================
ERROR tests/unit/test_entropy.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.89s ===============================



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
