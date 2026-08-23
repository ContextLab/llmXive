# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/model_comparison.py: self-declared fabricated metric — “…ion     # For this script, we simulate the results based on the data to ensure…”
- code/analysis/model_comparison.py: self-declared fabricated metric — “…ment of the data,     # not a mock value.      # Baseline Model: Judgm…”
- code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…lated_data: DataFrame of simulated data from posterior.…”
- code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…e)      # Perform PPC if simulated data is available (simulated…”
- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…""     Validate that the simulated dataset size matches the MDES as…”
- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…r of participants in the simulated dataset.         mdes_report_pat…”
- code/analysis/validation.py: synthetic/fake INPUT data not authorized by the spec — “…to     validate that the simulated dataset size matches the MDES as…”
- code/data/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…mulation', load from the generated synthetic dataset.     If DATA_MOD…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 34 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/model_comparison.py: self-declared fabricated metric — “…ion     # For this script, we simulate the results based on the data to ensure…”; code/analysis/model_comparison.py: self-declared fabricated metric — “…ment of the data,     # not a mock value.      # Baseline Model: Judgm…”; code/analysis/model_comparison.py: synthetic/fake INPUT data not authorized by the spec — “…lated_data: DataFrame of simulated data from posterior.…”; 8 command(s) failed: python code/data/ingest.py (rc=1); python code/data/simulation.py (rc=1); python code/data/preprocess.py (rc=1); 2 declared deliverable(s) absent: data/processed/simulated_data.csv; data/processed/test.csv

## Failing / missing run-book commands

- python code/data/ingest.py -> rc=1
    '}

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/ingest.py", line 235, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/ingest.py", line 219, in main
    mfq_df = load_mfq_data()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/ingest.py", line 37, in load_mfq_data
    generate_mfq()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation_mfq.py", line 173, in main
    mdes_report = load_mdes_report()
                  ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation_mfq.py", line 35, in load_mdes_report
    raise FileNotFoundError(
FileNotFoundError: MDES report missing at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/state/mdes_report.yaml. Ensure T045 (Power Analysis) is complete before running this task.
- python code/data/simulation.py -> rc=1
    ome/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/data/simulation.py", line 48, in main
    log_pipeline_step(logger, "START", "Simulation Data Generation")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/logging_utils.py", line 174, in log_pipeline_step
    log_msg = json.dumps(log_entry)
              ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/json/__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/json/encoder.py", line 200, in encode
    chunks = self.iterencode(o, _one_shot=True)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/json/encoder.py", line 258, in iterencode
    return _iterencode(o, 0)
           ^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/json/encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type Logger is not JSON serializable
- python code/data/preprocess.py -> rc=1
    2026-08-23 06:13:48,433 - __main__ - INFO - Starting preprocessing pipeline
2026-08-23 06:13:48,434 - __main__ - INFO - Loading blend shape config from /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/config/unity_blend_shapes.yaml
2026-08-23 06:13:48,440 - __main__ - INFO - Loaded 10 story mappings
2026-08-23 06:13:48,440 - __main__ - INFO - Loading merged data from /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/merged_data.csv
2026-08-23 06:13:48,440 - __main__ - ERROR - File not found: Merged data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/merged_data.csv
2026-08-23 06:13:48,440 - __main__ - ERROR - Execution failed: Merged data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/merged_data.csv
- python code/models/bayesian.py -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/.venv/lib/python3.11/site-packages/arviz/__init__.py:50: FutureWarning: 
ArviZ is undergoing a major refactor to improve flexibility and extensibility while maintaining a user-friendly interface.
Some upcoming changes may be backward incompatible.
For details and migration guidance, visit: https://python.arviz.org/en/latest/user_guide/migration_guide.html
  warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian.py", line 218, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/models/bayesian.py", line 187, in main
    log_pipeline_step("Starting Bayesian Model Execution (T023)")
TypeError: log_pipeline_step() missing 1 required positional argument: 'status'
- python code/analysis/model_comparison.py -> rc=1
    2026-08-23 06:13:54 - model_comparison - INFO - Running Model Comparison Analysis
2026-08-23 06:13:54 - model_comparison - INFO - Data mode detected: True
2026-08-23 06:13:54 - model_comparison - ERROR - Preprocessed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/preprocessed_data.csv
- python code/analysis/validation.py -> rc=1
    alidate Sample Size against MDES
2026-08-23 06:13:55,088 - __main__ - INFO - Starting validation pipeline (T046)...
2026-08-23 06:13:55,088 - __main__ - ERROR - MDES report not found at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/state/mdes_report.yaml. Ensure T045 (power_analysis) has completed successfully.
2026-08-23 06:13:55,088 - __main__ - ERROR - Validation failed: MDES report not found at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/state/mdes_report.yaml. Ensure T045 (power_analysis) has completed successfully.
{
  "sample_size_validation": null,
  "status": "failed",
  "message": "MDES report not found at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/state/mdes_report.yaml. Ensure T045 (power_analysis) has completed successfully.",
  "error_type": "file_not_found"
}
2026-08-23 06:13:55,088 - __main__ - ERROR - T046 Validation FAILED: MDES report not found at /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/state/mdes_report.yaml. Ensure T045 (power_analysis) has completed successfully.
- python code/utils/hashing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/hashing.py", line 9, in <module>
    import logging
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/code/utils/logging.py", line 15, in <module>
    _loggers: Dict[str, logging.Logger] = {}
                        ^^^^^^^^^^^^^^
AttributeError: partially initialized module 'logging' has no attribute 'Logger' (most likely due to a circular import). Did you mean: '_loggers'?
- python code/reports/generate_report.py -> rc=1
    2026-08-23 06:13:55,394 - __main__ - INFO - Starting report generation...
2026-08-23 06:13:55,394 - __main__ - INFO - Running in True mode
2026-08-23 06:13:55,395 - __main__ - WARNING - Result file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json
2026-08-23 06:13:55,395 - __main__ - ERROR - No result data found. Cannot generate report.
2026-08-23 06:13:55,395 - __main__ - INFO - Failure report written to /home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/reports/final_validation_report.txt

## Declared deliverables still missing

- data/processed/simulated_data.csv
- data/processed/test.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 25 way(s):

- code/config.py: 1. get_path("data/processed/output.csv") -> Returns PROJECT_ROOT / "data/processed/output.csv"
- code/config.py: 2. get_path("data", "logs/exclusion.log") -> Returns PROJECT_ROOT / "data" / "logs/exclusion.log"
- code/config.py: 3. get_path("", "data/raw/file.csv") -> Returns PROJECT_ROOT / "data/raw/file.csv"
- code/config.py: raise ValueError("get_path() requires at least one path argument")
- code/config.py: full_path = get_path(file_path)
- code/models/bayesian.py: data_path = get_path("data/processed/merged_data.csv")
- code/models/bayesian.py: output_path = get_path("data/processed/model_result.json")
- code/analysis/power_analysis.py: output_path = get_path("state", "mdes_report.yaml")
- code/analysis/validation.py: mdes_report_path = str(get_path("state", "mdes_report.yaml"))
- code/analysis/model_comparison.py: data_path = get_path("data/processed/preprocessed_data.csv")
- code/analysis/model_comparison.py: output_path = get_path("data/processed/model_comparison.json")
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_mfq.csv")
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_stories.csv")
- code/data/ingest.py: data_path = get_path("data/raw/synthetic_vr_logs.csv")
- code/data/ingest.py: output_path = get_path("data/processed/merged_data.csv")
- code/data/unity_verification.py: full_path = get_path(config_path)
- code/data/unity_verification.py: full_path = get_path(output_path)
- code/data/preprocess.py: config_path = get_path(CONFIG_PATH)
- code/data/preprocess.py: data_path = get_path(MERGED_DATA_PATH)
- code/data/preprocess.py: output_path = get_path(PREPROCESSED_OUTPUT_PATH)
- code/data/simulation.py: preprocessed_path = get_path("data/processed/preprocessed_data.csv")
- code/data/simulation.py: output_path = get_path("data/processed/simulated_data.csv")
- code/data/simulation.py: get_path("data/raw/synthetic_mfq.csv"),
- code/data/simulation.py: get_path("data/raw/synthetic_stories.csv"),
- code/data/simulation.py: get_path("data/raw/synthetic_vr_logs.csv"),

Make `get_path` in `code/config.py` accept ALL of the above.

### `log_pipeline_step` — defined in `code/utils/logging.py`; called 16 way(s):

- code/models/regression.py: log_pipeline_step("regression_pipeline", "completed", str(output_path))
- code/models/bayesian.py: log_pipeline_step("Starting Bayesian Model Execution (T023)")
- code/analysis/model_comparison.py: log_pipeline_step("model_comparison", status="completed")
- code/data/ingest.py: log_pipeline_step("start_ingestion", DATA_MODE)
- code/data/ingest.py: log_pipeline_step("end_ingestion", {"records": len(validated_df)})
- code/data/ingest.py: log_pipeline_step("end_ingestion_failed", {"error": str(e)})
- code/data/simulation.py: log_pipeline_step(logger, "START", "Simulation Data Generation")
- code/data/simulation.py: log_pipeline_step(logger, "COMPLETE", "Simulation Data Generation")
- code/data/simulation_stories.py: log_pipeline_step("Starting Moral Stories and VR Logs simulation")
- code/data/simulation_stories.py: log_pipeline_step(
- code/data/simulation_mfq.py: log_pipeline_step("START", "T013: Synthetic MFQ Generation")
- code/data/simulation_mfq.py: log_pipeline_step("SUCCESS", "T013: Synthetic MFQ Generation completed")
- code/tests/test_logging_infrastructure.py: log_pipeline_step(
- code/utils/logging.py: log_pipeline_step("TEST", "Logging infrastructure test")
- code/utils/hashing.py: log_pipeline_step("hashing", f"Updated {len(hashes)} checksums in {STATE_FILE}")
- code/utils/hashing.py: log_pipeline_step("hashing", "Starting artifact checksumming for simulation-derived data")

Make `log_pipeline_step` in `code/utils/logging.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/utils/logging.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/utils/logging.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/simulated_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/model_comparison.py` — IS a run-book command
    - `code/data/simulation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/simulated_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/refactor_cleanup.py` — NOT invoked by the run-book
    - `code/models/regression.py` — NOT invoked by the run-book
    - `code/analysis/validation.py` — IS a run-book command
    - `code/analysis/model_comparison.py` — IS a run-book command
    - `code/data/ingest_real.py` — NOT invoked by the run-book
    - `code/tests/test_edge_cases.py` — NOT invoked by the run-book
    - `code/tests/test_model_recovery.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/merged_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/models/regression.py`, `code/models/bayesian.py`, `code/data/ingest.py`, `code/data/preprocess.py`, `code/data/simulation.py`, `code/utils/hashing.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/merged_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/quickstart_validation.py`, `code/models/regression.py`, `code/models/bayesian.py`, `code/data/ingest.py`, `code/data/preprocess.py`, `code/data/simulation.py`, `code/utils/hashing.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/reports/generate_report.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-134-the-cognitive-mechanisms-underlying-intu/data/processed/model_results.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/reports/generate_report.py`.
