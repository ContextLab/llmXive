# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/bes/population.py: function `select_parent` returns a bare RNG draw (line 279) — a reported value computed from no real input

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/dataset/generator.py --count 500 --output data/raw/puzzles.jsonl --scaling`
  - script usage: `generator.py [-h] --n N [N ...] --count COUNT`
  - argparse error: `generator.py: error: the following arguments are required: --n`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/bes/population.py: function `select_parent` returns a bare RNG draw (line 279) — a reported value computed from no real input; 4 command(s) failed: python code/dataset/generator.py --count 500 --output data/raw/puzzles.jsonl --scaling (rc=2); python code/main.py --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl (rc=1); python code/main.py --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl (rc=1); 7 declared deliverable(s) absent: data/processed/calibrated_tdp.json; data/processed/calibration_run.json; data/processed/distribution_report.json

## Failing / missing run-book commands

- python code/dataset/generator.py --count 500 --output data/raw/puzzles.jsonl --scaling -> rc=2
    usage: generator.py [-h] --n N [N ...] --count COUNT
                    [--types TYPES [TYPES ...]] [--output-dir OUTPUT_DIR]
                    [--seed SEED] [--max-attempts MAX_ATTEMPTS]
generator.py: error: the following arguments are required: --n
- python code/main.py --method symbolic --pop-size 50 --generations 20 --output data/processed/symbolic_run.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/main.py", line 18, in <module>
    from config import load_config, get_experiment_id, initialize_experiment
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/main.py --method neural --pop-size 50 --generations 20 --output data/processed/neural_run.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/main.py", line 18, in <module>
    from config import load_config, get_experiment_id, initialize_experiment
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-884-llmxive-follow-up-extending-self-improvi/code/config.py", line 8, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/analysis/stats.py --symbolic data/processed/symbolic_run.jsonl --neural data/processed/neural_run.jsonl --output data/processed/results.json -> rc=1
    Error: [Errno 2] No such file or directory: '--symbolic'

## Declared deliverables still missing

- data/processed/calibrated_tdp.json
- data/processed/calibration_run.json
- data/processed/distribution_report.json
- data/processed/distribution_validation.json
- data/processed/exclusions.json
- data/processed/literature_gpu_factor.json
- data/processed/scaling_raw_logs.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/calibrated_tdp.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/utils/generate_tdp_constant.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibrated_tdp.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/calibration_run.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/generate_tdp_constant.py` — NOT invoked by the run-book
    - `code/utils/calibrate_tdp.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibration_run.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/distribution_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/dataset/validate_distribution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/distribution_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/dataset/validate_distribution.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusions.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_report_generator.py` — NOT invoked by the run-book
    - `code/symbolic/parser.py` — NOT invoked by the run-book
    - `code/symbolic/exclusion_logger.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusions.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/literature_gpu_factor.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/final_report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/literature_gpu_factor.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/scaling_raw_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_pilot_scaling_experiments.py` — NOT invoked by the run-book
    - `code/run_scalability_analysis.py` — NOT invoked by the run-book
    - `code/run_scaling_experiments.py` — NOT invoked by the run-book
    - `code/run_full_symbolic_experiments.py` — NOT invoked by the run-book
    - `code/analysis/scalability_analyzer.py` — NOT invoked by the run-book
    - `code/analysis/scaling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/scaling_raw_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
