# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…est the schema against a mock dataset entry."""     print("\nT…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…t("\nTesting schema with mock data...")          if not sch…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a minimal valid mock dataset entry based on the schem…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…ed fields are present in mock data         required = schem…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…print(f"✗ ERROR: Mock data missing required field:…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…print("✓ Mock data validation passed.")…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…ROR: Failed to test with mock data: {e}")         return Fa…”
- code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…# 3. Test with mock data     if not test_schema_w…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/power_histogram.png) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…est the schema against a mock dataset entry."""     print("\nT…”; code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…t("\nTesting schema with mock data...")          if not sch…”; code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a minimal valid mock dataset entry based on the schem…”; every produced artifact is gitignored (data/processed/power_histogram.png) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/01_ingest_openml.py (rc=1); python code/02_parse_publications.py (rc=1); python code/03_compute_sensitivity.py (rc=1); 2 declared deliverable(s) absent: data/processed/extraction_stats.json; data/processed/performance_metrics.json

## Failing / missing run-book commands

- python code/01_ingest_openml.py -> rc=1

utils.logging_config - INFO - Starting OpenML ingestion process.
utils.logging_config - ERROR - Failed to fetch datasets from OpenML: [412] HTTP error 412

- python code/02_parse_publications.py -> rc=1

__main__ - ERROR - Raw data file not found: data/raw/openml_metadata_filtered.json

- python code/03_compute_sensitivity.py -> rc=1

2026-10-15 18:28:56,631 - __main__ - ERROR - Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/data/processed/extracted_params.json
2026-10-15 18:28:56,632 - __main__ - INFO - Please run code/02_parse_publications.py first to generate extracted_params.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/03_compute_sensitivity.py", line 262, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/03_compute_sensitivity.py", line 255, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined

- python -m pytest tests/ -> rc=2
sing-statistical-power-in-reproduci/code/__init__.py)
____________ ERROR collecting tests/unit/test_power_audit_schema.py ____________
import file mismatch:
imported module 'test_power_audit_schema' has this __file__ attribute:
  /home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/contract/test_power_audit_schema.py
which is not the same as the test file we want to collect:
  /home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/unit/test_power_audit_schema.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
=========================== short test summary info ============================
ERROR tests/unit/test_07_generate_extraction_stats.py
ERROR tests/unit/test_compute_sensitivity.py
ERROR tests/unit/test_ingest_dedup.py - AttributeError: module 'ingest_module...
ERROR tests/unit/test_oa_checker.py
ERROR tests/unit/test_performance_harness.py
ERROR tests/unit/test_power_audit_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 0.35s ===============================



## Declared deliverables still missing

- data/processed/extraction_stats.json
- data/processed/performance_metrics.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `openml` to the project's `requirements.txt` and `pip install openml`.
- **Verified**: this loads **6435** real records with fields: did, name, version, description_160, uploader, status, format, MajorityClassSize, MaxNominalAttDistinctValues, MinorityClassSize, NumberOfClasses, NumberOfFeatures, NumberOfInstances, NumberOfInstancesWithMissingValues, NumberOfMissingValues, NumberOfNumericFeatures, NumberOfSymbolicFeatures.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import openml, pandas as pd

df = openml.datasets.list_datasets(output_format="dataframe")
records = df.to_dict(orient="records")
print(f"RECORDS={len(records)}")
print("FIELDS=" + ",".join(records[0].keys()) if records else "FIELDS=")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/extraction_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_generate_report.py` — IS a run-book command
    - `code/07_generate_extraction_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extraction_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/performance_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/042_run_performance_harness.py` — NOT invoked by the run-book
    - `code/044_assert_memory_limit.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/performance_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
