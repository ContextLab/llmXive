# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…implementation relied on synthetic data generation, which was fl…”
- code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…o make it clear that     synthetic data generation is no longer…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation for social me…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xperiments.  This module generates controlled synthetic datasets for testing the…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…IMPORTANT: This module generates CONTROLLED synthetic data for testing purpose…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…iguration for generating synthetic game data."""     num_games: int =…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic game data for testing th…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…ction creates structured synthetic data that mimics the format…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -c "from data.loaders import verify_datasets; verify_datasets()"`
- `python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling`
- `python code/run_experiment.py --context full --agents 5 --games 100 --seed 42`
- `python code/run_experiment.py --context full --agents 5 --games 100 --seed 42`
- `python code/run_experiment.py --context full --agents 5 --games 1000`
- `python code/run_experiment.py --context limited --agents 5 --games 1000`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 fabricated/simulated-result signal(s) — results are not real measurements: code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…implementation relied on synthetic data generation, which was fl…”; code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…o make it clear that     synthetic data generation is no longer…”; code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generation for social me…”; 6 command(s) failed: python code/run_experiment.py --context full --agents 5 --games 1000 (rc=1); python code/run_experiment.py --context limited --agents 5 --games 1000 (rc=1); python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling (rc=1)

## Failing / missing run-book commands

- python code/run_experiment.py --context full --agents 5 --games 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)
- python code/run_experiment.py --context limited --agents 5 --games 1000 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)
- python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)
- python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)
- python -c "from data.loaders import verify_datasets; verify_datasets()" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/data/__init__.py", line 4, in <module>
    from .loaders import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/data/loaders.py", line 18, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/run_experiment.py --context full --agents 5 --games 100 --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)
- python code/run_experiment.py --context full --agents 5 --games 100 --seed 42 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/run_experiment.py", line 34, in <module>
    from generate_full_results import simulate_one_game, ensure_dir
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/generate_full_results.py", line 26, in <module>
    from utils.logging import get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/__init__.py", line 5, in <module>
    from .config import load_config, save_config
ImportError: cannot import name 'load_config' from 'utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/utils/config.py)

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `__getattr__` — defined in `code/memory/buffer.py`; called 0 way(s):


Make `__getattr__` in `code/memory/buffer.py` accept ALL of the above.

### `compute_retrieval_efficiency` — defined in `code/metrics/retrieval.py`; called 11 way(s):

- code/generate_full_results.py: retrieval_eff, _ = compute_retrieval_efficiency(
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

Make `compute_retrieval_efficiency` in `code/metrics/retrieval.py` accept ALL of the above.

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

`MemoryBuffer.reset` call sites (4):
- code/generate_full_results.py: agent.memory.reset()
- code/memory/buffer.py: buffer.reset()
- code/tests/unit/test_memory_buffer.py: """Test that reset() clears all entries."""
- code/tests/unit/test_memory_buffer.py: buffer.reset()
