# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…is replaces the previous dummy input approach which was rejec…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/scripts/run_full_benchmark.py --mode prepare`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/scripts/run_full_benchmark.py --mode prepare`
  - script usage: `run_full_benchmark.py [-h] [--subset-size SUBSET_SIZE]`
  - argparse error: `run_full_benchmark.py: error: unrecognized arguments: --mode prepare`
- run-book command: `python code/scripts/run_full_benchmark.py --mode benchmark --subset-size 500`
  - script usage: `run_full_benchmark.py [-h] [--subset-size SUBSET_SIZE]`
  - argparse error: `run_full_benchmark.py: error: unrecognized arguments: --mode benchmark`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/adapters/text_cross_attention.py: synthetic/fake INPUT data not authorized by the spec — “…is replaces the previous dummy input approach which was rejec…”; 2 command(s) failed: python code/scripts/run_full_benchmark.py --mode prepare (rc=2); python code/scripts/run_full_benchmark.py --mode benchmark --subset-size 500 (rc=2); 8 declared deliverable(s) absent: data/processed/fidelity_report.json; data/processed/filtered_subset_manifest.json; data/processed/latency_verification_report.json

## Failing / missing run-book commands

- python code/scripts/run_full_benchmark.py --mode prepare -> rc=2
    usage: run_full_benchmark.py [-h] [--subset-size SUBSET_SIZE]
                             [--config CONFIG] [--output-dir OUTPUT_DIR]
run_full_benchmark.py: error: unrecognized arguments: --mode prepare
- python code/scripts/run_full_benchmark.py --mode benchmark --subset-size 500 -> rc=2
    usage: run_full_benchmark.py [-h] [--subset-size SUBSET_SIZE]
                             [--config CONFIG] [--output-dir OUTPUT_DIR]
run_full_benchmark.py: error: unrecognized arguments: --mode benchmark

## Declared deliverables still missing

- data/processed/fidelity_report.json
- data/processed/filtered_subset_manifest.json
- data/processed/latency_verification_report.json
- data/processed/manifest.json
- data/processed/motion_labels.json
- data/processed/robustness_report.json
- data/processed/sensitivity_analysis.csv
- data/processed/stratified_subset_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/fidelity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/fidelity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_subset_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_subset_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/latency_verification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/metrics/latency.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/latency_verification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/feasibility_filter.py` — NOT invoked by the run-book
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/manifest.py` — NOT invoked by the run-book
    - `code/src/pipeline/state_updater.py` — NOT invoked by the run-book
    - `code/src/pipeline/runner.py` — NOT invoked by the run-book
    - `code/src/pipeline/reporter.py` — NOT invoked by the run-book
    - `code/tests/unit/test_runner_6h_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/motion_labels.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats/sensitivity.py` — NOT invoked by the run-book
    - `code/src/stats/motion_labels.py` — NOT invoked by the run-book
    - `code/tests/unit/test_motion_labels.py` — NOT invoked by the run-book
    - `code/scripts/run_motion_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/motion_labels.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/robustness_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats/robustness_interpreter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/robustness_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats/robustness_interpreter.py` — NOT invoked by the run-book
    - `code/src/stats/sensitivity.py` — NOT invoked by the run-book
    - `code/src/pipeline/benchmark_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/stratified_subset_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/stratified_subset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/stratified_subset_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
