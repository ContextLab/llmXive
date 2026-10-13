# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/patient_outcome_slopes.parquet, data/processed/patient_taxon_slopes.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/patient_outcome_slopes.parquet, data/processed/patient_taxon_slopes.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python -m code.src.pipeline.ingest (rc=1); python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m pytest -q code/tests (rc=1); 8 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/raw/ppmi_asv.csv

## Failing / missing run-book commands

- python -m code.src.pipeline.ingest -> rc=1

2026-10-13 04:22:29,418 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-13 04:22:29,418 ERROR __main__: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.
2026-10-13 04:22:29,418 ERROR __main__: Input validation FAILED: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.

- python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1
ork/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 200, in main
    report = validate_inputs(asv_path, clinical_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 159, in validate_inputs
    asv_report = _validate_asv(Path(asv_path))
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 52, in _validate_asv
    _fail(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/ingest.py", line 46, in _fail
    raise FileNotFoundError(message)
FileNotFoundError: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.

- python -m pytest -q code/tests -> rc=1
s(clinical_df)
    
        for _, row in out_df.iterrows():
>           assert np.isclose(row["outcome_slope"], expected[row["patient_id"]], atol=1e-9)
E           assert np.False_
E            +  where np.False_ = <function isclose at 0x7f6386851df0>(-1.6206417078123697e-15, 2.0, atol=1e-09)
E            +    where <function isclose at 0x7f6386851df0> = np.isclose

code/tests/test_slopes.py:135: AssertionError
----------------------------- Captured stderr call -----------------------------
2026-10-13 04:22:31,646 INFO code.src.pipeline.slopes: Computed outcome slopes for 2 patients
------------------------------ Captured log call -------------------------------
INFO     code.src.pipeline.slopes:slopes.py:166 Computed outcome slopes for 2 patients
=========================== short test summary info ============================
FAILED code/tests/test_mixed_effects.py::test_mixed_effects_recovers_known_interaction
FAILED code/tests/test_permutation.py::test_permutation_runs - ValueError: Yo...
FAILED code/tests/test_slopes.py::test_compute_taxon_slopes_simple - assert n...
FAILED code/tests/test_slopes.py::test_compute_outcome_slopes_simple - assert...
4 failed, 16 passed in 1.28s



## Declared deliverables still missing

- data/processed/clr_abundances.parquet
- data/processed/filtered_samples.parquet
- data/raw/ppmi_asv.csv
- data/raw/ppmi_clinical.parquet
- data/results/mixed_effects_summary.csv
- data/results/partial_spearman_exploratory.csv
- data/results/permutation_pvalues.csv
- data/results/taxa_correlations.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/clr_abundances.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clr_abundances.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_asv.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_ingest.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_asv.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_clinical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
    - `code/tests/test_ingest.py` — NOT invoked by the run-book
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_clinical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/mixed_effects_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/tests/test_mixed_effects.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/mixed_effects_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/partial_spearman_exploratory.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/partial_spearman_exploratory.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/permutation_pvalues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/tests/test_permutation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/permutation_pvalues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/taxa_correlations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/taxa_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
