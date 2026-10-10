# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/mock_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…a fallback mechanism to generate deterministic synthetic task traces and success…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data_loader.py --download --dataset alfworld/alfworld`
  - script usage: `data_loader.py [-h] [--sample SAMPLE]`
  - argparse error: `data_loader.py: error: unrecognized arguments: --download --dataset alfworld/alfworld`
- run-book command: `python code/data_loader.py --verify`
  - script usage: `data_loader.py [-h] [--sample SAMPLE]`
  - argparse error: `data_loader.py: error: unrecognized arguments: --verify`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/mock_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…a fallback mechanism to generate deterministic synthetic task traces and success…”; 5 command(s) failed: python code/data_loader.py --download --dataset alfworld/alfworld (rc=2); python code/data_loader.py --verify (rc=2); python code/main.py --config config/default.yaml (rc=1); 3 declared deliverable(s) absent: data/results/error_analysis_log.json; data/results/latency_violations.json; data/results/memory_check.json

## Failing / missing run-book commands

- python code/data_loader.py --download --dataset alfworld/alfworld -> rc=2

usage: data_loader.py [-h] [--sample SAMPLE]
data_loader.py: error: unrecognized arguments: --download --dataset alfworld/alfworld

- python code/data_loader.py --verify -> rc=2

usage: data_loader.py [-h] [--sample SAMPLE]
data_loader.py: error: unrecognized arguments: --verify

- python code/main.py --config config/default.yaml -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/main.py", line 21, in <module>
    def run_comparative_pipeline(config: Dict[str, Any]):
                                         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/main.py --granularity fine --predicates spatial+temporal -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/main.py", line 21, in <module>
    def run_comparative_pipeline(config: Dict[str, Any]):
                                         ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

- python code/experiment_runner.py --mode baseline-only -> rc=1
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/data_loader.py", line 41, in stream_alfworld_traces
    raise RuntimeError(
RuntimeError: Failed to load ALFWorld traces from remote or local sources. Error: pyarrow requires NumPy 2.0 or newer, found 1.26.4. Please ensure 'data/raw/' contains valid trace files or 'datasets' package is installed with network access.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/experiment_runner.py", line 276, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/experiment_runner.py", line 273, in main
    run_sweep(sample_size=args.sample_size)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos/code/experiment_runner.py", line 170, in run_sweep
    raise RuntimeError("Baseline acquisition failed: No reproducible artifact found.")
RuntimeError: Baseline acquisition failed: No reproducible artifact found.


## Declared deliverables still missing

- data/results/error_analysis_log.json
- data/results/latency_violations.json
- data/results/memory_check.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/error_analysis_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/error_analysis.py` — NOT invoked by the run-book
    - `code/experiment_runner.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/error_analysis_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/latency_violations.json` is declared but was NOT written. Scripts referencing it:
    - `code/latency_guard.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/latency_violations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/memory_check.json` is declared but was NOT written. Scripts referencing it:
    - `code/graph_builder.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/memory_check.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
