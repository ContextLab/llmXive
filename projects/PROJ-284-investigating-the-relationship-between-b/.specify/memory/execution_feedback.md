# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/viz/network.py: function `load_node_coordinates` returns a bare RNG draw (line 37) — a reported value computed from no real input
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…) ) -> Path:     """     Generate a synthetic NIfTI file for CI valida…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…raise          # Create synthetic data - random noise with real…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…validation by generating synthetic data for a small subset.…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…="Run CI validation with synthetic data")          args = parser…”
- code/download/fetch_openneuro.py: synthetic/fake INPUT data not authorized by the spec — “…manifest, and we cannot mock data:     # We will attempt t…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…="running")     # Create synthetic test data for verification only (n…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…generator.     # It uses synthetic data to verify the logic, not…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/hcp_phenotypic.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 fabricated/simulated-result signal(s) — results are not real measurements: code/viz/network.py: function `load_node_coordinates` returns a bare RNG draw (line 37) — a reported value computed from no real input; code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…) ) -> Path:     """     Generate a synthetic NIfTI file for CI valida…”; code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…raise          # Create synthetic data - random noise with real…”; every produced artifact is gitignored (data/raw/hcp_phenotypic.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python code/download/fetch_openneuro.py --subjects 50 --output data/raw (rc=1); python code/download/fetch_hcp_behavioral.py --subjects 50 --output data/raw (rc=1); python code/preprocess/run_qc_only.py --input data/raw --output data/processed (rc=1); 8 declared deliverable(s) absent: data/analysis/aggregated_metrics.csv; data/analysis/factor_scores.csv; data/analysis/fdr_corrected_results.csv

## Failing / missing run-book commands

- python code/download/fetch_openneuro.py --subjects 50 --output data/raw -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/download/fetch_openneuro.py", line 22, in <module>
    from tqdm import tqdm
ModuleNotFoundError: No module named 'tqdm'
- python code/download/fetch_hcp_behavioral.py --subjects 50 --output data/raw -> rc=1
    Warning: Subject ID 50 does not look like a standard HCP ID.

/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/download/fetch_hcp_behavioral.py:96: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Error: Error tokenizing data. C error: Expected 1 fields in line 9, saw 2
- python code/preprocess/run_qc_only.py --input data/raw --output data/processed -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/preprocess/run_qc_only.py:25: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
- python code/main_pipeline.py --batch-size 5 --mode cpu -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/main_pipeline.py", line 17, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
- python code/viz/generate_report.py --input data/analysis/correlation_results.csv --output reports/summary.md -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-284-investigating-the-relationship-between-b/code/viz/generate_report.py:20: DeprecationWarning: 
Pyarrow will become a required dependency of pandas in the next major release of pandas (pandas 3.0),
(to allow more performant data types, such as the Arrow string type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
- python code/utils/checksums.py verify -> rc=1
    Checksum Verification Results:
==================================================
Total files checked: 1
Valid files: 0
Failed files: 1

Failed files:
  ✗ Checksums file missing: data/processed/checksums.json
==================================================
Checksum verification FAILED.

## Declared deliverables still missing

- data/analysis/aggregated_metrics.csv
- data/analysis/factor_scores.csv
- data/analysis/fdr_corrected_results.csv
- data/analysis/metrics_raw.csv
- data/analysis/pca_loadings.csv
- data/analysis/power_analysis.json
- data/analysis/qc_summary.csv
- data/analysis/subjects_included.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `generate_scatter_plot` — defined in `code/viz/scatter.py`; called 0 way(s):


Make `generate_scatter_plot` in `code/viz/scatter.py` accept ALL of the above.

### `get_logger` — defined in `code/logging_config.py`; called 25 way(s):

- code/main.py: logger = get_logger(__name__)
- code/logging_config.py: return get_logger().log(op, **kwargs)
- code/main_pipeline.py: logger = get_logger(__name__)
- code/main_pipeline.py: self.logger = get_logger(__name__)
- code/viz/network.py: logger = get_logger(__name__)
- code/viz/generate_report.py: logger = get_logger(__name__)
- code/viz/scatter.py: logger = get_logger(__name__)
- code/preprocess/run_qc_only.py: logger = get_logger(__name__)
- code/analysis/correlations.py: logger = get_logger(__name__)
- code/analysis/generate_full_metrics.py: logger = get_logger(__name__)
- code/analysis/create_full_metrics.py: logger = get_logger(__name__)
- code/analysis/pca_runner.py: logger = get_logger(__name__)
- code/analysis/power.py: logger = get_logger(__name__)
- code/analysis/correlation_main_runner.py: logger = get_logger(__name__)
- code/analysis/run_correlations.py: logger = get_logger(__name__)
- code/analysis/run_analysis.py: logger = get_logger(__name__)
- code/data/preprocess.py: logger = get_logger(__name__)
- code/data/metrics.py: logger = get_logger(__name__)
- code/data/download.py: logger = get_logger(__name__)
- code/tools/cleanup.py: self.logger = get_logger(__name__)
- code/tools/cleanup.py: logger = get_logger(__name__)
- code/tools/validate_quickstart.py: logger = get_logger(__name__)
- code/tools/refactor.py: self.logger = get_logger(__name__)
- code/tools/refactor.py: logger = get_logger(__name__)
- code/tools/verify_batching.py: logger = get_logger(__name__)

Make `get_logger` in `code/logging_config.py` accept ALL of the above.

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

- `data/analysis/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
    - `code/data/metrics.py` — NOT invoked by the run-book
    - `code/tools/verify_batching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/factor_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/factor_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/fdr_corrected_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/viz/network.py` — NOT invoked by the run-book
    - `code/viz/generate_report.py` — IS a run-book command
    - `code/viz/scatter.py` — NOT invoked by the run-book
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/fdr_corrected_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/pca_loadings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/pca_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/pca_loadings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/viz/generate_report.py` — IS a run-book command
    - `code/analysis/power.py` — NOT invoked by the run-book
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/qc_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess/run_qc_only.py` — IS a run-book command
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/qc_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/subjects_included.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/subjects_included.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/aggregated_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis/correlations.py`, `code/data/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/aggregated_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/correlations.py`, `code/analysis/create_full_metrics.py`, `code/analysis/pca_runner.py`, `code/data/metrics.py`, `code/tools/verify_batching.py`.
