# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- results/mixed_effects_summary.csv: header only, ZERO data rows — the analysis produced no rows

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: results/mixed_effects_summary.csv: header only, ZERO data rows — the analysis produced no rows; 3 command(s) failed: python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 (rc=1); python -m pytest -q code/tests (rc=1); 4 declared deliverable(s) absent: data/results/mixed_effects_summary.csv; data/results/partial_spearman_exploratory.csv; data/results/permutation_pvalues.csv

## Failing / missing run-book commands

- python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1
/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/regression/mixed_linear_model.py:1634: UserWarning: Random effects covariance is singular
  warnings.warn(msg)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/regression/mixed_linear_model.py:2054: UserWarning: The random effects covariance matrix is singular.
  warnings.warn(_warn_cov_sing)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/regression/mixed_linear_model.py:2237: ConvergenceWarning: The MLE may be on the boundary of the parameter space.
  warnings.warn(msg, ConvergenceWarning)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/regression/mixed_linear_model.py:2245: UserWarning: The random effects covariance matrix is singular.
  warnings.warn(_warn_cov_sing)
2026-10-13 09:22:25,806 ERROR src.pipeline.mixed_effects: MixedLM failed for taxon taxon_b: Singular matrix
2026-10-13 09:22:25,806 ERROR src.pipeline.permutation: Failed to fit taxon taxon_b: Singular matrix
2026-10-13 09:22:25,809 ERROR __main__: Permutation stage failed: You are trying to merge on object and datetime64[ns] columns for key 'visit_date'. If you wish to proceed you should use pd.concat

- python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 -> rc=1
_stage
    result = func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/permutation.py", line 192, in run_permutation
    merged_perm = clr_df.merge(permuted_clinical, on=["patient_id", "visit_date"], how="inner")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 10832, in merge
    return merge(
           ^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/reshape/merge.py", line 170, in merge
    op = _MergeOperation(
         ^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/reshape/merge.py", line 807, in __init__
    self._maybe_coerce_merge_keys()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/reshape/merge.py", line 1514, in _maybe_coerce_merge_keys
    raise ValueError(msg)
ValueError: You are trying to merge on object and datetime64[ns] columns for key 'visit_date'. If you wish to proceed you should use pd.concat

- python -m pytest -q code/tests -> rc=1
ion.py::test_permutation_runs
projects/PROJ-331-investigating-the-correlation-between-gu/code/tests/test_permutation.py::test_permutation_runs
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/regression/mixed_linear_model.py:2245: UserWarning: The random effects covariance matrix is singular.
    warnings.warn(_warn_cov_sing)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/contract/test_contracts.py::test_taxa_correlations_contract
FAILED code/tests/test_correlation.py::test_correlation_produces_results - Va...
FAILED code/tests/test_mixed_effects.py::test_mixed_effects_recovers_known_interaction
FAILED code/tests/test_permutation.py::test_permutation_runs - ValueError: Yo...
FAILED code/tests/test_preprocess.py::test_zero_variance_covariate_detected
FAILED code/tests/test_runtime_budget.py::test_runtime_logging_and_budget - A...
FAILED code/tests/test_slopes.py::test_compute_outcome_slopes_simple - assert...
ERROR code/tests/test_runtime_budget.py::test_runtime_logging_and_budget - At...
7 failed, 22 passed, 8 warnings, 1 error in 2.26s



## Declared deliverables still missing

- data/results/mixed_effects_summary.csv
- data/results/partial_spearman_exploratory.csv
- data/results/permutation_pvalues.csv
- data/results/taxa_correlations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/mixed_effects_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us3.py` — IS a run-book command
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mixed_effects_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/partial_spearman_exploratory.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/partial_spearman_exploratory.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us3.py` — IS a run-book command
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/taxa_correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/taxa_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
