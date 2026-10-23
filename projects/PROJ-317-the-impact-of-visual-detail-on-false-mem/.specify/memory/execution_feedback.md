# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data. """  import json import…”
- code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…aLoadError(             "Mock data generation is disabled.…”
- code/validation/validate_quickstart.py: synthetic/fake INPUT data not authorized by the spec — “…"name": "Generate Mock Data",             "cmd": [sy…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/utils/data_loader.py --source prebundled --count <sample_size> --seed 42`
  - script usage: `data_loader.py [-h] [--source SOURCE] [--count COUNT] [--seed SEED]`
  - argparse error: `data_loader.py: error: argument --count: invalid int value: '<sample_size>'`
- run-book command: `python code/data/ethics_generator.py --mode all --seed 42`
  - script usage: `ethics_generator.py [-h] [--mode {pre-bundled,mock}] [--count COUNT]`
  - argparse error: `ethics_generator.py: error: argument --mode: invalid choice: 'all' (choose from 'pre-bundled', 'mock')`
- run-book command: `python code/analysis/anova.py         # secondary descriptive ANOVA (run after assumption checks)`
  - script usage: `anova.py [-h] [--input INPUT] [--output OUTPUT] [--alpha ALPHA]`
  - argparse error: `anova.py: error: unrecognized arguments: # secondary descriptive ANOVA (run after assumption checks)`
- run-book command: `python code/utils/data_loader.py --source visual_genome --limit <reasonable_limit> --stream`
  - script usage: `data_loader.py [-h] [--source SOURCE] [--count COUNT] [--seed SEED]`
  - argparse error: `data_loader.py: error: unrecognized arguments: --limit <reasonable_limit> --stream`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data. """  import json import…”; code/data/loader.py: synthetic/fake INPUT data not authorized by the spec — “…aLoadError(             "Mock data generation is disabled.…”; code/validation/validate_quickstart.py: synthetic/fake INPUT data not authorized by the spec — “…"name": "Generate Mock Data",             "cmd": [sy…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/glmm.py          # primary binomial mixed‑effects model; 6 command(s) failed: python code/utils/data_loader.py --source prebundled --count <sample_size> --seed 42 (rc=2); python code/data/ethics_generator.py --mode all --seed 42 (rc=2); python code/analysis/power.py (rc=1)

## Failing / missing run-book commands

- python code/utils/data_loader.py --source prebundled --count <sample_size> --seed 42 -> rc=2

2026-10-23 16:40:32 - llmXive - INFO - Logging system initialized with PII sanitization enabled
2026-10-23 16:40:32 - llmXive - INFO - Log file: /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/logs/app.log
2026-10-23 16:40:32 - llmXive - INFO - Log level: INFO
usage: data_loader.py [-h] [--source SOURCE] [--count COUNT] [--seed SEED]
                      [--output OUTPUT] [--validate]
                      [--complexity-min COMPLEXITY_MIN]
                      [--complexity-max COMPLEXITY_MAX]
data_loader.py: error: argument --count: invalid int value: '<sample_size>'

- python code/data/ethics_generator.py --mode all --seed 42 -> rc=2

2026-10-23 16:40:32 - llmXive - INFO - Logging system initialized with PII sanitization enabled
2026-10-23 16:40:32 - llmXive - INFO - Log file: /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/logs/app.log
2026-10-23 16:40:32 - llmXive - INFO - Log level: INFO
usage: ethics_generator.py [-h] [--mode {pre-bundled,mock}] [--count COUNT]
                           [--seed SEED]
ethics_generator.py: error: argument --mode: invalid choice: 'all' (choose from 'pre-bundled', 'mock')

- python code/analysis/power.py -> rc=1
in__ - WARNING - Could not compute power for effect_size=0.3: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:33 - __main__ - INFO - Effect size 0.30: N=None, Power=0.000
2026-10-23 16:40:33 - __main__ - WARNING - Could not compute power for effect_size=0.35: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:33 - __main__ - INFO - Effect size 0.35: N=None, Power=0.000
2026-10-23 16:40:33 - __main__ - WARNING - Could not compute power for effect_size=0.4: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:33 - __main__ - INFO - Effect size 0.40: N=None, Power=0.000
2026-10-23 16:40:33 - __main__ - INFO - Sensitivity analysis saved to /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/analysis/sensitivity_analysis.json
2026-10-23 16:40:33 - __main__ - INFO - Power report saved to /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/analysis/power_report.json
2026-10-23 16:40:33 - __main__ - ERROR - Power analysis indicates insufficient power. Consider increasing N.

- python code/analysis/glmm.py          # primary binomial mixed‑effects model -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-317-the-impact-of-visual-detail-on-false-mem/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/code/analysis/glmm.py': [Errno 2] No such file or directory

- python code/analysis/anova.py         # secondary descriptive ANOVA (run after assumption checks) -> rc=2

2026-10-23 16:40:33 - llmXive - INFO - Logging system initialized with PII sanitization enabled
2026-10-23 16:40:33 - llmXive - INFO - Log file: /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/logs/app.log
2026-10-23 16:40:33 - llmXive - INFO - Log level: INFO
usage: anova.py [-h] [--input INPUT] [--output OUTPUT] [--alpha ALPHA]
anova.py: error: unrecognized arguments: # secondary descriptive ANOVA (run after assumption checks)

- python code/analysis/power.py --report data/analysis/power_analysis_report.txt -> rc=1
 - __main__ - INFO - Effect size 0.25: N=None, Power=0.000
2026-10-23 16:40:35 - __main__ - WARNING - Could not compute power for effect_size=0.3: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:35 - __main__ - INFO - Effect size 0.30: N=None, Power=0.000
2026-10-23 16:40:35 - __main__ - WARNING - Could not compute power for effect_size=0.35: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:35 - __main__ - INFO - Effect size 0.35: N=None, Power=0.000
2026-10-23 16:40:35 - __main__ - WARNING - Could not compute power for effect_size=0.4: FTestAnovaPower.solve_power() got an unexpected keyword argument 'n_groups'
2026-10-23 16:40:35 - __main__ - INFO - Effect size 0.40: N=None, Power=0.000
2026-10-23 16:40:35 - __main__ - INFO - Sensitivity analysis saved to /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/analysis/sensitivity_analysis.json
2026-10-23 16:40:35 - __main__ - INFO - Power report saved to data/analysis/power_analysis_report.txt
2026-10-23 16:40:35 - __main__ - ERROR - Power analysis indicates insufficient power. Consider increasing N.

- python code/utils/data_loader.py --source visual_genome --limit <reasonable_limit> --stream -> rc=2

2026-10-23 16:40:36 - llmXive - INFO - Logging system initialized with PII sanitization enabled
2026-10-23 16:40:36 - llmXive - INFO - Log file: /home/runner/work/llmXive/llmXive/projects/PROJ-317-the-impact-of-visual-detail-on-false-mem/data/logs/app.log
2026-10-23 16:40:36 - llmXive - INFO - Log level: INFO
usage: data_loader.py [-h] [--source SOURCE] [--count COUNT] [--seed SEED]
                      [--output OUTPUT] [--validate]
                      [--complexity-min COMPLEXITY_MIN]
                      [--complexity-max COMPLEXITY_MAX]
data_loader.py: error: unrecognized arguments: --limit <reasonable_limit> --stream

