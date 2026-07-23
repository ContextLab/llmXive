# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic polymer data using the s…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d representation for the synthetic dataset     char_map = {…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generates synthetic polymer graphs with asso…”
- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…vice     )      # Create dummy data loader     # Generate a…”
- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…dummy data loader     # Generate a few synthetic samples to test the back…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/data/ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic polymer data using the s…”; code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…d representation for the synthetic dataset     char_map = {…”; code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generates synthetic polymer graphs with asso…”; 2 command(s) failed: python code/data/ingestion.py --download-pubchem (rc=1); python code/data/ingestion.py --generate-mock-target (rc=1); 3 declared deliverable(s) absent: data/processed/polymers.h5; data/processed/scaffold_split_indices.json; data/raw/checksums.json

## Failing / missing run-book commands

- python code/data/ingestion.py --download-pubchem -> rc=1
    ^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 151, in fetch_nist_pubchem_data
    raise DataUnavailableError("Real data source unavailable. Falling back to simulation.")
DataUnavailableError: Real data source unavailable. Falling back to simulation.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 335, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 300, in main
    data = generate_simulation_data()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 163, in generate_simulation_data
    graphs, records = generate_polymer_graphs(num_samples=1000)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: generate_polymer_graphs() got an unexpected keyword argument 'num_samples'
- python code/data/ingestion.py --generate-mock-target -> rc=1
    ^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 151, in fetch_nist_pubchem_data
    raise DataUnavailableError("Real data source unavailable. Falling back to simulation.")
DataUnavailableError: Real data source unavailable. Falling back to simulation.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 335, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 300, in main
    data = generate_simulation_data()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/ingestion.py", line 163, in generate_simulation_data
    graphs, records = generate_polymer_graphs(num_samples=1000)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: generate_polymer_graphs() got an unexpected keyword argument 'num_samples'

## Declared deliverables still missing

- data/processed/polymers.h5
- data/processed/scaffold_split_indices.json
- data/raw/checksums.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `generate_polymer_graphs` — defined in `code/data/simulation.py`; called 2 way(s):

- code/data/simulation.py: graphs = generate_polymer_graphs(count, seed)
- code/data/ingestion.py: graphs, records = generate_polymer_graphs(num_samples=1000)

Make `generate_polymer_graphs` in `code/data/simulation.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/polymers.h5` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/quickstart.py` — NOT invoked by the run-book
    - `code/performance_optimizer.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/performance_profiler.py` — NOT invoked by the run-book
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/data/ingestion.py` — IS a run-book command
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/polymers.h5` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaffold_split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/performance_optimizer.py` — NOT invoked by the run-book
    - `code/performance_profiler.py` — NOT invoked by the run-book
    - `code/evaluation/metrics.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaffold_split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingestion.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
