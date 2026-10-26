# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…on **never**     creates synthetic data; any problem results in…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…on **never**     creates synthetic data; any problem results in…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py --mode full  --num_objects 10  --seed 42; python code/analysis/statistical_test.py --input data/logs/; python code/main.py --mode full --seed $RANDOM; 1 command(s) failed: python code/data_loader.py (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py -> rc=1
_head_call_error
    raise ValueError("Force download failed due to the above error.") from head_call_error
ValueError: Force download failed due to the above error.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py", line 208, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py", line 187, in main
    manifest_path = load_dragmesh_manifest()
                    ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py", line 151, in load_dragmesh_manifest
    return fetch_dragmesh_manifest(output_dir=output_path.parent)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py", line 110, in fetch_dragmesh_manifest
    raise FileNotFoundError(
FileNotFoundError: Repository not found: dragmesh/dragmesh-2

- python code/main.py --mode full  --num_objects 10  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/main.py': [Errno 2] No such file or directory

- python code/analysis/statistical_test.py --input data/logs/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/analysis/statistical_test.py': [Errno 2] No such file or directory

- python code/main.py --mode full --seed $RANDOM -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/main.py': [Errno 2] No such file or directory

## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
