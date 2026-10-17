# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- data/raw/commit_pairs.csv: self-declared fabricated metric — “…hat your reported numbers are NOT real measurements: they are drawn from `random…”
- data/raw/commit_pairs.csv: self-declared fabricated metric — “…m`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautolo…”
- data/raw/commit_pairs.csv: self-declared fabricated metric — “…ver offload). Never present a simulated number as a measurement.  - code/ana…”
- data/raw/commit_pairs.csv: self-declared fabricated metric — “…esult signal(s) — results are not real measurements: code/analysis/generate_sens…”
- code/run_pipeline.py: synthetic/fake INPUT data not authorized by the spec — “…un the smoke test with a synthetic sample (ignores other stages)."…”
- data/raw/commit_pairs.csv: synthetic/fake INPUT data not authorized by the spec — “…ity_report.py: synthetic/fake INPUT data not authorized by the sp…”
- data/raw/commit_pairs.csv: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”
- data/raw/commit_pairs.csv: synthetic/fake INPUT data not authorized by the spec — “…e/research.md: synthetic/fake INPUT data not authorized by the sp…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 59 fabricated/simulated-result signal(s) — results are not real measurements: data/raw/commit_pairs.csv: self-declared fabricated metric — “…hat your reported numbers are NOT real measurements: they are drawn from `random…”; data/raw/commit_pairs.csv: self-declared fabricated metric — “…m`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautolo…”; data/raw/commit_pairs.csv: self-declared fabricated metric — “…ver offload). Never present a simulated number as a measurement.  - code/ana…”; 1 command(s) failed: python -m code.run_pipeline --full (rc=-1); 1 declared deliverable(s) absent: data/gold_standard/annotations.json

## Failing / missing run-book commands

- python -m code.run_pipeline --full -> rc=-1
Power analysis: estimated power for n=500 is 1.0000; exploratory=False
Wrote /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/results/power_report.md

2026-10-17 08:18:59,472 INFO __main__: Running full pipeline
2026-10-17 08:18:59,472 INFO __main__: Running power analysis...
2026-10-17 08:19:42,258 INFO code.power_analysis: Power analysis complete: power=1.0000 (n=500), exploratory=False
2026-10-17 08:19:42,259 INFO __main__: Running data extraction...
2026-10-17 08:19:42,259 INFO code.data_extraction: Repo already cloned at /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/repos/pandas, pulling latest.

[TIMEOUT after 120s]

## Declared deliverables still missing

- data/gold_standard/annotations.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/gold_standard/annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/generation.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
    - `code/power_analysis.py` — IS a run-book command
    - `code/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/gold_standard/annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
