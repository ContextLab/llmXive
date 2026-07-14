# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/t015_generate_full_results.py: self-declared fabricated metric — “…game state.     # This is NOT fake results; it is the INPUT data for th…”
- code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “….     Uses the project's synthetic fallback data (authorized by FR-011) t…”
- code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “…l_queries = 0          # Generate synthetic cues to test against the…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…"""Synthetic data generation utilities for…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ublication.  Per FR-011, synthetic data generation is a FALLBACK…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ication for generating a synthetic dataset."""     name: str     nu…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate a synthetic dataset for structural t…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…Specification for the synthetic dataset. If None, uses defaults.…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/t015_generate_full_results.py: self-declared fabricated metric — “…game state.     # This is NOT fake results; it is the INPUT data for th…”; code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “….     Uses the project's synthetic fallback data (authorized by FR-011) t…”; code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “…l_queries = 0          # Generate synthetic cues to test against the…”; 6 command(s) failed: python code/run_experiment.py --context full --agents 5 --games 1000 (rc=1); python code/run_experiment.py --context limited --agents 5 --games 1000 (rc=1); python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling (rc=1)

## Failing / missing run-book commands

- python code/run_experiment.py --context full --agents 5 --games 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)
- python code/run_experiment.py --context limited --agents 5 --games 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)
- python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)
- python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)
- python code/run_experiment.py --context full --agents 5 --games 100 --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)
- python code/run_experiment.py --context full --agents 5 --games 100 --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 23, in <module>
    from analysis.scaling import fit_power_law, generate_scaling_plot
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/__init__.py", line 5, in <module>
    from .anova import ANOVAOutput, load_experiment_results, prepare_data_for_anova, compute_two_way_anova, compute_manual_anova, apply_bonferroni_correction, run_anova_analysis, main
ImportError: cannot import name 'ANOVAOutput' from 'analysis.anova' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/analysis/anova.py)

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `__getattr__` — defined in `code/utils/logging.py`; called 0 way(s):


Make `__getattr__` in `code/utils/logging.py` accept ALL of the above.

### `compute_retrieval_efficiency` — defined in `code/metrics/retrieval.py`; called 18 way(s):

- code/run_experiment.py: ret_eff, _ = compute_retrieval_efficiency(
- code/t015_generate_full_results.py: ret_eff, ret_metrics = compute_retrieval_efficiency(
- code/metrics/retrieval.py: return compute_retrieval_efficiency(total_successful, total_queries, avg_agents)
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
- code/analysis/sensitivity.py: ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, agent_count)
- code/tests/unit/test_retrieval.py: metrics, eff = compute_retrieval_efficiency(5, 10, [0, 1, 2])
- code/tests/unit/test_retrieval.py: metrics, eff = compute_retrieval_efficiency(0, 0, 3)
- code/data/generate_scaling_data.py: ret_eff, _ = compute_retrieval_efficiency(total_retrieved, total_facts, agent_count)

Make `compute_retrieval_efficiency` in `code/metrics/retrieval.py` accept ALL of the above.

### `compute_specialization_index` — defined in `code/metrics/specialization.py`; called 12 way(s):

- code/run_experiment.py: spec_index, _ = compute_specialization_index(
- code/t015_generate_full_results.py: spec_index, spec_metrics = compute_specialization_index(agent_fact_counts, num_agents=config.num_agents)
- code/metrics/specialization.py: return compute_specialization_index(avg_counts, num_agents=max_len)
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index([])
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index(None)
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index(agent_facts)
- code/metrics/tests/test_specialization.py: index, metrics = compute_specialization_index(agent_facts, num_agents=5)
- code/analysis/sensitivity.py: spec_idx, _ = compute_specialization_index(facts_per_agent, num_agents=agent_count)
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index(agent_skills)
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index([])
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index(agents=agent_skills, num_agents=2)
- code/tests/unit/test_specialization.py: idx, metrics = compute_specialization_index(5, 10)
- code/data/generate_scaling_data.py: spec_index, _ = compute_specialization_index(agent_skills, num_agents=agent_count)

Make `compute_specialization_index` in `code/metrics/specialization.py` accept ALL of the above.

### `get_logger` — defined in `code/utils/logging.py`; called 13 way(s):

- code/run_full_pipeline_ci.py: logger = get_logger(__name__)
- code/run_experiment.py: logger = get_logger(__name__)
- code/output_full_results.py: logger = get_logger(__name__)
- code/t015_generate_full_results.py: logger = get_logger("T015_main")
- code/run_pipeline_profile.py: logger = get_logger(__name__)
- code/utils/logging.py: return get_logger().log(op, **kwargs)
- code/utils/tests/test_logging.py: logger = get_logger(name=logger_name)
- code/utils/tests/test_logging.py: logger2 = get_logger(name="existing_logger")
- code/analysis/power.py: logger = get_logger(__name__)
- code/analysis/sensitivity.py: logger = get_logger(__name__)
- code/tests/integration/test_ci_pipeline.py: logger = get_logger(__name__)
- code/tests/unit/test_logging.py: logger1 = get_logger(name="test1")
- code/tests/unit/test_logging.py: logger2 = get_logger(name="test2")

Make `get_logger` in `code/utils/logging.py` accept ALL of the above.

### `simulate_one_game` — defined in `code/generate_full_results.py`; called 4 way(s):

- code/run_experiment.py: result = simulate_one_game(config)
- code/output_full_results.py: spec_idx, ret_eff = simulate_one_game(
- code/t015_generate_full_results.py: result, _ = simulate_one_game(config)
- code/tests/unit/test_run_experiment.py: spec_metrics, ret_metrics, result = simulate_one_game(1, config)

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
- code/memory/buffer.py: _SHARED_BUFFER.reset()
- code/memory/tests/test_buffer.py: result = buf.reset()
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
