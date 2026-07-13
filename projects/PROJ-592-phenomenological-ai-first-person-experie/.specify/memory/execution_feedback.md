# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/stats.py: synthetic/fake INPUT data not authorized by the spec — “…enerate a minimal set of synthetic data to ensure the pipeline r…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --task generate_control --config code/config.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/stats.py: synthetic/fake INPUT data not authorized by the spec — “…enerate a minimal set of synthetic data to ensure the pipeline r…”; 7 command(s) failed: python code/main.py --task generate --config code/config.py (rc=1); python code/main.py --task generate_control --config code/config.py (rc=1); python code/main.py --task select_validation_sample --config code/config.py (rc=2); 1 declared deliverable(s) absent: data/processed/validity_scores.csv

## Failing / missing run-book commands

- python code/main.py --task generate --config code/config.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 115, in main
    run_generation_phase(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 38, in run_generation_phase
    run_generation_pipeline(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/generation/runner.py", line 138, in run_generation_pipeline
    model_path = config["model_path"]
                 ~~~~~~^^^^^^^^^^^^^^
KeyError: 'model_path'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py --task generate_control --config code/config.py -> rc=1
    odule_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1211, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1168, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'arxiv_nlp' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py --task select_validation_sample --config code/config.py -> rc=2
    usage: main.py [-h] --task
               {generate,generate_control,analyze,stats,validate_human,sensitivity-kappa,archive,full}
               [--config CONFIG]
main.py: error: argument --task: invalid choice: 'select_validation_sample' (choose from 'generate', 'generate_control', 'analyze', 'stats', 'validate_human', 'sensitivity-kappa', 'archive', 'full')
- python code/main.py --task analyze -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 119, in main
    run_analysis_phase(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 50, in run_analysis_phase
    run_consistency_analysis(config)
TypeError: run_consistency_analysis() missing 1 required positional argument: 'output_path'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py --task validate_human -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 123, in main
    run_validation_phase(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 64, in run_validation_phase
    run_stratified_sampling(config)
TypeError: run_stratified_sampling() missing 1 required positional argument: 'output_file'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py --task stats -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 121, in main
    run_stats_phase(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 58, in run_stats_phase
    orchestrate_analysis(config)
TypeError: orchestrate_analysis() takes 0 positional arguments but 1 was given

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py --task sensitivity-kappa -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 126, in main
    run_sensitivity_kappa_analysis(config)
TypeError: run_sensitivity_kappa_analysis() missing 1 required positional argument: 'output_file'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 141, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-592-phenomenological-ai-first-person-experie/code/main.py", line 136, in main
    logger.error(f"Pipeline failed: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'

## Declared deliverables still missing

- data/processed/validity_scores.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_operation` — defined in `code/utils/logging.py`; called 18 way(s):

- code/main.py: log_operation("setup_environment", config_path=config_path)
- code/main.py: log_operation("run_generation_phase")
- code/main.py: log_operation("run_control_phase")
- code/main.py: log_operation("run_analysis_phase")
- code/main.py: log_operation("run_stats_phase")
- code/main.py: log_operation("run_validation_phase")
- code/main.py: log_operation("run_full_pipeline")
- code/main.py: log_operation("full_pipeline_complete")
- code/main.py: log_operation("main_start", task=args.task, config=args.config)
- code/main.py: log_operation("task_complete", task=args.task)
- code/main.py: log_operation("task_failed", task=args.task, error=str(e))
- code/utils/logging.py: """Dual-purpose: a decorator (@log_operation) OR a direct logging call.
- code/analysis/stats.py: log_operation("orchestrate_analysis_start")
- code/analysis/stats.py: log_operation("orchestrate_analysis_complete", output=str(output_path))
- code/analysis/stats.py: log_operation("stats_main_start")
- code/generation/runner.py: log_operation("generate_sample_attempt", strategy=strategy, seed=seed)
- code/generation/runner.py: log_operation("run_generation_phase", config_path=str(config_path))
- code/generation/runner.py: log_operation("generation_complete", total_samples=len(all_samples))

Make `log_operation` in `code/utils/logging.py` accept ALL of the above.

### `orchestrate_analysis` — defined in `code/analysis/stats.py`; called 2 way(s):

- code/main.py: orchestrate_analysis(config)
- code/analysis/stats.py: results = orchestrate_analysis()

Make `orchestrate_analysis` in `code/analysis/stats.py` accept ALL of the above.

### `retry_on_failure` — defined in `code/utils/logging.py`; called 4 way(s):

- code/validation/turing_simulation.py: @retry_on_failure(max_attempts=3, delay_seconds=1.0)
- code/generation/runner_local.py: @retry_on_failure(max_attempts=3, delay=5)
- code/generation/runner.py: @retry_on_failure(max_attempts=MAX_ATTEMPTS_PER_SAMPLE, delay=2.0, logger=logger)
- code/generation/control_corpus.py: @retry_on_failure(max_attempts=3, delay=2.0, logger=logger)

Make `retry_on_failure` in `code/utils/logging.py` accept ALL of the above.

### `run_consistency_analysis` — defined in `code/analysis/consistency.py`; called 2 way(s):

- code/main.py: run_consistency_analysis(config)
- code/analysis/consistency.py: run_consistency_analysis(args.input, args.output, args.model)

Make `run_consistency_analysis` in `code/analysis/consistency.py` accept ALL of the above.

### `run_sensitivity_kappa_analysis` — defined in `code/analysis/sensitivity_kappa.py`; called 2 way(s):

- code/main.py: run_sensitivity_kappa_analysis(config)
- code/analysis/sensitivity_kappa.py: results = run_sensitivity_kappa_analysis(

Make `run_sensitivity_kappa_analysis` in `code/analysis/sensitivity_kappa.py` accept ALL of the above.

### `run_stratified_sampling` — defined in `code/validation/stratified_sampler.py`; called 2 way(s):

- code/main.py: run_stratified_sampling(config)
- code/validation/stratified_sampler.py: run_stratified_sampling(

Make `run_stratified_sampling` in `code/validation/stratified_sampler.py` accept ALL of the above.

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

- `data/processed/validity_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/validity_justification.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/validation/stratified_sampler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validity_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/prompts/base_prompts.json`

- ACTUAL columns/keys the producer wrote: `[id, prompt]`
- REQUIRED by the consumer(s): `[model_path]`
- MISSING (required but not written): `['model_path']`
- PRODUCER(s) to edit: `code/generation/runner.py`, `code/generation/prompt_engineering.py`
- CONSUMER(s) that read it: `code/generation/runner_local.py`, `code/generation/runner.py`, `code/generation/prompt_engineering.py`
  → Edit the producer so every required name [model_path] is in `data/prompts/base_prompts.json`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
