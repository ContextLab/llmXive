# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_docs.py: self-declared fabricated metric — “…tivity data found. Generating placeholder results.")             results_conte…”
- code/generate_docs.py: self-declared fabricated metric — “…logger.warning(f"Generated placeholder results due to missing data: {output…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42`
  - script usage: `generate_data.py [-h] [--n N] [--p P] [--rho RHO] [--seed SEED]`
  - argparse error: `generate_data.py: error: the following arguments are required: --out`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_docs.py: self-declared fabricated metric — “…tivity data found. Generating placeholder results.")             results_conte…”; code/generate_docs.py: self-declared fabricated metric — “…logger.warning(f"Generated placeholder results due to missing data: {output…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py --full-sweep; 1 command(s) failed: python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42 (rc=2); 5 declared deliverable(s) absent: data/results/ks_stats.json; data/results/sensitivity.csv; data/sweep/params.csv

## Failing / missing run-book commands

- python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42 -> rc=2
    usage: generate_data.py [-h] [--n N] [--p P] [--rho RHO] [--seed SEED]
                        [--dist {normal,t,skew_normal}] --out OUT
generate_data.py: error: the following arguments are required: --out
- python code/main.py --full-sweep -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/results/ks_stats.json
- data/results/sensitivity.csv
- data/sweep/params.csv
- data/sweep/power_analysis_result.json
- data/sweep/seed_map.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/ks_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ks_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_docs.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/legacy_t024_placeholder.py` — NOT invoked by the run-book
    - `code/docs_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/params.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_docs.py` — NOT invoked by the run-book
    - `code/profile_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/docs_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/params.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/power_analysis_result.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/power_analysis_result.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/seed_map.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_docs.py` — NOT invoked by the run-book
    - `code/profile_simulation.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/seed_map.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
