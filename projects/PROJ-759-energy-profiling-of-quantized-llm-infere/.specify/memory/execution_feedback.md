# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.benchmark  --prompt-length 500  --repetitions 5  --output-dir data/results  --log-dir logs`
  - script usage: `benchmark.py [-h] --config CONFIG [--dry-run]`
  - argparse error: `benchmark.py: error: the following arguments are required: --config`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -c " (rc=-1); python -m code.benchmark  --prompt-length 500  --repetitions 5  --output-dir data/results  --log-dir logs (rc=2); python -m pytest -q tests/contract (rc=2); 1 declared deliverable(s) absent: data/raw/wikitext2.parquet

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
---------------
2026-10-14 17:11:32,364 WARNING code.utils.quantize: auto-gptq not available (pyarrow requires NumPy 2.0 or newer, found 1.26.4); quantization will be skipped.
_ ERROR collecting projects/PROJ-759-energy-profiling-of-quantized-llm-infere/tests/contract/test_wikitext2_download.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-759-energy-profiling-of-quantized-llm-infere/tests/contract/test_wikitext2_download.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_wikitext2_download.py:14: in <module>
    from utils.data_loader import download_wikitext2
E   ModuleNotFoundError: No module named 'utils.data_loader'
=========================== short test summary info ============================
ERROR tests/contract/test_quantize_config.py - AttributeError: module jsonsch...
ERROR tests/contract/test_wikitext2_download.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 3.90s



## Declared deliverables still missing

- data/raw/wikitext2.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/wikitext2.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/utils/data_loader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/wikitext2.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
