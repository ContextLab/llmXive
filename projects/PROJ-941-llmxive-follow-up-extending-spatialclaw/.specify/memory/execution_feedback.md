# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: function `random_float` returns a bare RNG draw (line 67) — a reported value computed from no real input
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…code/data/generator.py  Generates the Synthetic SpatialClaw Proxy datase…”
- code/pipeline_runner.py: synthetic/fake INPUT data not authorized by the spec — “…"""Execute T006a/b: Generate the Synthetic SpatialClaw Proxy datase…”
- code/stats/analyze_projection_loss.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Load the raw synthetic dataset and index by task_id.…”
- code/stats/execute_projection_loss.py: synthetic/fake INPUT data not authorized by the spec — “…help="Path to the raw synthetic dataset JSON (for ground truth l…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/stats/sensitivity.py --input results/logs/combined_metrics.csv`
  - script usage: `sensitivity.py [-h] [--dataset DATASET] [--paired PAIRED]`
  - argparse error: `sensitivity.py: error: unrecognized arguments: --input results/logs/combined_metrics.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: function `random_float` returns a bare RNG draw (line 67) — a reported value computed from no real input; code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…code/data/generator.py  Generates the Synthetic SpatialClaw Proxy datase…”; code/pipeline_runner.py: synthetic/fake INPUT data not authorized by the spec — “…"""Execute T006a/b: Generate the Synthetic SpatialClaw Proxy datase…”; 4 command(s) failed: python code/data/loader.py --mode generate --output data/raw/synthetic_spatialclaw.jsonl (rc=1); python code/main.py --agent 2d --tasks occlusion --runs 5 --seed 42 (rc=1); python code/main.py --agent 3d --tasks occlusion --runs 5 --seed 42 (rc=1); 1 declared deliverable(s) absent: data/raw/synthetic_spatialclaw_v1.json

## Failing / missing run-book commands

- python code/data/loader.py --mode generate --output data/raw/synthetic_spatialclaw.jsonl -> rc=1
Attempting to load dataset from: data/raw/synthetic_spatialclaw_v1.json
CRITICAL ERROR: [Errno 2] No such file or directory: 'data/raw/synthetic_spatialclaw_v1.json'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/data/loader.py", line 273, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/data/loader.py", line 237, in main
    file_size = os.path.getsize(FULL_PATH)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen genericpath>", line 50, in getsize
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/synthetic_spatialclaw_v1.json'

- python code/main.py --agent 2d --tasks occlusion --runs 5 --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/main.py", line 21, in <module>
    from code.utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/utils/logging_config.py", line 280, in <module>
    def extract_seed_usage(log_file: str = None) -> List[Dict[str, Any]]:
                                                    ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/main.py --agent 3d --tasks occlusion --runs 5 --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/main.py", line 21, in <module>
    from code.utils.logging_config import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-941-llmxive-follow-up-extending-spatialclaw/code/utils/logging_config.py", line 280, in <module>
    def extract_seed_usage(log_file: str = None) -> List[Dict[str, Any]]:
                                                    ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/stats/sensitivity.py --input results/logs/combined_metrics.csv -> rc=2

usage: sensitivity.py [-h] [--dataset DATASET] [--paired PAIRED]
                      [--output OUTPUT] [--epsilons EPSILONS [EPSILONS ...]]
sensitivity.py: error: unrecognized arguments: --input results/logs/combined_metrics.csv


## Declared deliverables still missing

- data/raw/synthetic_spatialclaw_v1.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/synthetic_spatialclaw_v1.json` is declared but was NOT written. Scripts referencing it:
    - `code/agents/agent_2d.py` — NOT invoked by the run-book
    - `code/agents/baseline_3d.py` — NOT invoked by the run-book
    - `code/agents/run_baseline_3d.py` — NOT invoked by the run-book
    - `code/data/generator.py` — NOT invoked by the run-book
    - `code/data/loader.py` — IS a run-book command
    - `code/data/projector.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/pipeline_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_spatialclaw_v1.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
