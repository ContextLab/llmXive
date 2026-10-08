# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/complexity.py: self-declared fabricated metric — “…# Fallback: return 0 or a dummy value if psutil is not installed…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json`
  - script usage: `sensitivity_analysis.py [-h] [--metrics-path METRICS_PATH]`
  - argparse error: `sensitivity_analysis.py: error: unrecognized arguments: --input data/processed/prs_metrics.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/complexity.py: self-declared fabricated metric — “…# Fallback: return 0 or a dummy value if psutil is not installed…”; 7 command(s) failed: python code/data/fetch_github.py --output data/raw/prs_raw.json (rc=1); python code/data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv (rc=1); python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv (rc=1); 10 declared deliverable(s) absent: data/audit/error_rate.json; data/audit/manual_audit_results.json; data/processed/complexity_scores.csv

## Failing / missing run-book commands

- python code/data/fetch_github.py --output data/raw/prs_raw.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/data/fetch_github.py", line 339, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/data/fetch_github.py", line 291, in main
    log_config = setup_logging(script_name="fetch_github")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: setup_logging() got an unexpected keyword argument 'script_name'
- python code/data/classify_prs.py --input data/raw/prs_raw.json --output data/processed/prs_labeled.csv -> rc=1
    a/logs/classify_prs.log")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/utils/logging.py", line 72, in setup_logging
    file_handler = RotatingFileHandler(
                   ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/handlers.py", line 155, in __init__
    BaseRotatingHandler.__init__(self, filename, mode, encoding=encoding,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/handlers.py", line 58, in __init__
    logging.FileHandler.__init__(self, filename, mode=mode,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/data/logs/data/logs/classify_prs.log'
- python code/data/extract_metrics.py --input data/processed/prs_labeled.csv --output data/processed/prs_metrics.csv -> rc=1
    2026-10-08 15:32:12,430 - __main__ - INFO - Starting PR metrics extraction pipeline (T022)
2026-10-08 15:32:12,430 - __main__ - INFO - Loading labeled PRs from /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_prs_labeled
2026-10-08 15:32:12,430 - __main__ - ERROR - Input file error: Required input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_prs_labeled. Ensure T017 (save_labeled_dataset) has completed successfully.
2026-10-08 15:32:12,430 - __main__ - ERROR - Pipeline failed
- python code/analysis/statistical_tests.py --input data/processed/prs_metrics.csv --output reports/results.json -> rc=1
    etrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_metrics
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 233, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 217, in main
    results = run_statistical_tests()
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 192, in run_statistical_tests
    data = load_metrics_data()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/statistical_tests.py", line 27, in load_metrics_data
    raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
FileNotFoundError: Metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_metrics
- python code/analysis/visualizations.py --input data/processed/prs_metrics.csv --output reports/figures/ -> rc=1
    llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_metrics_csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/visualizations.py", line 547, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/visualizations.py", line 532, in main
    results = run_visualization_pipeline()
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/visualizations.py", line 483, in run_visualization_pipeline
    df = load_metrics_for_viz(metrics_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/code/analysis/visualizations.py", line 111, in load_metrics_for_viz
    raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
FileNotFoundError: Metrics file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-320-evaluating-the-impact-of-code-generation/processed_metrics_csv
- python code/analysis/sensitivity_analysis.py --input data/processed/prs_metrics.csv --output reports/sensitivity_results.json -> rc=2
    usage: sensitivity_analysis.py [-h] [--metrics-path METRICS_PATH]
                               [--labeled-path LABELED_PATH]
                               [--output-path OUTPUT_PATH]
                               [--detector-threshold DETECTOR_THRESHOLD]
                               [--seed SEED]
sensitivity_analysis.py: error: unrecognized arguments: --input data/processed/prs_metrics.csv
- python code/audit/manual_validation.py --input data/processed/prs_metrics.csv --output data/processed/audit_log.csv -> rc=1
    2026-10-08 15:32:16,813 - __main__ - INFO - Starting manual validation audit for data/processed/prs_metrics.csv
2026-10-08 15:32:16,813 - __main__ - ERROR - Input file not found: data/processed/prs_metrics.csv. Ensure T017 (save_labeled_dataset) has completed.

## Declared deliverables still missing

- data/audit/error_rate.json
- data/audit/manual_audit_results.json
- data/processed/complexity_scores.csv
- data/processed/gate_status.json
- data/processed/prs_labeled.csv
- data/processed/prs_metrics.csv
- data/processed/results.json
- figures/boxplots.pdf
- figures/final_report.pdf
- figures/histograms.pdf

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `setup_logging` — defined in `code/utils/logging.py`; called 19 way(s):

- code/utils/logging.py: Assumes logging has been setup via setup_logging().
- code/utils/logging.py: setup_logging()
- code/utils/logging.py: setup_logging(log_file=log_file)
- code/utils/batch_processor.py: setup_logging()
- code/data/save_labeled_dataset.py: setup_logging()
- code/data/classify_prs.py: setup_logging(log_file="data/logs/classify_prs.log")
- code/data/extract_metrics.py: setup_logging()
- code/data/optimize_metrics_extraction.py: setup_logging()
- code/data/save_metrics.py: setup_logging()
- code/data/fetch_github.py: log_config = setup_logging(script_name="fetch_github")
- code/audit/manual_validation.py: setup_logging()
- code/analysis/statistical_tests.py: setup_logging()
- code/analysis/generate_final_report_pdf.py: logger = setup_logging('generate_final_report_pdf', log_dir)
- code/analysis/sensitivity_analysis.py: setup_logging(log_level='INFO')
- code/analysis/complexity.py: setup_logging()
- code/analysis/generate_results_report.py: logger = setup_logging("generate_results_report", log_dir / "generate_results_report.log")
- code/analysis/save_complexity_scores.py: setup_logging()
- code/analysis/optimize_complexity_processing.py: setup_logging()
- code/analysis/generate_final_report.py: logger = setup_logging("generate_final_report", "data/logs/final_report.log")

Make `setup_logging` in `code/utils/logging.py` accept ALL of the above.

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

- `data/audit/error_rate.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/audit/error_rate.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/audit/manual_audit_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/audit/manual_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/audit/manual_audit_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/complexity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/save_complexity_scores.py` — NOT invoked by the run-book
    - `code/analysis/optimize_complexity_processing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/complexity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gate_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_results_report.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gate_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prs_labeled.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/save_labeled_dataset.py` — NOT invoked by the run-book
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
    - `code/analysis/complexity.py` — NOT invoked by the run-book
    - `code/analysis/save_complexity_scores.py` — NOT invoked by the run-book
    - `code/analysis/optimize_complexity_processing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prs_labeled.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prs_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_metrics.py` — IS a run-book command
    - `code/data/optimize_metrics_extraction.py` — NOT invoked by the run-book
    - `code/data/save_metrics.py` — NOT invoked by the run-book
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/prs_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/results.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/batch_processor.py` — NOT invoked by the run-book
    - `code/data/save_labeled_dataset.py` — NOT invoked by the run-book
    - `code/data/classify_prs.py` — IS a run-book command
    - `code/data/fetch_github.py` — IS a run-book command
    - `code/audit/manual_validation.py` — IS a run-book command
    - `code/analysis/statistical_tests.py` — IS a run-book command
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/boxplots.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/visualizations.py` — IS a run-book command
  Make ONE of these WRITE `figures/boxplots.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/final_report.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/generate_final_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `figures/final_report.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `figures/histograms.pdf` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_final_report_pdf.py` — NOT invoked by the run-book
    - `code/analysis/visualizations.py` — IS a run-book command
  Make ONE of these WRITE `figures/histograms.pdf` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/prs_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/extract_metrics.py`, `code/data/save_metrics.py`, `code/analysis/statistical_tests.py`, `code/analysis/sensitivity_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/prs_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/extract_metrics.py`, `code/data/optimize_metrics_extraction.py`, `code/data/save_metrics.py`, `code/analysis/statistical_tests.py`, `code/analysis/generate_final_report_pdf.py`, `code/analysis/sensitivity_analysis.py`.
