# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/validation/validate_quickstart.py: synthetic/fake INPUT data not authorized by the spec — “…"name": "Generate Mock Data",             "cmd": [sy…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/validation/validate_quickstart.py: synthetic/fake INPUT data not authorized by the spec — “…"name": "Generate Mock Data",             "cmd": [sy…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/analysis/power.py; python code/analysis/anova.py; python code/utils/data_loader.py --source visual_genome --limit 30; 1 command(s) failed: python code/data/ethics_generator.py --mode pre-bundled --count 30 --seed 42 (rc=1); 1 declared deliverable(s) absent: data/analysis/power_report.json

## Failing / missing run-book commands

- python code/data/ethics_generator.py --mode pre-bundled --count 30 --seed 42 -> rc=1
    FAILURE: CRITICAL: No real IRB approval document found at /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/ethics/irb_approval_final.pdf. Recruitment cannot begin. Please obtain IRB approval for PROJ-317-the-impact-of-visual-detail-on-false-mem and place the document in the ethics directory before proceeding.
- python code/analysis/power.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/analysis/power.py': [Errno 2] No such file or directory
- python code/analysis/anova.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/analysis/anova.py': [Errno 2] No such file or directory
- python code/utils/data_loader.py --source visual_genome --limit 30 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/utils/data_loader.py': [Errno 2] No such file or directory
- python code/analysis/anova.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/analysis/anova.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/analysis/power_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/power_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
