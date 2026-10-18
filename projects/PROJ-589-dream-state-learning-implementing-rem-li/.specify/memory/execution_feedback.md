# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…model.to(device)      # Dummy data loader – 10 batches of r…”; 2 command(s) failed: python code/train.py --seed 42 --steps 10 --mode debug (rc=1); python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 (rc=1)

## Failing / missing run-book commands

- python code/train.py --seed 42 --steps 10 --mode debug -> rc=1
 = Trainer(model=model, config=config, device=device)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/models/trainer.py", line 113, in __init__
    self.memory_monitor = MemoryMonitor(config, self.logger)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/utils/memory_monitor.py", line 61, in __init__
    self.checkpoint_dir = Path(checkpoint_dir)
                          ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not Logger

- python code/train.py --seeds 0,1,2,3,4 --ratio 4:1 --warmup 20 -> rc=1
 = Trainer(model=model, config=config, device=device)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/models/trainer.py", line 113, in __init__
    self.memory_monitor = MemoryMonitor(config, self.logger)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-589-dream-state-learning-implementing-rem-li/code/utils/memory_monitor.py", line 61, in __init__
    self.checkpoint_dir = Path(checkpoint_dir)
                          ^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 871, in __new__
    self = cls._from_parts(args)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 509, in _from_parts
    drv, root, parts = self._parse_args(args)
                       ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 493, in _parse_args
    a = os.fspath(a)
        ^^^^^^^^^^^^
TypeError: expected str, bytes or os.PathLike object, not Logger

