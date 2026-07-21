# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…tail data (MLE).     2. Generate n_bootstrap synthetic datasets from this fitte…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…Pareto.     3. For each synthetic dataset, estimate its x_min (usi…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…(n_bootstrap):         # Generate synthetic data from fitted Pareto(…”
- code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…Estimate x_min for this synthetic data (to mimic the data-drive…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/main.py --year 2022`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --year 2022`
  - script usage: `main.py [-h] --input INPUT --output OUTPUT [--summary SUMMARY]`
  - argparse error: `main.py: error: the following arguments are required: --input, --output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…tail data (MLE).     2. Generate n_bootstrap synthetic datasets from this fitte…”; code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…Pareto.     3. For each synthetic dataset, estimate its x_min (usi…”; code/diagnostics.py: synthetic/fake INPUT data not authorized by the spec — “…(n_bootstrap):         # Generate synthetic data from fitted Pareto(…”; 1 command(s) failed: python code/main.py --year 2022 (rc=2); 2 declared deliverable(s) absent: data/results/tail_index_estimate.json; data/results/tail_ks.json

## Failing / missing run-book commands

- python code/main.py --year 2022 -> rc=2
    2026-07-21 04:45:12,670 - pipeline - INFO - Starting Flight Delay Analysis Pipeline
2026-07-21 04:45:12,670 - INFO - Starting Flight Delay Analysis Pipeline
2026-07-21 04:45:12,670 - pipeline - INFO - Executing Stage 1: Data Acquisition and Pre-processing
2026-07-21 04:45:12,670 - INFO - Executing Stage 1: Data Acquisition and Pre-processing
usage: main.py [-h] --input INPUT --output OUTPUT [--summary SUMMARY]
               [--zero-excluded-output ZERO_EXCLUDED_OUTPUT]
main.py: error: the following arguments are required: --input, --output

## Declared deliverables still missing

- data/results/tail_index_estimate.json
- data/results/tail_ks.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `download_bts_data` — defined in `code/data_loader.py`; called 1 way(s):

- code/data_loader.py: output_path = download_bts_data(year=year, output_dir=output_dir)

Make `download_bts_data` in `code/data_loader.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/tail_index_estimate.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/tail_index_estimate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/tail_ks.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/tail_ks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
