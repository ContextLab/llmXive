# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.benchmark  --prompt-length 500  --repetitions 5  --output-dir data/results  --log-dir logs`
  - script usage: `benchmark.py [-h] --config CONFIG [--dry-run]`
  - argparse error: `benchmark.py: error: the following arguments are required: --config`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -c " (rc=-1); python -m code.benchmark  --prompt-length 500  --repetitions 5  --output-dir data/results  --log-dir logs (rc=2); python -m pytest -q tests/contract (rc=2)

## Failing / missing run-book commands

- python -c " -> rc=-1
unparseable command (shlex)
- python -m code.benchmark  --prompt-length 500  --repetitions 5  --output-dir data/results  --log-dir logs -> rc=2

usage: benchmark.py [-h] --config CONFIG [--dry-run]
                    [--prompt-length PROMPT_LENGTH]
                    [--repetitions REPETITIONS] [--output-dir OUTPUT_DIR]
                    [--log-dir LOG_DIR]
benchmark.py: error: the following arguments are required: --config

- python -m pytest -q tests/contract -> rc=2
===========
_ ERROR collecting projects/PROJ-759-energy-profiling-of-quantized-llm-infere/tests/contract/test_quantize_config.py _
tests/contract/test_quantize_config.py:21: in <module>
    schema = jsonschema.load(f)
/home/runner/.cache/llmxive/base-env/py311-6f1866971868/jsonschema/__init__.py:105: in __getattr__
    raise AttributeError(f"module {__name__} has no attribute {name}")
E   AttributeError: module jsonschema has no attribute load
------------------------------- Captured stderr --------------------------------
2026-10-14 19:22:59,307 INFO datasets: PyTorch version 2.3.0 available.
2026-10-14 19:22:59,719 WARNING code.utils.quantize: auto-gptq not available (cannot import name 'clear_device_cache' from 'accelerate.utils.memory' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-759-energy-profiling-of-quantized-llm-infere/lib/python3.11/site-packages/accelerate/utils/memory.py)); quantization will be skipped.
=========================== short test summary info ============================
ERROR tests/contract/test_quantize_config.py - AttributeError: module jsonsch...
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 3.91s


