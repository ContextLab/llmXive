# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Developmen…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…back (T005)  This module generates synthetic survey data conforming t…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…able.  NOTE: This script generates synthetic data ONLY when real data…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, Any]:     """     Generate a single synthetic respondent record confor…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate the full synthetic dataset conforming to da…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…Pandas DataFrame with synthetic survey data     """     rng = random…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…n() -> None:     """     Generate and save synthetic data (FALLBACK ONLY).…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…_data.csv containing     synthetic records conforming to the projec…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 30 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Developmen…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…back (T005)  This module generates synthetic survey data conforming t…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…able.  NOTE: This script generates synthetic data ONLY when real data…”; 6 command(s) failed: python code/01_download_data.py --synthetic (rc=1); python code/02_clean_data.py (rc=1); python code/03_engineer_features.py (rc=1); 1 declared deliverable(s) absent: data/processed/cleaned_data.csv

## Failing / missing run-book commands

- python code/01_download_data.py --synthetic -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/01_download_data.py", line 298, in <module>
    @log_operation("data_acquisition_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/02_clean_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 66, in <module>
    @log_operation("load_config")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/03_engineer_features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/03_engineer_features.py", line 397, in <module>
    @log_operation("feature_engineering_main")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable
- python code/04_model_analysis.py -> rc=1
    ERROR:root:Model analysis failed: Engineered data not found at data/processed/engineered_data.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 340, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/logging_config.py", line 71, in _wrapper
    return func(*a, **k)
           ^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 279, in main
    df = load_engineered_data(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/04_model_analysis.py", line 54, in load_engineered_data
    raise CustomDataError(f"Engineered data not found at {path}")
CustomDataError: Engineered data not found at data/processed/engineered_data.csv
- python code/05_generate_report.py -> rc=1
    WARNING: reportlab not installed. PDF generation will fail.
Install with: pip install reportlab
Starting report generation...
ERROR: Cleaned data not found at data/processed/cleaned_data.csv
- python code/02_clean_data.py --input data/raw/survey_data.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/code/02_clean_data.py", line 66, in <module>
    @log_operation("load_config")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'LogEntry' object is not callable

## Declared deliverables still missing

- data/processed/cleaned_data.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_config` — defined in `code/config.py`; called 25 way(s):

- code/02_clean_data.py: return get_config()
- code/02_clean_data.py: config = get_config()
- code/config.py: 1. get_config() -> Returns the full Config object
- code/config.py: 2. get_config("key") -> Returns the value for "key" from config
- code/config.py: 3. get_config("key", default) -> Returns the value for "key" or default
- code/config.py: base = get_config("project_root", ".")
- code/config.py: return Path(base) / get_config("data_path", default)
- code/config.py: return Path(base) / get_config("raw_data_path", default)
- code/config.py: return Path(base) / get_config("processed_data_path", default)
- code/config.py: return Path(base) / get_config("results_path", default)
- code/config.py: return Path(base) / get_config("modeling_log_path", default)
- code/03_engineer_features.py: base_dir = Path(get_config("project_root", "."))
- code/03_engineer_features.py: processed_dir = base_dir / get_config("processed_data_path", "data/processed")
- code/03_engineer_features.py: results_dir = base_dir / get_config("results_path", "results")
- code/03_engineer_features.py: log_path = base_dir / get_config("modeling_log_path", "modeling_log.yaml")
- code/03_engineer_features.py: config = get_config()
- code/03_engineer_features.py: log_path=str(Path(get_config("project_root", ".")) / get_config("modeling_log_path", "modeling_log.yaml"))
- code/logging_config.py: base = get_config("project_root", ".")
- code/logging_config.py: log_path = str(Path(base) / get_config("modeling_log_path", "modeling_log.yaml"))
- code/06_finalize_results.py: config = get_config()
- code/05_generate_report.py: config = get_config()
- code/00_generate_synthetic_data.py: config_path = Path(get_config("config_path", "code/config.yaml"))
- code/00_generate_synthetic_data.py: log_path = Path(get_config("modeling_log_path", "modeling_log.yaml"))
- code/validate_quickstart.py: config = get_config()
- code/01_download_data.py: self.config = config or get_config()

Make `get_config` in `code/config.py` accept ALL of the above.

### `log_operation` — defined in `code/logging_config.py`; called 15 way(s):

- code/02_clean_data.py: @log_operation("load_config")
- code/02_clean_data.py: @log_operation("load_raw_data")
- code/02_clean_data.py: @log_operation("validate_variables")
- code/02_clean_data.py: @log_operation("calculate_missingness")
- code/02_clean_data.py: @log_operation("handle_missing_values")
- code/02_clean_data.py: @log_operation("normalize_categorical_codes")
- code/02_clean_data.py: @log_operation("calculate_power_analysis")
- code/02_clean_data.py: @log_operation("update_modeling_log_with_power_analysis")
- code/02_clean_data.py: @log_operation("export_cleaned_data")
- code/02_clean_data.py: @log_operation("data_cleaning_pipeline")
- code/03_engineer_features.py: @log_operation("feature_engineering_main")
- code/logging_config.py: """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
- code/00_generate_synthetic_data.py: @log_operation("synthetic_data_generation_main")
- code/01_download_data.py: @log_operation("data_acquisition_main")
- code/04_model_analysis.py: @log_operation

Make `log_operation` in `code/logging_config.py` accept ALL of the above.

### `update_log_section` — defined in `code/logging_config.py`; called 8 way(s):

- code/02_clean_data.py: update_log_section("power_analysis", power_result, log_path=log_path)
- code/02_clean_data.py: update_log_section("data_validation", validation_result, log_path=log_path)
- code/02_clean_data.py: update_log_section("initial_missingness", missingness.to_dict(), log_path=log_path)
- code/02_clean_data.py: update_log_section("data_cleaning", {
- code/03_engineer_features.py: update_log_section("feature_engineering", log_data, log_path=str(log_path))
- code/03_engineer_features.py: update_log_section(
- code/00_generate_synthetic_data.py: update_log_section("data_source_metadata", log_data, log_path=log_path)
- code/04_model_analysis.py: update_log_section("model_analysis", {

Make `update_log_section` in `code/logging_config.py` accept ALL of the above.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (25):
- code/02_clean_data.py: base_dir = Path(config.get("project_root", "."))
- code/02_clean_data.py: raw_dir = base_dir / config.get("raw_data_path", "data/raw")
- code/02_clean_data.py: return mapping.get(x, x)
- code/02_clean_data.py: log_path = str(base_dir / config.get("modeling_log_path", "modeling_log.yaml"))
- code/02_clean_data.py: proc_dir = base_dir / config.get("processed_data_path", "data/processed")
- code/code_00_generate_synthetic_data.py: random.seed(config.get("random_seed", 42))
- code/code_00_generate_synthetic_data.py: n = config.get("n_respondents", 1000)
- code/config.py: return self._config.get(key, default)
- code/config.py: # Tolerant for any other method call (e.g., .info(), .debug(), .get() called on Config object directly)
- code/config.py: return _GLOBAL_CONFIG.get(key, default)
- code/03_engineer_features.py: priority_proxies = config.get("proxy_variables", [
- code/03_engineer_features.py: weights = config.get("engagement_weights", {})
- code/03_engineer_features.py: w = weights.get(col, 1.0)
- code/03_engineer_features.py: conv_status = "passed" if metrics.get('convergent_validity', {}).get('passed', False) else "failed"
- code/logging_config.py: self.name = args[0] if args else kwargs.get("name", "reproducibility")
- code/logging_config.py: op = args[0] if args else kwargs.get("operation", "")
- code/06_finalize_results.py: "random_seed": config.get("random_seed"),
- code/06_finalize_results.py: "data_source": config.get("data_source", "unknown"),
- code/06_finalize_results.py: "seed_value": config.get("random_seed"),
- code/06_finalize_results.py: set_random_seed(config.get("random_seed", 42))
- code/06_finalize_results.py: project_root = Path(config.get("project_root", "."))
- code/05_generate_report.py: base_dir = Path(config.get("project_root", "."))
- code/05_generate_report.py: processed_path = base_dir / config.get("processed_data_path", "data/processed")
- code/05_generate_report.py: results_path = base_dir / config.get("results_path", "results")
- code/05_generate_report.py: reg_data = results.get("regression", {})

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
    - `code/02_clean_data.py` — IS a run-book command
    - `code/03_engineer_features.py` — IS a run-book command
    - `code/06_finalize_results.py` — NOT invoked by the run-book
    - `code/05_generate_report.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `engineered_data.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[results_dir]`
- PRODUCER(s) to edit: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/04_model_analysis.py`
- CONSUMER(s) that read it: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`, `code/04_model_analysis.py`
  → Edit the producer so every required name [results_dir] is in `engineered_data.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).

### `data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.

### `data/processed/engineered_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/04_model_analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/engineered_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`, `code/04_model_analysis.py`.

### `data/raw/survey_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/code_00_generate_synthetic_data.py`, `code/00_generate_synthetic_data.py`, `code/01_download_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/survey_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/code_00_generate_synthetic_data.py`, `code/00_generate_synthetic_data.py`, `code/validate_quickstart.py`, `code/01_download_data.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/data/processed/cleaned_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-018-adoption-of-sustainable-agricultural-pra/data/processed/cleaned_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/02_clean_data.py`, `code/03_engineer_features.py`, `code/06_finalize_results.py`, `code/05_generate_report.py`, `code/validate_quickstart.py`.
