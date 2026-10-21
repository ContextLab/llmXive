# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success`
  - script usage: `ingest.py [-h] [--output OUTPUT] [--raw RAW [RAW ...]]`
  - argparse error: `ingest.py: error: unrecognized arguments: # downloads, checksums, merges, proxy calc; exits 0 on success`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 command(s) failed: bash scripts/env_check.sh (rc=1); python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success (rc=2); python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation (rc=1); 5 declared deliverable(s) absent: data/processed/unified_fatigue.csv; data/raw/checksums.json; data/results/model_performance.csv

## Failing / missing run-book commands

- bash scripts/env_check.sh -> rc=1

IMPORT FAILURE (mandatory): No module named 'torch'

- python -m src.ingest.ingest          # downloads, checksums, merges, proxy calc; exits 0 on success -> rc=2

usage: ingest.py [-h] [--output OUTPUT] [--raw RAW [RAW ...]]
                 [--limit-rows LIMIT_ROWS]
ingest.py: error: unrecognized arguments: # downloads, checksums, merges, proxy calc; exits 0 on success

- python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.preprocess.preprocess' (ModuleNotFoundError: No module named 'src.preprocess')

- python -m src.models.train --feature-set A   # process‑only -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set B   # process + measured stress (balanced subset) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.train --feature-set C   # process + material props (+ proxy stress) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --compare A B   # Wilcoxon signed‑rank test (≥10 % MAPE improvement required) -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.models.evaluate --cross-material  # transfer learning ΔMAPE + permutation test -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.models.evaluate' (ModuleNotFoundError: No module named 'src.models')

- python -m src.mediation.bootstrap_mediation --resamples 10000 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-291-predicting-the-impact-of-residual-stress/bin/python: Error while finding module specification for 'src.mediation.bootstrap_mediation' (ModuleNotFoundError: No module named 'src.mediation')

- python -m pytest -q -> rc=1
/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/ingest/ingest.py:103: FutureWarning: A value is trying to be set on a copy of a DataFrame or Series through chained assignment using an inplace method.
  The behavior will change in pandas 3.0. This inplace method will never work because the intermediate object on which we are setting values always behaves as a copy.
  
  For example, when doing 'df[col].method(value, inplace=True)', try using 'df.method({col: value}, inplace=True)' or df[col] = df[col].method(value) instead, to perform the operation inplace on the original object.
  
  
    df[col].fillna(median_val, inplace=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_env_check.py::test_env_check_exits_successfully - Asse...
FAILED code/tests/test_env_check.py::test_checksums_match_files - AssertionEr...
FAILED tests/test_features.py::test_feature_sets_build_correctly - assert 8 == 4
FAILED tests/test_ingest.py::test_run_ingest_creates_unified_csv - ValueError...
4 failed, 1 passed, 1 warning in 1.39s



## Declared deliverables still missing

- data/processed/unified_fatigue.csv
- data/raw/checksums.json
- data/results/model_performance.csv
- data/results/proxy_agreement.csv
- data/results/runtime_summary.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/unified_fatigue.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest/ingest.py` — NOT invoked by the run-book
    - `code/src/build_features.py` — NOT invoked by the run-book
    - `code/src/proxy_agreement.py` — NOT invoked by the run-book
    - `code/src/run_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_fatigue.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/env_check.py` — NOT invoked by the run-book
    - `code/tests/test_env_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_performance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/model_performance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/proxy_agreement.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/proxy_agreement.py` — NOT invoked by the run-book
    - `code/src/run_e2e.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/proxy_agreement.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/runtime_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/run_e2e.py` — NOT invoked by the run-book
    - `code/src/timing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/runtime_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
