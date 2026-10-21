# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/missing_flags.json, data/processed/unified_fatigue.csv, data/raw/checksums.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/missing_flags.json, data/processed/unified_fatigue.csv, data/raw/checksums.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 8 command(s) failed: python -m src.preprocess.preprocess   # unit conversion, imputation, contract validation (rc=1); python -m src.models.train --feature-set A   # process‑only (rc=1); python -m src.models.train --feature-set B   # process + measured stress (balanced subset) (rc=1); 3 declared deliverable(s) absent: data/results/model_performance.csv; data/results/proxy_agreement.csv; data/results/runtime_summary.csv

## Failing / missing run-book commands

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
sed/scaler_C.pkl
INFO     code.src.build_features:build_features.py:94 Feature set C written to /home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/processed/feature_set_C.csv
INFO     code.src.build_features:build_features.py:168 All feature sets built successfully.
=============================== warnings summary ===============================
projects/PROJ-291-predicting-the-impact-of-residual-stress/tests/test_ingest.py::test_run_ingest_creates_unified_csv
  /home/runner/work/llmXive/llmXive/projects/PROJ-291-predicting-the-impact-of-residual-stress/code/ingest/ingest.py:217: FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version. Call result.infer_objects(copy=False) instead. To opt-in to the future behavior, set `pd.set_option('future.no_silent_downcasting', True)`
    unified = unified.fillna(0)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_features.py::test_feature_sets_build_correctly - assert 8 == 4
1 failed, 4 passed, 1 warning in 1.60s



## Declared deliverables still missing

- data/results/model_performance.csv
- data/results/proxy_agreement.csv
- data/results/runtime_summary.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

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
