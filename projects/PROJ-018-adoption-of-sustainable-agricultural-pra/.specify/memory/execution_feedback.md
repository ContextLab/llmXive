# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Synthetic data generator for the agricu…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"description": "Synthetic fallback dataset for agricultural survey"…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic agricultural survey data…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…None,     )      print(f"Synthetic dataset written to: {output_path…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…vey data or fall back to synthetic data.  This script now includ…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…ne:     """Create a tiny synthetic dataset with the required column…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…description="Download or generate synthetic survey data.")     parse…”
- code/01_download_data.py: synthetic/fake INPUT data not authorized by the spec — “…help="Force use of synthetic data (bypasses real download)…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/02_clean_data.py --input data/raw/survey_data.csv`
  - script usage: `02_clean_data.py [-h] [--synthetic]`
  - argparse error: `02_clean_data.py: error: unrecognized arguments: --input data/raw/survey_data.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Synthetic data generator for the agricu…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"description": "Synthetic fallback dataset for agricultural survey"…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic agricultural survey data…”; 5 command(s) failed: python code/01_download_data.py --synthetic (rc=1); python code/03_engineer_features.py (rc=1); python code/04_model_analysis.py (rc=1); 1 declared deliverable(s) absent: data/processed/cleaned_data.csv

## Failing / missing run-book commands

- python code/01_download_data.py --synthetic -> rc=1
    File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/01_download_data.py", line 56
    Very small synthetic generator – only used when real data cannot be fetched.
                                   ^
SyntaxError: invalid character '–' (U+2013)
- python code/03_engineer_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/03_engineer_features.py", line 36, in <module>
    @log_operation("load_cleaned_data")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/04_model_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 22, in <module>
    from evalues import evalue
ModuleNotFoundError: No module named 'evalues'
- python code/05_generate_report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/05_generate_report.py", line 37, in <module>
    @log_operation("load_cleaned_data")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/02_clean_data.py --input data/raw/survey_data.csv -> rc=2
    usage: 02_clean_data.py [-h] [--synthetic]
02_clean_data.py: error: unrecognized arguments: --input data/raw/survey_data.csv

## Declared deliverables still missing

- data/processed/cleaned_data.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_config` — defined in `code/config.py`; called 24 way(s):

- code/02_clean_data.py: cfg = get_config()
- code/config.py: _CONFIG = None  # force reload on next get_config()
- code/config.py: # may still provide defaults via ``get_config(key, default)``.
- code/config.py: - get_config()
- code/config.py: - get_config(key)
- code/config.py: - get_config(key, default)
- code/config.py: - get_config(key=..., default=...)
- code/config.py: - get_config(key='my_key')
- code/config.py: return _base_path() / get_config("data_path", "data")
- code/config.py: return _base_path() / get_config("raw_data_path", "data/raw")
- code/config.py: return _base_path() / get_config("processed_data_path", "data/processed")
- code/config.py: return _base_path() / get_config("results_path", "results")
- code/config.py: return _base_path() / get_config("figures_path", "figures")
- code/config.py: return _base_path() / get_config("modeling_log_path", "modeling_log.yaml")
- code/config.py: seed = get_config("random_seed", default)
- code/01_download_data.py: log_path=get_config("modeling_log_path", "modeling_log.yaml"),
- code/01_download_data.py: cfg = get_config()
- code/03_engineer_features.py: get_config("processed_data_path", "data/processed")
- code/03_engineer_features.py: explicit = get_config("practice_columns")
- code/03_engineer_features.py: proxies = get_config("proxy_variables", default_proxies)
- code/03_engineer_features.py: weights_cfg: Dict[str, float] = get_config("engagement_weights", {})
- code/03_engineer_features.py: related = get_config("convergent_constructs", [])
- code/03_engineer_features.py: results_dir = Path(get_config("results_path", "results"))
- code/03_engineer_features.py: out_dir = Path(get_config("processed_data_path", "data/processed"))

Make `get_config` in `code/config.py` accept ALL of the above.

### `log_operation` — defined in `code/logging_config.py`; called 25 way(s):

- code/05_generate_report.py: @log_operation("load_cleaned_data")
- code/05_generate_report.py: @log_operation("load_engineered_data")
- code/05_generate_report.py: @log_operation("load_model_results")
- code/05_generate_report.py: @log_operation("load_vif")
- code/05_generate_report.py: @log_operation("load_roc")
- code/05_generate_report.py: @log_operation("load_mediation_results")
- code/05_generate_report.py: @log_operation("load_validity_metrics")
- code/05_generate_report.py: @log_operation("generate_report")
- code/02_clean_data.py: # ``@log_operation`` decorator that currently returns a LogEntry.
- code/02_clean_data.py: log_operation(operation_name, **kwargs)
- code/02_clean_data.py: log_operation("pipeline_failure", error=str(exc))
- code/00_generate_synthetic_data.py: @log_operation
- code/logging_config.py: * As a decorator: ``@log_operation("my_op")`` wraps the function unchanged.
- code/logging_config.py: * As a direct call: ``log_operation("my_op", key=value)`` returns a LogEntry.
- code/01_download_data.py: @log_operation("download_real_data")
- code/01_download_data.py: @log_operation("generate_synthetic_fallback")
- code/01_download_data.py: @log_operation("validate_variables")
- code/01_download_data.py: @log_operation("main")
- code/04_model_analysis.py: @log_operation("load_engineered_data")
- code/04_model_analysis.py: @log_operation("prepare_design_matrix")
- code/04_model_analysis.py: @log_operation("fit_logistic_regression")
- code/04_model_analysis.py: @log_operation("save_regression_summary")
- code/04_model_analysis.py: @log_operation("calculate_vif")
- code/04_model_analysis.py: @log_operation("save_vif")
- code/04_model_analysis.py: @log_operation("apply_fdr_correction")

Make `log_operation` in `code/logging_config.py` accept ALL of the above.

### `update_log_section` — defined in `code/logging_config.py`; called 14 way(s):

- code/05_generate_report.py: update_log_section("report_generated", {"path": str(report_path)})
- code/02_clean_data.py: update_log_section(
- code/02_clean_data.py: update_log_section("power_analysis", power_entry)
- code/00_generate_synthetic_data.py: update_log_section(
- code/01_download_data.py: update_log_section(
- code/04_model_analysis.py: update_log_section("regression_summary_path", path=str(out_path))
- code/04_model_analysis.py: update_log_section("vif_path", path=str(out_path))
- code/04_model_analysis.py: update_log_section("fdr_path", path=str(out_path))
- code/04_model_analysis.py: update_log_section("roc_plot_path", path=str(fig_path))
- code/04_model_analysis.py: update_log_section("roc_metrics_path", path=str(out_path))
- code/04_model_analysis.py: update_log_section("mediation_analysis", **results)
- code/04_model_analysis.py: update_log_section("mediation_results_path", path=str(out_path))
- code/04_model_analysis.py: update_log_section("pipeline_complete", status="success")
- code/03_engineer_features.py: update_log_section("validity", status)

Make `update_log_section` in `code/logging_config.py` accept ALL of the above.

## ✅ KNOWN-GOOD REFERENCE — a fully tolerant logging module

`code/logging_config.py` keeps breaking across rounds because it mixes the stdlib `logging` module (whose `Logger.log(level, msg)` needs an INTEGER level and has no `to_json`) with a custom `LogEntry`. That hybrid can never satisfy all callers. Replace the contents of `code/logging_config.py` with the self-contained reference below — it ALREADY defines every symbol callers need (`get_logger`, `log_operation`, `ReproducibilityLogger`, `LogEntry`), returns a `LogEntry` (with `.to_json()`) from direct `log_operation(...)` calls, supports `@log_operation`, and resolves any `.info`/`.debug`/`.warning` via `__getattr__`. Do NOT reach for the stdlib `logging` module again. Adjust only if a call site listed above needs a field it lacks.

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

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_generate_report.py` — IS a run-book command
    - `code/02_clean_data.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/03_engineer_features.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `engineered_data.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[results_dir]`
- PRODUCER(s) to edit: `code/05_generate_report.py`, `code/config.py`, `code/04_model_analysis.py`, `code/03_engineer_features.py`
- CONSUMER(s) that read it: `code/05_generate_report.py`, `code/validate_quickstart.py`, `code/config.py`, `code/04_model_analysis.py`, `code/03_engineer_features.py`
  → Edit the producer so every required name [results_dir] is in `engineered_data.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_generate_report.py`, `code/02_clean_data.py`, `code/03_engineer_features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_generate_report.py`, `code/02_clean_data.py`, `code/validate_quickstart.py`, `code/03_engineer_features.py`.

### `data/processed/engineered_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_generate_report.py`, `code/config.py`, `code/04_model_analysis.py`, `code/03_engineer_features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/engineered_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_generate_report.py`, `code/validate_quickstart.py`, `code/config.py`, `code/04_model_analysis.py`, `code/03_engineer_features.py`.

### `data/raw/survey_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/code_00_generate_synthetic_data.py`, `code/02_clean_data.py`, `code/00_generate_synthetic_data.py`, `code/01_download_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/survey_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/code_00_generate_synthetic_data.py`, `code/02_clean_data.py`, `code/validate_quickstart.py`, `code/00_generate_synthetic_data.py`, `code/01_download_data.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_generate_report.py`, `code/02_clean_data.py`, `code/03_engineer_features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_generate_report.py`, `code/02_clean_data.py`, `code/validate_quickstart.py`, `code/03_engineer_features.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_generate_report.py`, `code/02_clean_data.py`, `code/03_engineer_features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_generate_report.py`, `code/02_clean_data.py`, `code/validate_quickstart.py`, `code/03_engineer_features.py`.
