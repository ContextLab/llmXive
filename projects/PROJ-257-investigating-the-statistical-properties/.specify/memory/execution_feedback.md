# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate the synthetic BBH catalog (AM-001 hypo…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.main               # Executes all phases in order`
  - script usage: `main.py [-h] [--download-only] [--skip-download] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: # Executes all phases in order`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: src/data/synthetic_gen.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate the synthetic BBH catalog (AM-001 hypo…”; 2 command(s) failed: python -m src.main               # Executes all phases in order (rc=2); python -m pytest tests/contract (rc=5); 1 declared deliverable(s) absent: data/results/data_availability.json

## Failing / missing run-book commands

- python -m src.main               # Executes all phases in order -> rc=2

usage: main.py [-h] [--download-only] [--skip-download] [--seed SEED]
main.py: error: unrecognized arguments: # Executes all phases in order

- python -m pytest tests/contract -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.1.1, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-257-investigating-the-statistical-properties
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collected 0 items

============================ no tests ran in 0.01s =============================



## Declared deliverables still missing

- data/results/data_availability.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/data_availability.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/record_availability.py` — NOT invoked by the run-book
    - `src/data/record_availability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_availability.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
