# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…cution halted to prevent synthetic data fabrication.")…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…s this check or generate fake data.\n"             "=" * 70…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…ta requirement disabled. Synthetic data generation is permitted.…”
- code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…line configured to allow synthetic data.")  def main():     """…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…oad real NAB/UCI data OR generate synthetic time-series via `synthpo…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic time-series data mimicki…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Saved synthetic data to {output_path}")     r…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…a is False or fails,     generates synthetic data. Validates the resu…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…cution halted to prevent synthetic data fabrication.")…”; code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…s this check or generate fake data.\n"             "=" * 70…”; code/data_collection_trigger.py: synthetic/fake INPUT data not authorized by the spec — “…ta requirement disabled. Synthetic data generation is permitted.…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/extract_features.py --mode simulate --n 500 --signal; python code/extract_features.py --mode simulate --n 500 --null; python code/extract_features.py --mode real; 6 command(s) failed: python code/compute_metrics.py (rc=1); python code/analyze.py (rc=1); python code/visualize.py (rc=1)

## Failing / missing run-book commands

- python -c "import openface; import librosa; import statsmodels; import synthpop; print('Dependencies OK')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'openface'
- python code/extract_features.py --mode simulate --n 500 --signal -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py': [Errno 2] No such file or directory
- python code/extract_features.py --mode simulate --n 500 --null -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py': [Errno 2] No such file or directory
- python code/compute_metrics.py -> rc=1
    2026-10-03 07:37:11,126 - __main__ - ERROR - Input file not found: data/processed/features.csv
2026-10-03 07:37:11,126 - __main__ - ERROR - Please ensure T013 and T014 have completed successfully.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 246, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 218, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined
- python code/analyze.py -> rc=1
    2026-10-03 07:37:12,131 - __main__ - ERROR - Input file not found: data/processed/features.csv
- python code/visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 14, in <module>
    logger = get_logger()
             ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 12, in get_logger
    return get_logger(__name__)
           ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given
- python code/extract_features.py --mode real -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/extract_features.py': [Errno 2] No such file or directory
- python code/compute_metrics.py -> rc=1
    2026-10-03 07:37:13,508 - __main__ - ERROR - Input file not found: data/processed/features.csv
2026-10-03 07:37:13,508 - __main__ - ERROR - Please ensure T013 and T014 have completed successfully.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 246, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/compute_metrics.py", line 218, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined
- python code/analyze.py -> rc=1
    2026-10-03 07:37:14,247 - __main__ - ERROR - Input file not found: data/processed/features.csv
- python code/visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 14, in <module>
    logger = get_logger()
             ^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-344-the-impact-of-emotional-expression-in-ai/code/visualize.py", line 12, in get_logger
    return get_logger(__name__)
           ^^^^^^^^^^^^^^^^^^^^
TypeError: get_logger() takes 0 positional arguments but 1 was given

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/visualize.py`; called 18 way(s):

- code/data_collection.py: logger = get_logger(__name__)
- code/data_collection.py: self.logger = get_logger(self.__class__.__name__)
- code/update_associational_framing.py: logger = get_logger("T017_framing")
- code/extract_vocal.py: logger = get_logger(__name__)
- code/utils.py: logger = get_logger()
- code/generate_unified_report.py: logger = get_logger()
- code/extract_facial.py: logger = get_logger()
- code/compute_metrics.py: logger = get_logger(__name__)
- code/benchmark.py: logger = get_logger(__name__)
- code/monitor_resources.py: logger = get_logger(__name__)
- code/visualize.py: return get_logger(__name__)
- code/visualize.py: logger = get_logger()
- code/logging_config.py: logger = get_logger()
- code/data_loader.py: logger = get_logger(__name__)
- code/validate_outputs.py: logger = get_logger()
- code/data_collection_trigger.py: logger = get_logger(__name__)
- code/export_figure.py: logger = get_logger(__name__)
- code/analyze.py: logger = get_logger(__name__)

Make `get_logger` in `code/visualize.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/visualize.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/visualize.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/features.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/extract_vocal.py`, `code/extract_facial.py`, `code/compute_metrics.py`, `code/analyze.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/features.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/extract_vocal.py`, `code/extract_facial.py`, `code/compute_metrics.py`, `code/export_figure.py`, `code/analyze.py`.
