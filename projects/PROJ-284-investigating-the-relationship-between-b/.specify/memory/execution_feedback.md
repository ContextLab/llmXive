# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nput to output (assuming synthetic input is already 'corrected' f…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…original implementation generated synthetic NIfTI‑like data, which v…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…d without     generating synthetic NIfTI data.  The function simply ca…”
- code/viz/network.py: synthetic/fake INPUT data not authorized by the spec — “…d if available,     # or generate a synthetic one for demonstration.…”
- code/viz/network.py: synthetic/fake INPUT data not authorized by the spec — “…g synthetic.")         # Generate a synthetic connectivity matrix (400…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nput to output (assuming synthetic input is already 'corrected' f…”; code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…original implementation generated synthetic NIfTI‑like data, which v…”; code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…d without     generating synthetic NIfTI data.  The function simply ca…”; 1 command(s) failed: python code/main.py --step analyze (rc=1); 3 declared deliverable(s) absent: data/analysis/factor_scores.csv; data/analysis/full_metrics.csv; data/analysis/pca_loadings.csv

## Failing / missing run-book commands

- python code/main.py --step analyze -> rc=1
    

## Declared deliverables still missing

- data/analysis/factor_scores.csv
- data/analysis/full_metrics.csv
- data/analysis/pca_loadings.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `nilearn` to the project's `requirements.txt` and `pip install nilearn`.
- **Verified**: this loads **30** real records with fields: Unnamed: 0, Subject, Rest.Scan, MeanFD, NumFD_greater_than_0.20, rootMeanSquareFD, FDquartile.top1.4thFD., PercentFD_greater_than_0.20, MeanDVARS, MeanFD_Jenkinson, site, sibling_id, data_set, age, sex, handedness, full_2_iq, full_4_iq, viq, piq, iq_measure, tdc, adhd, adhd_inattentive, adhd_combined, adhd_subthreshold, diagnosis_using_cdis, notes, sess_1_anat_2, oppositional, cog_inatt, hyperac, anxious_shy, perfectionism, social_problems, psychosomatic, conn_adhd, restless_impulsive, emot_lability, conn_gi_tot, dsm_iv_inatt, dsm_iv_h_i, dsm_iv_tot, study, sess_1_rest_1, sess_1_rest_1_eyes, sess_1_rest_2, sess_1_rest_2_eyes, sess_1_rest_3, sess_1_rest_3_eyes, sess_1_rest_4, sess_1_rest_4_eyes, sess_1_rest_5, sess_1_rest_5_eyes, sess_1_rest_6, sess_1_rest_6_eyes, sess_1_anat_1, sess_1_which_anat, sess_2_rest_1, sess_2_rest_1_eyes, sess_2_rest_2, sess_2_rest_2_eyes, sess_2_anat_1, defacing_ok, defacing_notes.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os
from nilearn import datasets

bunch = datasets.fetch_adhd(
    data_dir=os.path.join(os.getenv("HOME"), "nilearn_data"),
    verbose=0,
)

records = len(bunch.phenotypic)
print(f"RECORDS={records}")

fields = list(bunch.phenotypic.columns)
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_logger` — defined in `code/logging_config.py`; called 17 way(s):

- code/logging_config.py: return get_logger().log(op, **kwargs)
- code/main.py: logger = get_logger(__name__)
- code/viz/network.py: logger = get_logger(__name__)
- code/viz/scatter.py: logger = get_logger(__name__)
- code/analysis/power.py: logger = get_logger(__name__)
- code/analysis/correlations.py: logger = get_logger(__name__)
- code/analysis/generate_full_metrics.py: logger = get_logger(__name__)
- code/analysis/create_full_metrics.py: logger = get_logger(__name__)
- code/report/generate.py: logger = get_logger(__name__)
- code/data/preprocess.py: logger = get_logger("data.preprocess")
- code/tools/verify_imports.py: self.logger = get_logger(__name__)
- code/tools/verify_imports.py: logger = get_logger(__name__)
- code/tools/refactor.py: self.logger = get_logger(__name__)
- code/tools/refactor.py: logger = get_logger(__name__)
- code/tools/cleanup.py: self.logger = get_logger(__name__)
- code/tools/cleanup.py: logger = get_logger(__name__)
- code/tools/validate_quickstart.py: logger = get_logger(__name__)

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

- `data/analysis/factor_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/generate_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/factor_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/full_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/viz/network.py` — NOT invoked by the run-book
    - `code/viz/scatter.py` — NOT invoked by the run-book
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/generate_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
    - `code/tools/verify_batching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/full_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/pca_loadings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/generate_full_metrics.py` — NOT invoked by the run-book
    - `code/analysis/create_full_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/pca_loadings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
