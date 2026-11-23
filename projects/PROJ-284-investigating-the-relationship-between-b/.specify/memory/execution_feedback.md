# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…="running")     # Create synthetic test data for verification only (n…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…generator.     # It uses synthetic data to verify the logic, not…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/hcp_phenotypic.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…="running")     # Create synthetic test data for verification only (n…”; code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…generator.     # It uses synthetic data to verify the logic, not…”; every produced artifact is gitignored (data/raw/hcp_phenotypic.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 7 command(s) failed: python code/download/fetch_openneuro.py --subjects 50 --output data/raw (rc=1); python code/download/fetch_hcp_behavioral.py --subjects 50 --output data/raw (rc=1); python code/preprocess/run_qc_only.py --input data/raw --output data/processed (rc=1); 10 declared deliverable(s) absent: data/analysis/aggregated_metrics.csv; data/analysis/factor_scores.csv; data/analysis/fdr_corrected_results.csv

## Failing / missing run-book commands

- python code/download/fetch_openneuro.py --subjects 50 --output data/raw -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/download/fetch_openneuro.py", line 26, in <module>
    from openneuro import OpenNeuro
ModuleNotFoundError: No module named 'openneuro'

- python code/download/fetch_hcp_behavioral.py --subjects 50 --output data/raw -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/download/fetch_hcp_behavioral.py:18: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Warning: Subject ID 50 does not look like a standard HCP ID.
Error: Unable to parse CSV at data/raw/hcp_phenotypic.csv: Error tokenizing data. C error: Expected 1 fields in line 9, saw 2


- python code/preprocess/run_qc_only.py --input data/raw --output data/processed -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/preprocess/run_qc_only.py", line 84, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/preprocess/run_qc_only.py", line 72, in main
    record_tsnr_evidence_and_filter(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/data/preprocess.py", line 167, in record_tsnr_evidence_and_filter
    raise FileNotFoundError(f"No NIfTI files found in {nifti_dir}")
FileNotFoundError: No NIfTI files found in data/raw

- python code/main_pipeline.py --batch-size 5 --mode cpu -> rc=1


- python code/viz/generate_report.py --input data/analysis/correlation_results.csv --output reports/summary.md -> rc=1
iz/generate_report.py:34: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/viz/generate_report.py", line 245, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/viz/generate_report.py", line 223, in main
    df = _load_csv(args.input)
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/viz/generate_report.py", line 65, in _load_csv
    raise FileNotFoundError(f"Correlation results CSV not found: {csv_path}")
FileNotFoundError: Correlation results CSV not found: data/analysis/correlation_results.csv

- python code/utils/checksums.py verify -> rc=1
Checksum verification FAILED.
==================================================
Checksums file missing: /home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/data/processed/checksums.json
==================================================


- python -m pytest tests/contract/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/analysis/aggregated_metrics.csv
- data/analysis/factor_scores.csv
- data/analysis/fdr_corrected_results.csv
- data/analysis/full_metrics.csv
- data/analysis/metrics_raw.csv
- data/analysis/node_metrics_raw.csv
- data/analysis/pca_loadings.csv
- data/analysis/power_analysis.json
- data/analysis/qc_summary.csv
- data/analysis/subjects_included.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
    - `code/analysis/pca_utils.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/tools/verify_batching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/factor_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
    - `code/analysis/pca_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/factor_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/fdr_corrected_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/viz/network.py` — NOT invoked by the run-book
    - `code/viz/scatter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/fdr_corrected_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/full_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/generate_full_metrics.py` — NOT invoked by the run-book
    - `code/viz/scatter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/full_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/viz/network.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/node_metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/viz/network.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/node_metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/pca_loadings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
    - `code/analysis/pca_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/pca_loadings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/qc_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/preprocess/run_qc_only.py` — IS a run-book command
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/qc_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/subjects_included.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/preprocess/run_qc_only.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis/subjects_included.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
