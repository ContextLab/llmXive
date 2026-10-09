# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/renderer.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic event log for testing pu…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode render --seed 42 --steps 10 --verify-consistency`
  - argparse error: `{"timestamp": "2026-10-09T08:19:59.821588Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: unrecognized arguments: --steps 10 --verify-consistency", "module": "logger", "function": "write", "line": 93}`
- run-book command: `python code/main.py --mode full --seeds 42,100,200 --model qwen2-3b --runs 20`
  - argparse error: `{"timestamp": "2026-10-09T08:19:59.864751Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: unrecognized arguments: --model qwen2-3b --runs 20", "module": "logger", "function": "write", "line": 93}`
- run-book command: `python code/main.py --mode scale --runs 64 --model qwen2-3b`
  - argparse error: `{"timestamp": "2026-10-09T08:19:59.906854Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: the following arguments are required: --seeds", "module": "logger", "function": "write", "line": 93}`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/renderer.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic event log for testing pu…”; 5 command(s) failed: python code/main.py --mode render --seed 42 --steps 10 --verify-consistency (rc=2); python code/main.py --mode full --seeds 42,100,200 --model qwen2-3b --runs 20 (rc=2); python code/main.py --mode scale --runs 64 --model qwen2-3b (rc=2)

## Failing / missing run-book commands

- python code/main.py --mode render --seed 42 --steps 10 --verify-consistency -> rc=2
{"timestamp": "2026-10-09T08:19:59.821509Z", "level": "INFO", "logger": "llmxive", "message": "usage: main.py [-h] [--mode {pilot,full,scale,render}] --seeds SEEDS", "module": "logger", "function": "write", "line": 93}
{"timestamp": "2026-10-09T08:19:59.821588Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: unrecognized arguments: --steps 10 --verify-consistency", "module": "logger", "function": "write", "line": 93}


- python code/main.py --mode full --seeds 42,100,200 --model qwen2-3b --runs 20 -> rc=2
{"timestamp": "2026-10-09T08:19:59.864670Z", "level": "INFO", "logger": "llmxive", "message": "usage: main.py [-h] [--mode {pilot,full,scale,render}] --seeds SEEDS", "module": "logger", "function": "write", "line": 93}
{"timestamp": "2026-10-09T08:19:59.864751Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: unrecognized arguments: --model qwen2-3b --runs 20", "module": "logger", "function": "write", "line": 93}


- python code/main.py --mode scale --runs 64 --model qwen2-3b -> rc=2
{"timestamp": "2026-10-09T08:19:59.906773Z", "level": "INFO", "logger": "llmxive", "message": "usage: main.py [-h] [--mode {pilot,full,scale,render}] --seeds SEEDS", "module": "logger", "function": "write", "line": 93}
{"timestamp": "2026-10-09T08:19:59.906854Z", "level": "INFO", "logger": "llmxive", "message": "main.py: error: the following arguments are required: --seeds", "module": "logger", "function": "write", "line": 93}


- python -m pytest tests/ -> rc=2
ROR tests/integration/test_checksum_integration.py
ERROR tests/integration/test_full_loop.py - TypeError: get_logger() takes 0 p...
ERROR tests/unit/test_agent_error_handling.py - TypeError: get_logger() takes...
ERROR tests/unit/test_agent_loop.py - TypeError: get_logger() takes 0 positio...
ERROR tests/unit/test_agent_step_limit.py - TypeError: get_logger() takes 0 p...
ERROR tests/unit/test_baseline_adapter.py - TypeError: get_logger() takes 0 p...
ERROR tests/unit/test_baseline_runner.py - TypeError: get_logger() takes 0 po...
ERROR tests/unit/test_checksum.py
ERROR tests/unit/test_config_loader.py
ERROR tests/unit/test_context_truncation.py - TypeError: get_logger() takes 0...
ERROR tests/unit/test_context_window.py - TypeError: get_logger() takes 0 pos...
ERROR tests/unit/test_contracts.py
ERROR tests/unit/test_hasher.py
ERROR tests/unit/test_renderer_validator.py
ERROR tests/unit/test_renderer_visual.py
ERROR tests/unit/test_scorer.py
ERROR tests/unit/test_step_limit.py - TypeError: get_logger() takes 0 positio...
!!!!!!!!!!!!!!!!!!! Interrupted: 17 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 17 errors in 5.98s ==============================


- python utils/hasher.py --verify -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c/utils/hasher.py", line 19, in <module>
    logger = get_logger(__name__)
             ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

