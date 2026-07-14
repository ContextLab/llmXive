# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…F data or return path to mock data if URL fails."""     con…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…failed, falling back to mock data.")          # Fallback t…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating mock genomic data.")     generate_all_mock…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…tadata or return path to mock data if URL fails."""     con…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…failed, falling back to mock data.")          # Fallback…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating mock environmental data.")     generate_all_mock…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…ofiles or return path to mock data if URL fails."""     con…”
- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…failed, falling back to mock data.")          # Fallback…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…F data or return path to mock data if URL fails."""     con…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…failed, falling back to mock data.")          # Fallback t…”; code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Generating mock genomic data.")     generate_all_mock…”; 1 command(s) failed: python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/features_vif.csv; data/processed/filtered.csv; data/raw/genomic_vcf.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-07-14 21:24:24,271 - __main__ - INFO - Starting full pipeline...
2026-07-14 21:24:24,271 - __main__ - INFO - Starting full pipeline...
2026-07-14 21:24:24,271 - __main__ - INFO - Step 1: Ingestion
2026-07-14 21:24:24,271 - __main__ - INFO - Step 1: Ingestion
2026-07-14 21:24:24,272 - __main__ - ERROR - Pipeline failed: main() takes 0 positional arguments but 1 was given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-475-predicting-plant-defense-compound-produc/code/main.py", line 56, in run_pipeline
    run_ingestion(config)
TypeError: main() takes 0 positional arguments but 1 was given
2026-07-14 21:24:24,272 - __main__ - ERROR - Pipeline failed: main() takes 0 positional arguments but 1 was given
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-475-predicting-plant-defense-compound-produc/code/main.py", line 56, in run_pipeline
    run_ingestion(config)
TypeError: main() takes 0 positional arguments but 1 was given

## Declared deliverables still missing

- data/processed/features_vif.csv
- data/processed/filtered.csv
- data/raw/genomic_vcf.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `main` — defined in `code/main.py`; called 14 way(s):

- code/main.py: main()
- code/setup_project.py: sys.exit(main())
- code/scripts/run_linter.py: sys.exit(main())
- code/scripts/update_manifest.py: sys.exit(main())
- code/scripts/validate_quickstart.py: sys.exit(main())
- code/models/training.py: main()
- code/models/evaluation.py: main(config)
- code/tests/test_models.py: unittest.main()
- code/tests/test_update_manifest.py: unittest.main()
- code/tests/test_preprocessing.py: unittest.main()
- code/tests/test_stats.py: unittest.main()
- code/data/ingestion.py: sys.exit(main())
- code/data/validation.py: main()
- code/data/preprocessing.py: main()

Make `main` in `code/main.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features_vif.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/training.py` — NOT invoked by the run-book
    - `code/models/evaluation.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_vif.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_update_manifest.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/genomic_vcf.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/test_update_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/mock_generator.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/genomic_vcf.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
