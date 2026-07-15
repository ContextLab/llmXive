# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/mock_generator.py: metric `concentration` assigned from an RNG draw (line 99)
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…rified URLs or generates mock data for CI/testing. """ impo…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…t configured. Generating mock data.")     # Generate mock d…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…k data.")     # Generate mock data as fallback for CI, but…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…t configured. Generating mock data.")     mock_data = gener…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…t configured. Generating mock data.")     mock_data = gener…”
- code/data/mock_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Deterministic Mock Data Generator for CI and Tes…”
- code/data/mock_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ator for CI and Testing. Generates synthetic but consistent data to a…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 25 fabricated/simulated-result signal(s) — results are not real measurements: code/data/mock_generator.py: metric `concentration` assigned from an RNG draw (line 99); code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…rified URLs or generates mock data for CI/testing. """ impo…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…t configured. Generating mock data.")     # Generate mock d…”; 4 declared deliverable(s) absent: data/processed/filtered.csv; data/raw/compound_data.json; data/raw/env_data.json

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/processed/filtered.csv
- data/raw/compound_data.json
- data/raw/env_data.json
- data/raw/genomic_vcf.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `main` — defined in `code/main.py`; called 20 way(s):

- code/main.py: success = main()
- code/setup_project.py: sys.exit(main())
- code/config.py: main()
- code/models/training.py: main()
- code/models/evaluation.py: main()
- code/utils/stats.py: sys.exit(main())
- code/scripts/validate_quickstart.py: sys.exit(main())
- code/scripts/generate_mock_data.py: sys.exit(main())
- code/scripts/run_linter.py: sys.exit(main())
- code/scripts/update_manifest.py: sys.exit(main())
- code/scripts/run_preprocessing.py: sys.exit(main())
- code/data/validation.py: main()
- code/data/mock_generator.py: sys.exit(main())
- code/data/ingestion.py: main()
- code/data/preprocessing.py: sys.exit(main())
- code/tests/test_stats.py: unittest.main()
- code/tests/test_update_manifest.py: unittest.main()
- code/tests/test_models.py: unittest.main()
- code/tests/test_preprocessing.py: unittest.main()
- code/tests/test_ingestion.py: unittest.main()

Make `main` in `code/main.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/training.py` — NOT invoked by the run-book
    - `code/models/evaluation.py` — NOT invoked by the run-book
    - `code/scripts/run_preprocessing.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/tests/test_update_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/compound_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_mock_data.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/mock_generator.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/tests/test_ingestion.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/compound_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/env_data.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_mock_data.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/mock_generator.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/tests/test_ingestion.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/env_data.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/genomic_vcf.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_mock_data.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/data/mock_generator.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/tests/test_update_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/genomic_vcf.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
