# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: function `generate_turn_text` returns a bare RNG draw (line 77) — a reported value computed from no real input
- code/data/generate_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…(US-1: "The system MUST generate synthetic conflict dialogue trajec…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…int) -> str:     """     Generates a synthetic dialogue turn based on m…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…adata.     Note: This is synthetic data generation as per the pr…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/generate_trajectories.py --download-only '#' creates data/raw/`
  - script usage: `generate_trajectories.py [-h] [--oversample-high-emotion]`
  - argparse error: `generate_trajectories.py: error: unrecognized arguments: --download-only # creates data/raw/`
- run-book command: `python code/data/generate_trajectories.py --oversample-high-difficulty --num-trajectories 120`
  - script usage: `generate_trajectories.py [-h] [--oversample-high-emotion]`
  - argparse error: `generate_trajectories.py: error: unrecognized arguments: --oversample-high-difficulty`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: function `generate_turn_text` returns a bare RNG draw (line 77) — a reported value computed from no real input; code/data/generate_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…(US-1: "The system MUST generate synthetic conflict dialogue trajec…”; code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…int) -> str:     """     Generates a synthetic dialogue turn based on m…”; 4 run-book script(s) missing (plan/impl path mismatch): python src/data/split_dataset.py --train-ratio 0.6; python src/data/classifier_training.py; python src/analysis/stats_utils.py; 3 command(s) failed: python code/data/generate_trajectories.py --download-only '#' creates data/raw/ (rc=2); python code/data/generate_trajectories.py --oversample-high-difficulty --num-trajectories 120 (rc=2); python code/experiments/runner.py --models llama-3-8b,mistral-7b,gemma-2b,phi-2b,openchat-3.5,starling-7b,qwen-7b,gemma-7b --conditions adapter,static --batch-size 4 (rc=1); 2 declared deliverable(s) absent: data/results/scope_adjustments.json; data/results/stats_report.json

## Failing / missing run-book commands

- python code/data/generate_trajectories.py --download-only '#' creates data/raw/ -> rc=2

usage: generate_trajectories.py [-h] [--oversample-high-emotion]
                                [--oversample-diverse-cultural]
                                [--num-trajectories NUM_TRAJECTORIES]
                                [--seed SEED]
generate_trajectories.py: error: unrecognized arguments: --download-only # creates data/raw/

- python code/data/generate_trajectories.py --oversample-high-difficulty --num-trajectories 120 -> rc=2

usage: generate_trajectories.py [-h] [--oversample-high-emotion]
                                [--oversample-diverse-cultural]
                                [--num-trajectories NUM_TRAJECTORIES]
                                [--seed SEED]
generate_trajectories.py: error: unrecognized arguments: --oversample-high-difficulty

- python src/data/split_dataset.py --train-ratio 0.6 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-885-llmxive-follow-up-extending-socrates-tow/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/data/split_dataset.py': [Errno 2] No such file or directory

- python src/data/classifier_training.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-885-llmxive-follow-up-extending-socrates-tow/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/data/classifier_training.py': [Errno 2] No such file or directory

- python code/experiments/runner.py --models llama-3-8b,mistral-7b,gemma-2b,phi-2b,openchat-3.5,starling-7b,qwen-7b,gemma-7b --conditions adapter,static --batch-size 4 -> rc=1
Xive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/experiments/runner.py", line 20, in <module>
    from experiments.prompts import get_static_baseline_prompt, get_dynamic_adapter_prompt
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/experiments/__init__.py", line 2, in <module>
    from .runner import enforce_cpu_only_execution, load_classifier, run_single_turn_inference, get_state_for_turn, process_trajectory, run_experiment, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/experiments/runner.py", line 20, in <module>
    from experiments.prompts import get_static_baseline_prompt, get_dynamic_adapter_prompt
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/experiments/prompts.py", line 23, in <module>
    SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY: (
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/enum.py", line 786, in __getattr__
    raise AttributeError(name) from None
AttributeError: HIGH_EMOTIONAL_REACTIVITY

- python src/analysis/stats_utils.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-885-llmxive-follow-up-extending-socrates-tow/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/src/analysis/stats_utils.py': [Errno 2] No such file or directory

- python tests/integration/test_full_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-885-llmxive-follow-up-extending-socrates-tow/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/tests/integration/test_full_pipeline.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/results/scope_adjustments.json
- data/results/stats_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/scope_adjustments.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis/verify_correction.py` — NOT invoked by the run-book
    - `code/analysis/verify_exclusion_citations.py` — NOT invoked by the run-book
    - `code/experiments/runner.py` — IS a run-book command
  Make ONE of these WRITE `data/results/scope_adjustments.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stats_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/verify_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stats_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
