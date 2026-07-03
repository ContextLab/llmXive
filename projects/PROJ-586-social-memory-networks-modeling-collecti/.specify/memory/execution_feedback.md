# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation for social me…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xperiments.  This module generates controlled synthetic datasets for testing the…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…IMPORTANT: This module generates CONTROLLED synthetic data for testing purpose…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…iguration for generating synthetic game data."""     num_games: int =…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic game data for testing th…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ction creates structured synthetic data that mimics the format…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Returns:         List of synthetic game records     """     random.seed(…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…00) -> None:     """     Generate all synthetic datasets needed for the…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 13 fabricated/simulated-result signal(s) — results are not real measurements: code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation for social me…”; code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xperiments.  This module generates controlled synthetic datasets for testing the…”; code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…IMPORTANT: This module generates CONTROLLED synthetic data for testing purpose…”; 1 command(s) failed: python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 (rc=2)

## Failing / missing run-book commands

- python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 -> rc=2
    usage: run_experiment.py [-h] [--context {full,limited}] [--agents AGENTS]
                         [--games GAMES] [--seed SEED]
                         [--output-dir OUTPUT_DIR] [--plot {scaling,None}]
run_experiment.py: error: unrecognized arguments: --thresholds 128,256,512

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `__getattr__` — defined in `code/utils/logging.py`; called 0 way(s):


Make `__getattr__` in `code/utils/logging.py` accept ALL of the above.

### `compute_retrieval_efficiency` — defined in `code/t015_generate_full_results.py`; called 20 way(s):

- code/run_experiment.py: ret_eff, ret_metrics = compute_retrieval_efficiency(result)
- code/t015_generate_full_results.py: 1. compute_retrieval_efficiency(retrieved, total, agents)
- code/t015_generate_full_results.py: 2. compute_retrieval_efficiency(agent_count, game_id) - legacy
- code/t015_generate_full_results.py: 3. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
- code/t015_generate_full_results.py: ret_metrics, ret_eff = compute_retrieval_efficiency(
- code/metrics/retrieval.py: 1. compute_retrieval_efficiency(retrieved, total, agents) - positional
- code/metrics/retrieval.py: 2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
- code/metrics/retrieval.py: 3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)
- code/metrics/tests/test_retrieval.py: metrics, efficiency = compute_retrieval_efficiency(10, 10, 3)
- code/metrics/tests/test_retrieval.py: metrics, efficiency = compute_retrieval_efficiency(1, 3, 3)
- code/metrics/tests/test_retrieval.py: metrics, efficiency = compute_retrieval_efficiency(0, 10, 3)
- code/metrics/tests/test_retrieval.py: metrics, efficiency = compute_retrieval_efficiency(9, 10, 3)
- code/metrics/tests/test_retrieval.py: metrics, _ = compute_retrieval_efficiency(5, 10, 5)
- code/metrics/tests/test_retrieval.py: metrics, _ = compute_retrieval_efficiency(5, 10, 3)
- code/metrics/tests/test_retrieval.py: compute_retrieval_efficiency(5, 10, -1)
- code/metrics/tests/test_retrieval.py: compute_retrieval_efficiency(5, -1, 3)
- code/metrics/tests/test_retrieval.py: compute_retrieval_efficiency(-1, 10, 3)
- code/metrics/tests/test_retrieval.py: compute_retrieval_efficiency(15, 10, 3)
- code/tests/unit/test_retrieval.py: metrics, eff = compute_retrieval_efficiency(5, 10, [0, 1, 2])
- code/tests/unit/test_retrieval.py: metrics, eff = compute_retrieval_efficiency(0, 0, 3)

Make `compute_retrieval_efficiency` in `code/t015_generate_full_results.py` accept ALL of the above.

### `compute_specialization_index` — defined in `code/t015_generate_full_results.py`; called 14 way(s):

- code/run_experiment.py: spec_idx, spec_metrics = compute_specialization_index(result)
- code/t015_generate_full_results.py: 1. compute_specialization_index(agent_list) - agent_list is a list
- code/t015_generate_full_results.py: 2. compute_specialization_index(agent_list, num_agents=N)
- code/t015_generate_full_results.py: 3. compute_specialization_index(agent_count, game_id) - legacy
- code/t015_generate_full_results.py: 4. compute_specialization_index(agents=..., num_agents=...) - keyword
- code/t015_generate_full_results.py: spec_idx, _ = compute_specialization_index(assignments, num_agents=agent_count)
- code/metrics/specialization.py: 1. compute_specialization_index(agent_list) - list of agent skills
- code/metrics/specialization.py: 2. compute_specialization_index(agent_list, num_agents=N) - with explicit count
- code/metrics/specialization.py: 3. compute_specialization_index(agents=..., num_agents=...) - keyword style
- code/metrics/specialization.py: 4. compute_specialization_index(agent_count, game_id) - legacy (uses agent_count as list length)
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index([])
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index(game_results)
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index([1, 2, 2, 3], num_agents=4)
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index([], num_agents=0)

Make `compute_specialization_index` in `code/t015_generate_full_results.py` accept ALL of the above.

### `get_logger` — defined in `code/utils/logging.py`; called 11 way(s):

- code/run_experiment.py: logger = get_logger(__name__)
- code/output_full_results.py: logger = get_logger(__name__)
- code/t015_generate_full_results.py: logger = get_logger(__name__)
- code/run_pipeline_profile.py: logger = get_logger(__name__)
- code/utils/logging.py: return get_logger().log(op, **kwargs)
- code/utils/tests/test_logging.py: logger = get_logger(name=logger_name)
- code/utils/tests/test_logging.py: logger2 = get_logger(name="existing_logger")
- code/analysis/anova.py: logger = get_logger(__name__)
- code/analysis/sensitivity.py: logger = get_logger(__name__)
- code/tests/unit/test_logging.py: logger1 = get_logger(name="test1")
- code/tests/unit/test_logging.py: logger2 = get_logger(name="test2")

Make `get_logger` in `code/utils/logging.py` accept ALL of the above.

### `simulate_one_game` — defined in `code/generate_full_results.py`; called 12 way(s):

- code/generate_full_results.py: 1. simulate_one_game(agent_count: int, game_id: int, context: str)
- code/generate_full_results.py: 2. simulate_one_game(agent_list: List[int], game_id: int)
- code/generate_full_results.py: 3. simulate_one_game(agents, game_id) - legacy positional
- code/run_experiment.py: result = simulate_one_game(agent_count, game_id, context_condition)
- code/output_full_results.py: spec_idx, ret_eff = simulate_one_game(
- code/run_scaling_experiment.py: result = simulate_one_game(agents, game_id)
- code/t015_generate_full_results.py: 1. simulate_one_game(agent_count, game_id, context) - primary
- code/t015_generate_full_results.py: 2. simulate_one_game(agent_list, game_id) - legacy
- code/t015_generate_full_results.py: 3. simulate_one_game(agents, game_id) - legacy positional
- code/t015_generate_full_results.py: result = simulate_one_game(
- code/analysis/sensitivity.py: result = simulate_one_game(
- code/analysis/sensitivity.py: result = simulate_one_game(agents, game_id)

Make `simulate_one_game` in `code/generate_full_results.py` accept ALL of the above.

### class `MemoryBuffer` (in `code/memory/buffer.py`) — accessed via method/attribute names this round: `reset`

`MemoryBuffer` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/memory/buffer.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `MemoryBuffer` across the codebase must stop raising `AttributeError`/`TypeError`.

`MemoryBuffer.reset` call sites (3):
- code/memory/tests/test_buffer.py: buf.reset()
- code/memory/tests/test_buffer.py: buf1.reset()
- code/tests/unit/test_memory_buffer.py: buf.reset()  # should not raise

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
