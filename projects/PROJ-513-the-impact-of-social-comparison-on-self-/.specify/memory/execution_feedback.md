# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/simulate_participant.py: metric `score` assigned from an RNG draw (line 68)
- code/simulate_participant.py: metric `score` assigned from an RNG draw (line 70)
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…evelopment.  This script generates synthetic participant responses ba…”
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…sonl          Note: This generates synthetic data for TESTING ONLY.…”
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description='Generate synthetic participant data for tes…”
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…'WARNING: This is synthetic data and MUST NOT be used for…”
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…lp='Output file path for simulated data (default: data/raw/mock_…”
- code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…print("WARNING: This is SYNTHETIC data for TESTING ONLY.")…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/simulate_participant.py --n-participants 150 --output data/raw/mock_responses/`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/simulate_participant.py --n-participants 150 --output data/raw/mock_responses/`
  - script usage: `simulate_participant.py [-h] [--n N] [--output OUTPUT] [--seed SEED]`
  - argparse error: `simulate_participant.py: error: unrecognized arguments: --n-participants 150`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/simulate_participant.py: metric `score` assigned from an RNG draw (line 68); code/simulate_participant.py: metric `score` assigned from an RNG draw (line 70); code/simulate_participant.py: synthetic/fake INPUT data not authorized by the spec — “…evelopment.  This script generates synthetic participant responses ba…”; 2 command(s) failed: python code/simulate_participant.py --n-participants 150 --output data/raw/mock_responses/ (rc=2); python code/analysis.py (rc=1); 1 declared deliverable(s) absent: data/analysis_results.json

## Failing / missing run-book commands

- python code/simulate_participant.py --n-participants 150 --output data/raw/mock_responses/ -> rc=2
    usage: simulate_participant.py [-h] [--n N] [--output OUTPUT] [--seed SEED]
                               [--stimuli-dir STIMULI_DIR]
simulate_participant.py: error: unrecognized arguments: --n-participants 150
- python code/analysis.py -> rc=1
    Starting Data Validation for Analysis (T024)...
ERROR: Processed data directory not found: data/processed

## Declared deliverables still missing

- data/analysis_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/analysis_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
