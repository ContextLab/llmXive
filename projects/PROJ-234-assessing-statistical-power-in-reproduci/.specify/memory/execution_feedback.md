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

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…est the schema against a mock dataset entry."""     print("\nT…”; code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…t("\nTesting schema with mock data...")          if not sch…”; code/05_verify_dataset_schema.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a minimal valid mock dataset entry based on the schem…”; 5 command(s) failed: python code/01_ingest_openml.py (rc=1); python code/02_parse_publications.py (rc=1); python code/03_compute_sensitivity.py (rc=1); 2 declared deliverable(s) absent: data/processed/extraction_stats.json; data/processed/performance_metrics.json

## Failing / missing run-book commands

- python code/01_ingest_openml.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/01_ingest_openml.py", line 23, in <module>
    from utils.logging_config import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/__init__.py", line 5, in <module>
    from .oa_checker import is_open_access, check_doi_oa_status
ImportError: cannot import name 'check_doi_oa_status' from 'utils.oa_checker' (/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/oa_checker.py)

- python code/02_parse_publications.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/02_parse_publications.py", line 15, in <module>
    from utils.logging_config import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/__init__.py", line 5, in <module>
    from .oa_checker import is_open_access, check_doi_oa_status
ImportError: cannot import name 'check_doi_oa_status' from 'utils.oa_checker' (/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/oa_checker.py)

- python code/03_compute_sensitivity.py -> rc=1

2026-10-15 18:24:42,343 - __main__ - ERROR - Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/data/processed/extracted_params.json
2026-10-15 18:24:42,344 - __main__ - INFO - Please run code/02_parse_publications.py first to generate extracted_params.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/03_compute_sensitivity.py", line 262, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/03_compute_sensitivity.py", line 255, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined

- python code/04_generate_report.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/04_generate_report.py", line 17, in <module>
    from utils.logging_config import setup_logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/__init__.py", line 5, in <module>
    from .oa_checker import is_open_access, check_doi_oa_status
ImportError: cannot import name 'check_doi_oa_status' from 'utils.oa_checker' (/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/oa_checker.py)

- python -m pytest tests/ -> rc=2
.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_utils_refactor.py:7: in <module>
    from code.utils.oa_checker import is_open_access, check_doi_oa_status
E   ImportError: cannot import name 'check_doi_oa_status' from 'code.utils.oa_checker' (/home/runner/work/llmXive/llmXive/projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils/oa_checker.py)
=========================== short test summary info ============================
ERROR tests/unit/test_07_generate_extraction_stats.py
ERROR tests/unit/test_abstract_fallback.py
ERROR tests/unit/test_api_client.py
ERROR tests/unit/test_compute_sensitivity.py
ERROR tests/unit/test_ingest_dedup.py
ERROR tests/unit/test_parsers.py
ERROR tests/unit/test_performance_harness.py
ERROR tests/unit/test_power_audit_schema.py
ERROR tests/unit/test_utils_refactor.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.36s ===============================



## Declared deliverables still missing

- data/processed/extraction_stats.json
- data/processed/performance_metrics.json

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
