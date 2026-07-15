# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…generating deterministic mock data for CI/CD and testing en…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…verified URL or generate mock data.      Args:         data…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…unc: Function to call if mock data is needed.      Returns:…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…{data_type}. Generating mock data.")      # Generate mock…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…data.")      # Generate mock data     mock_data = generato…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…r_func()          # Save mock data     output_path.parent.m…”
- code/data/mock_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Deterministic Mock Data Generator for CI and Tes…”
- code/data/mock_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ator for CI and Testing. Generates synthetic but consistent data to a…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/compound_data.json, data/raw/env_data.json, data/raw/genomic_vcf.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…generating deterministic mock data for CI/CD and testing en…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…verified URL or generate mock data.      Args:         data…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…unc: Function to call if mock data is needed.      Returns:…”; every produced artifact is gitignored (data/raw/compound_data.json, data/raw/env_data.json, data/raw/genomic_vcf.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 command(s) failed: python code/main.py (rc=1); 2 declared deliverable(s) absent: data/processed/features_vif.csv; data/processed/filtered.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    ib/python3.11/site-packages/pandas/core/frame.py", line 769, in __init__
    mgr = dict_to_mgr(data, index, columns, dtype=dtype, copy=copy)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-475-predicting-plant-defense-compound-produc/code/.venv/lib/python3.11/site-packages/pandas/core/internals/construction.py", line 460, in dict_to_mgr
    return arrays_to_mgr(arrays, columns, index, dtype=dtype, consolidate=copy)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-475-predicting-plant-defense-compound-produc/code/.venv/lib/python3.11/site-packages/pandas/core/internals/construction.py", line 113, in arrays_to_mgr
    index = _extract_index(arrays)
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-475-predicting-plant-defense-compound-produc/code/.venv/lib/python3.11/site-packages/pandas/core/internals/construction.py", line 634, in _extract_index
    raise ValueError("If using all scalar values, you must pass an index")
ValueError: If using all scalar values, you must pass an index

## Declared deliverables still missing

- data/processed/features_vif.csv
- data/processed/filtered.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `main` — defined in `code/config.py`; called 19 way(s):

- code/config.py: sys.exit(main())
- code/main.py: success = main()
- code/setup_project.py: sys.exit(main())
- code/scripts/generate_mock_data.py: sys.exit(main())
- code/scripts/run_linter.py: sys.exit(main())
- code/scripts/update_manifest.py: sys.exit(main())
- code/scripts/validate_quickstart.py: sys.exit(main())
- code/utils/stats.py: sys.exit(main())
- code/models/training.py: main()
- code/models/evaluation.py: main()
- code/tests/test_models.py: unittest.main()
- code/tests/test_update_manifest.py: unittest.main()
- code/tests/test_preprocessing.py: unittest.main()
- code/tests/test_ingestion.py: unittest.main()
- code/tests/test_stats.py: unittest.main()
- code/data/ingestion.py: sys.exit(main())
- code/data/mock_generator.py: main()
- code/data/validation.py: main()
- code/data/preprocessing.py: sys.exit(main())

Make `main` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features_vif.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_vif.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/training.py` — NOT invoked by the run-book
    - `code/models/evaluation.py` — NOT invoked by the run-book
    - `code/tests/test_update_manifest.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
