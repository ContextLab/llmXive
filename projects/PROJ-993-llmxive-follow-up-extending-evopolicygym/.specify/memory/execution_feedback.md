# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration - in r…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode full --runs-per-condition 5 --seed 42`
  - script usage: `main.py [-h] [--run-evolution] [--run-shift-analysis] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --mode full --runs-per-condition 5 --seed 42`
- run-book command: `python code/main.py --mode analyze`
  - script usage: `main.py [-h] [--run-evolution] [--run-shift-analysis] [--config CONFIG]`
  - argparse error: `main.py: error: unrecognized arguments: --mode analyze`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…xist_ok=True)          # Mock data for demonstration - in r…”; 2 command(s) failed: python code/main.py --mode full --runs-per-condition 5 --seed 42 (rc=2); python code/main.py --mode analyze (rc=2); 3 declared deliverable(s) absent: data/evolution_results.csv; data/shift_validation.json; data/stats_results.json

## Failing / missing run-book commands

- python code/main.py --mode full --runs-per-condition 5 --seed 42 -> rc=2
    usage: main.py [-h] [--run-evolution] [--run-shift-analysis] [--config CONFIG]
main.py: error: unrecognized arguments: --mode full --runs-per-condition 5 --seed 42
- python code/main.py --mode analyze -> rc=2
    usage: main.py [-h] [--run-evolution] [--run-shift-analysis] [--config CONFIG]
main.py: error: unrecognized arguments: --mode analyze

## Declared deliverables still missing

- data/evolution_results.csv
- data/shift_validation.json
- data/stats_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/evolution_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
    - `code/agents/evolutionary_harness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/evolution_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/shift_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/refactor_cleanup.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
    - `code/tests/test_env_shift_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/shift_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/stats_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/tests/test_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/stats_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
