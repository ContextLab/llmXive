# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/pipeline/run_correlation_only.py: synthetic/fake INPUT data not authorized by the spec — “…n.run_correlation`.  The synthetic data is deliberately tiny (2…”
- code/src/pipeline/run_correlation_only.py: synthetic/fake INPUT data not authorized by the spec — “…ode."""     # 1️⃣  Write synthetic raw inputs.     asv_path, clin_path…”
- code/src/pipeline/run_us1.py: synthetic/fake INPUT data not authorized by the spec — “…lt upper bound; the tiny synthetic data used in tests     )…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/pipeline/run_correlation_only.py: synthetic/fake INPUT data not authorized by the spec — “…n.run_correlation`.  The synthetic data is deliberately tiny (2…”; code/src/pipeline/run_correlation_only.py: synthetic/fake INPUT data not authorized by the spec — “…ode."""     # 1️⃣  Write synthetic raw inputs.     asv_path, clin_path…”; code/src/pipeline/run_us1.py: synthetic/fake INPUT data not authorized by the spec — “…lt upper bound; the tiny synthetic data used in tests     )…”; 4 command(s) failed: python -m code.src.pipeline.ingest (rc=1); python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 (rc=1); python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 (rc=1); 10 declared deliverable(s) absent: data/processed/clr_abundances.parquet; data/processed/filtered_samples.parquet; data/processed/patient_outcome_slopes.parquet

## Failing / missing run-book commands

- python -m code.src.pipeline.ingest -> rc=1

2026-10-14 09:18:29,526 INFO __main__: === PPMI input validation (FR-001) ===
2026-10-14 09:18:29,527 ERROR __main__: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.
2026-10-14 09:18:29,527 ERROR __main__: Input validation FAILED: Required input file not found: neither /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/ppmi_asv.csv nor /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/data/raw/open_asv.csv exist. Place the researcher‑supplied asv table at one of these locations.

- python -m code.src.pipeline  --seed 42  --max_taxa 100  --perm_iterations 1000 -> rc=1
 following exception:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/__main__.py", line 13, in <module>
    from . import ingest, preprocess, slopes, correlation, mixed_effects, permutation
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/__init__.py", line 40, in __getattr__
    module = importlib.import_module(f".{name}", __name__)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/preprocess.py", line 32, in <module>
    raise ImportError(
ImportError: scikit‑bio is required for CLR transformation. Install it via `pip install scikit-bio`.

- python -m code.src.pipeline.run_us3 --iterations 1000 --seed 42 -> rc=1
t cause of the following exception:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/run_us3.py", line 29, in <module>
    from . import ingest, mixed_effects, permutation, preprocess, slopes
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/__init__.py", line 40, in __getattr__
    module = importlib.import_module(f".{name}", __name__)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/preprocess.py", line 32, in <module>
    raise ImportError(
ImportError: scikit‑bio is required for CLR transformation. Install it via `pip install scikit-bio`.

- python -m pytest -q code/tests -> rc=2
line/preprocess.py:32: in <module>
    raise ImportError(
E   ImportError: scikit‑bio is required for CLR transformation. Install it via `pip install scikit-bio`.
=============================== warnings summary ===============================
code/tests/test_preprocess_default_output.py:17
  /home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/tests/test_preprocess_default_output.py:17: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(180)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR code/tests/contract/test_contracts.py
ERROR code/tests/test_correlation.py
ERROR code/tests/test_permutation.py
ERROR code/tests/test_preprocess.py
ERROR code/tests/test_preprocess_memory_cap.py
ERROR code/tests/test_run_us1.py
ERROR code/tests/test_runtime_budget.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 7 errors in 1.23s



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
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_preprocess_default.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/clr_abundances.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_preprocess_default.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess_default_output.py` — NOT invoked by the run-book
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
    - `code/src/pipeline/__main__.py` — NOT invoked by the run-book
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/src/pipeline/verify_dataset.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_asv.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ppmi_clinical.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/__main__.py` — NOT invoked by the run-book
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/ingest.py` — IS a run-book command
    - `code/src/pipeline/mixed_effects.py` — NOT invoked by the run-book
    - `code/src/pipeline/permutation.py` — NOT invoked by the run-book
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ppmi_clinical.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
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
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/tests/contract/test_contracts.py` — NOT invoked by the run-book
    - `code/tests/test_run_us1.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/taxa_correlations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
