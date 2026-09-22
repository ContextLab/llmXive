# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_docs.py: self-declared fabricated metric — “…tivity data found. Generating placeholder results.")             results_conte…”
- code/generate_docs.py: self-declared fabricated metric — “…logger.warning(f"Generated placeholder results due to missing data: {output…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analyze_pvalues.py --input-dir data/results/pvalues --output-dir data/results/summary`
- `python code/run_tests.py --input data/synthetic/{uuid}.npz --iterations 100`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42`
  - script usage: `generate_data.py [-h] [--out OUT] [--n-values N_VALUES [N_VALUES ...]]`
  - argparse error: `generate_data.py: error: unrecognized arguments: --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_docs.py: self-declared fabricated metric — “…tivity data found. Generating placeholder results.")             results_conte…”; code/generate_docs.py: self-declared fabricated metric — “…logger.warning(f"Generated placeholder results due to missing data: {output…”; 4 command(s) failed: python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42 (rc=2); python code/run_tests.py --input data/synthetic/{uuid}.npz --iterations 100 (rc=1); python code/analyze_pvalues.py --input-dir data/results/pvalues --output-dir data/results/summary (rc=1); 7 declared deliverable(s) absent: data/results/bias_magnitude.csv; data/results/ks_stats.json; data/results/ritual_vs_reality.csv

## Failing / missing run-book commands

- python code/generate_data.py --n 100 --p 1000 --rho 0.5 --dist normal --seed 42 -> rc=2
    usage: generate_data.py [-h] [--out OUT] [--n-values N_VALUES [N_VALUES ...]]
                        [--p-values P_VALUES [P_VALUES ...]]
                        [--rho-values RHO_VALUES [RHO_VALUES ...]]
                        [--dist-types DIST_TYPES [DIST_TYPES ...]]
generate_data.py: error: unrecognized arguments: --seed 42
- python code/run_tests.py --input data/synthetic/{uuid}.npz --iterations 100 -> rc=1
    ERROR:__main__:Params file missing. Run generate_data.py first.
- python code/analyze_pvalues.py --input-dir data/results/pvalues --output-dir data/results/summary -> rc=1
    2026-09-22 15:22:02,585 - __main__ - INFO - Starting failure mechanism analysis...
2026-09-22 15:22:02,585 - __main__ - ERROR - File not found: Worst case summary file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/data/results/worst_case_summary.json. Please ensure T049 has been executed successfully.
- python code/main.py --full-sweep -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/code/main.py", line 49, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/code/main.py", line 16, in main
    os.chdir(base_dir)
    ^^
NameError: name 'os' is not defined

## Declared deliverables still missing

- data/results/bias_magnitude.csv
- data/results/ks_stats.json
- data/results/ritual_vs_reality.csv
- data/results/worst_case_summary.json
- data/sweep/params.csv
- data/sweep/power_analysis_result.json
- data/sweep/seed_map.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/bias_magnitude.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ritual_vs_reality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/bias_magnitude.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/ks_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_tests.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_reality_check_plot.py` — NOT invoked by the run-book
    - `code/run_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ks_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/ritual_vs_reality.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ritual_vs_reality.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/ritual_vs_reality.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/worst_case_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/ritual_vs_reality.py` — NOT invoked by the run-book
    - `code/generate_jagged_line_detail.py` — NOT invoked by the run-book
    - `code/generate_jagged_line_plot.py` — NOT invoked by the run-book
    - `code/analyze_pvalues.py` — IS a run-book command
  Make ONE of these WRITE `data/results/worst_case_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/params.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_tests.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/docs_generator.py` — NOT invoked by the run-book
    - `code/generate_reality_check_plot.py` — NOT invoked by the run-book
    - `code/generate_seed_map.py` — NOT invoked by the run-book
    - `code/generate_jagged_line_detail.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/params.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/power_analysis_result.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_data.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/run_power_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/power_analysis_result.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/sweep/seed_map.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_tests.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/generate_seed_map.py` — NOT invoked by the run-book
    - `code/collect_pvalues.py` — NOT invoked by the run-book
    - `code/generate_docs.py` — NOT invoked by the run-book
    - `code/profile_simulation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/sweep/seed_map.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/data/results/worst_case_summary.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ritual_vs_reality.py`, `code/analyze_pvalues.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-054-assessing-the-validity-of-p-values-in-hi/data/results/worst_case_summary.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/ritual_vs_reality.py`, `code/generate_jagged_line_detail.py`, `code/generate_jagged_line_plot.py`, `code/analyze_pvalues.py`.
