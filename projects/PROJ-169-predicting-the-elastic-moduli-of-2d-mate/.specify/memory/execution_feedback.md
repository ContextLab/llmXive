# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/importance.py: synthetic/fake INPUT data not authorized by the spec — “…will instantiate with a dummy input size and then load state…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/results/bias_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/ingest/filter.py --input data/processed --output data/filtered`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/model/train.py --data-dir data/filtered --epochs 100 --patience 3 --split-strategy family`
  - script usage: `train.py [-h] [--config CONFIG] [--epochs EPOCHS] [--patience PATIENCE]`
  - argparse error: `train.py: error: unrecognized arguments: --data-dir data/filtered --split-strategy family`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/importance.py: synthetic/fake INPUT data not authorized by the spec — “…will instantiate with a dummy input size and then load state…”; every produced artifact is gitignored (data/results/bias_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/ingest/download.py --output data/raw (rc=1); python code/ingest/bias_check.py --input data/raw --output data/bias_report.json (rc=1); python code/ingest/filter.py --input data/processed --output data/filtered (rc=1); 5 declared deliverable(s) absent: data/processed/graphs_v1.parquet; data/processed/split_indices.json; data/results/generalization_metrics.json

## Failing / missing run-book commands

- python code/ingest/download.py --output data/raw -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/download.py", line 20, in <module>
    from ingest.validator import enforce_single_source
ModuleNotFoundError: No module named 'ingest.validator'
- python code/ingest/bias_check.py --input data/raw --output data/bias_report.json -> rc=1
    2026-07-19 20:01:02,198 - __main__ - INFO - Starting bias check analysis...
2026-07-19 20:01:02,198 - root - WARNING - Exclusion log not found at /home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/data/processed/exclusion_log.json. Returning empty list.
2026-07-19 20:01:02,198 - __main__ - WARNING - No exclusion logs found. Generating empty report.
2026-07-19 20:01:02,199 - root - INFO - Bias report written to data/results/bias_report.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/bias_check.py", line 159, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/bias_check.py", line 155, in main
    write_bias_report(report, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/bias_check.py", line 105, in write_bias_report
    log_bias_check(report.summary)
TypeError: log_bias_check() missing 1 required positional argument: 'report'
- python code/ingest/filter.py --input data/processed --output data/filtered -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/filter.py", line 218, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/ingest/filter.py", line 186, in main
    raise ValueError(f"Unsupported input format: {input_path.suffix}. Use .json for this test.")
ValueError: Unsupported input format: . Use .json for this test.
- python code/model/train.py --data-dir data/filtered --epochs 100 --patience 3 --split-strategy family -> rc=2
    usage: train.py [-h] [--config CONFIG] [--epochs EPOCHS] [--patience PATIENCE]
                [--batch_size BATCH_SIZE] [--lr LR] [--data_path DATA_PATH]
                [--split_path SPLIT_PATH] [--output_log OUTPUT_LOG]
                [--output_test_indices OUTPUT_TEST_INDICES]
train.py: error: unrecognized arguments: --data-dir data/filtered --split-strategy family
- python code/analysis/importance.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/analysis/importance.py", line 520, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/analysis/importance.py", line 500, in main
    parser = argparse.ArgumentParser(description="Calculate Permutation Importance")
             ^^^^^^^^
NameError: name 'argparse' is not defined
- python code/analysis/ablation.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/analysis/ablation.py", line 17, in <module>
    from matminer.featurizers.composition import MagpieData
ImportError: cannot import name 'MagpieData' from 'matminer.featurizers.composition' (/home/runner/work/llmXive/llmXive/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/code/.venv/lib/python3.11/site-packages/matminer/featurizers/composition/__init__.py)

## Declared deliverables still missing

- data/processed/graphs_v1.parquet
- data/processed/split_indices.json
- data/results/generalization_metrics.json
- data/results/terminology_audit.json
- data/results/training_logs.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_bias_check` — defined in `code/utils/logger.py`; called 1 way(s):

- code/ingest/bias_check.py: log_bias_check(report.summary)

Make `log_bias_check` in `code/utils/logger.py` accept ALL of the above.

### class `Config` (in `code/utils/config.py`) — accessed via method/attribute names this round: `paths`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.paths` call sites (0):

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/utils/logger.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/utils/logger.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

```python
"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)
```

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/graphs_v1.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/model/cv_runner.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/baseline_metrics.py` — NOT invoked by the run-book
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/ingest/pipeline.py` — NOT invoked by the run-book
    - `code/ingest/parse_cif.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/graphs_v1.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_indices.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/ingest/pipeline.py` — NOT invoked by the run-book
    - `code/analysis/importance.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/split_indices.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/generalization_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/model/eval_runner.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/inference_benchmark.py` — NOT invoked by the run-book
    - `code/model/metrics_aggregator.py` — NOT invoked by the run-book
    - `code/model/disclaimer_injector.py` — NOT invoked by the run-book
    - `code/model/generalization_test.py` — NOT invoked by the run-book
    - `code/analysis/aggregate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/generalization_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/terminology_audit.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/terminology_audit.py` — NOT invoked by the run-book
    - `code/utils/terminology_scanner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/terminology_audit.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/training_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/model/eval_runner.py` — NOT invoked by the run-book
    - `code/model/train_logger.py` — NOT invoked by the run-book
    - `code/model/cv_runner.py` — NOT invoked by the run-book
    - `code/model/train.py` — IS a run-book command
    - `code/model/train_config.py` — NOT invoked by the run-book
    - `code/model/disclaimer_injector.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/training_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
