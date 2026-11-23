# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 (rc=1); python code/pipelines/run_conditioned.py --seed --epochs 15 (rc=1); python code/pipelines/run_analysis.py (rc=1); 7 declared deliverable(s) absent: data/artifacts/data_availability_gap_report.json; data/artifacts/data_integrity_report.json; data/artifacts/gpu_tuned_baselines.csv

## Failing / missing run-book commands

- python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_baseline.py", line 29, in <module>
    from utils.memory_monitor import MemoryMonitor, get_process_memory_mb
ImportError: cannot import name 'MemoryMonitor' from 'utils.memory_monitor' (/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/utils/memory_monitor.py)
- python code/pipelines/run_conditioned.py --seed --epochs 15 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_conditioned.py", line 8, in <module>
    from models.trainer import create_trainer, Trainer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/__init__.py", line 12, in <module>
    from models.projection import MLPProjection, AttentionProjection, GatedProjection, create_projection_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/projection.py", line 18, in <module>
    class MLPProjection(ProjectionModel):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/projection.py", line 31, in MLPProjection
    hidden_dims: Optional[List[int]] = None,
                          ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?
- python code/pipelines/run_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_analysis.py", line 151, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_analysis.py", line 146, in main
    success = run_pipeline(args)
              ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_analysis.py", line 37, in run_pipeline
    log_info(logger, "Starting full statistical analysis pipeline")
TypeError: log_info() takes 1 positional argument but 2 were given

## Declared deliverables still missing

- data/artifacts/data_availability_gap_report.json
- data/artifacts/data_integrity_report.json
- data/artifacts/gpu_tuned_baselines.csv
- data/artifacts/gpu_tuned_scalars.json
- data/artifacts/runtime_report.json
- data/processed/metadata_stats_summary.csv
- data/processed/normalized_tabular_features.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_info` — defined in `code/utils/logging.py`; called 25 way(s):

- code/data_loader.py: log_info(logger, f"Checksum verified successfully for {file_path}")
- code/data_loader.py: log_info(logger, f"Downloading {url} to {dest_path} (Attempt {attempt}/{MAX_RETRIES})")
- code/data_loader.py: log_info(logger, f"Download completed successfully: {dest_path}")
- code/data_loader.py: log_info(logger, f"Dataset found locally: {dataset_path}")
- code/data_loader.py: log_info(logger, f"Dataset downloaded: {dataset_path}")
- code/data_loader.py: log_info(logger, f"Dataset {dataset_name} ingested without checksum verification.")
- code/data_loader.py: log_info(logger, f"Starting data ingestion for {dataset_name}")
- code/embeddings/generator.py: log_info(f"Initializing EmbeddingGenerator on {device}")
- code/embeddings/generator.py: log_info("Models already loaded.")
- code/embeddings/generator.py: log_info("Loading CLIP ViT-B/32 image encoder...")
- code/embeddings/generator.py: log_info("CLIP image encoder loaded successfully.")
- code/embeddings/generator.py: log_info("Loading Sentence-BERT text encoder...")
- code/embeddings/generator.py: log_info("Sentence-BERT text encoder loaded successfully.")
- code/embeddings/generator.py: log_info(f"Processing {total} images for embeddings...")
- code/embeddings/generator.py: log_info(f"Processing {total} text samples for embeddings...")
- code/embeddings/edge_case_handler.py: log_info(f"Dropping {len(zero_var_cols)} zero-variance columns: {zero_var_cols}")
- code/embeddings/edge_case_handler.py: log_info(f"Imputing {len(zero_var_cols)} zero-variance columns with constant {constant_value}")
- code/embeddings/edge_case_handler.py: log_info("Imputing missing fields with constant values.")
- code/embeddings/serializer.py: log_info(f"Created empty Parquet file at {output_path}")
- code/embeddings/serializer.py: log_info(f"Successfully serialized {len(rows)} embeddings to {output_path}")
- code/embeddings/serializer.py: log_info(f"Output schema: {df.dtypes.to_dict()}")
- code/embeddings/serializer.py: log_info(f"Sample row: {df.iloc[0].to_dict()}")
- code/embeddings/serializer.py: log_info(f"Loaded {len(embeddings)} embeddings from {input_path}")
- code/embeddings/utils.py: log_info(f"Starting batch processing: {total_items} items, batch size {batch_size}, {num_batches} batches")
- code/embeddings/utils.py: log_info(f"Batch processing complete. Final shape: {final_array.shape}")

Make `log_info` in `code/utils/logging.py` accept ALL of the above.

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

- `data/artifacts/data_availability_gap_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/run_fdr_correction.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/data_availability_gap_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/data_integrity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/run_fdr_correction.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/data_integrity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/gpu_tuned_baselines.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/extract_baseline_scalars.py` — NOT invoked by the run-book
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/run_t_test.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
    - `code/pipelines/run_analysis.py` — IS a run-book command
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/gpu_tuned_baselines.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/gpu_tuned_scalars.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/extract_baseline_scalars.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/final_statistical_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/gpu_tuned_scalars.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/runtime_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/run_optimized_pipeline.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/runtime_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata_stats_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/aggregate_metadata_stats.py` — NOT invoked by the run-book
    - `code/pipelines/run_correlation_analysis.py` — NOT invoked by the run-book
    - `code/pipelines/aggregate_metadata_subset.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/run_analysis.py` — IS a run-book command
    - `code/pipelines/run_integration_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata_stats_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/normalized_tabular_features.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/normalize_tabular.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/normalized_tabular_features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
