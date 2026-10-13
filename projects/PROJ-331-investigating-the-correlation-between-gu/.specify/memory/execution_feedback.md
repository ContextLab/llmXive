# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/pipeline/slopes.py: synthetic/fake INPUT data not authorized by the spec — “…n issue in the         # synthetic test data), fall back to the expec…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/pipeline/slopes.py: synthetic/fake INPUT data not authorized by the spec — “…n issue in the         # synthetic test data), fall back to the expec…”; 3 command(s) failed: python -m code.src.pipeline.ingest (rc=1); python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m pytest -q code/tests (rc=1); 10 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/processed/patient_outcome_slopes.parquet

## Failing / missing run-book commands

- python -m code.src.pipeline.ingest -> rc=1

2026-10-13 05:20:17,578 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-13 05:20:17,578 ERROR __main__: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.
2026-10-13 05:20:17,578 ERROR __main__: Input validation FAILED: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv. Place the researcher-supplied ASV table at data/raw/ppmi_asv.csv (columns: ['sample_id', 'patient_id', 'visit_date', '<taxon count columns>']). The pipeline does not generate synthetic data.

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
_zero_with_skip_flag
FAILED code/tests/test_ingest.py::test_malformed_asv_missing_columns_aborts
FAILED code/tests/test_ingest.py::test_main_writes_validation_report - Import...
FAILED code/tests/test_preprocess.py::test_single_visit_patients_excluded_with_logged_count
FAILED code/tests/test_preprocess.py::test_two_visit_patients_are_retained - ...
FAILED code/tests/test_preprocess.py::test_zero_taxa_dropped_with_warning - I...
FAILED code/tests/test_preprocess.py::test_clr_output_rows_equal_retained_samples
FAILED code/tests/test_preprocess.py::test_zero_variance_covariate_detected
FAILED code/tests/test_slopes.py::test_compute_taxon_slopes_simple - ImportEr...
FAILED code/tests/test_slopes.py::test_compute_outcome_slopes_simple - Import...
FAILED code/tests/test_slopes.py::test_run_slopes_writes_files - ImportError:...
FAILED code/tests/test_slopes.py::test_run_slopes_missing_outcome - ImportErr...
ERROR code/tests/test_mixed_effects.py::test_mixed_effects_recovers_known_interaction
ERROR code/tests/test_mixed_effects.py::test_missing_outcome_causes_empty_file
ERROR code/tests/test_permutation.py::test_permutation_runs - ImportError: Un...
13 failed, 4 passed, 3 errors in 1.92s



## Declared deliverables still missing

- data/processed/clr_abundances.parquet
- data/processed/filtered_samples.parquet
- data/processed/patient_outcome_slopes.parquet
- data/processed/patient_taxon_slopes.parquet
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
- `data/processed/patient_outcome_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_outcome_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_taxon_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_taxon_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
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
