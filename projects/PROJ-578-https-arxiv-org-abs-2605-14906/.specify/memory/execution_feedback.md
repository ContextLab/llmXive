# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_memlens_demo.py: self-declared fabricated metric — “…a 2-core CPU with  no GPU, we simulate the benchmark logic using: 1. A tiny synthe…”
- code/run_memlens_demo.py: function `simulate_visual_ablation` returns a bare RNG draw (line 100) — a reported value computed from no real input
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…question dataset with 50 synthetic samples across the 5 core memory…”
- code/run_memlens_demo.py: synthetic/fake INPUT data not authorized by the spec — “…k logic using: 1. A tiny synthetic dataset (50 samples) representin…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/run_memlens_demo.py: self-declared fabricated metric — “…a 2-core CPU with  no GPU, we simulate the benchmark logic using: 1. A tiny synthe…”; code/run_memlens_demo.py: function `simulate_visual_ablation` returns a bare RNG draw (line 100) — a reported value computed from no real input; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…question dataset with 50 synthetic samples across the 5 core memory…”; 1 command(s) failed: python code/run_memlens_demo.py (rc=1)

## Failing / missing run-book commands

- python code/run_memlens_demo.py -> rc=1
    Starting MemLens CPU Adaptation Simulation...
Simulating 50 samples across 4 context lengths...
Simulating Visual Ablation Study...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-578-https-arxiv-org-abs-2605-14906/code/run_memlens_demo.py", line 257, in <module>
    run_simulation()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-578-https-arxiv-org-abs-2605-14906/code/run_memlens_demo.py", line 165, in run_simulation
    writer.writerows(results)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/csv.py", line 157, in writerows
    return self.writer.writerows(map(self._dict_to_list, rowdicts))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/csv.py", line 149, in _dict_to_list
    raise ValueError("dict contains fields not in fieldnames: "
ValueError: dict contains fields not in fieldnames: 'condition'
