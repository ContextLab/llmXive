# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion/generate_synthetic.py: function `generate_random_smiles` returns a bare RNG draw (line 57) — a reported value computed from no real input
- code/ingestion/generate_synthetic.py: function `select_random_solvent` returns a bare RNG draw (line 66) — a reported value computed from no real input
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…NIST TRC (or Zenodo) or generate a synthetic fallback. 2. **Featuriza…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…If the download fails, a synthetic  dataset is generated automatical…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…te the whole pipeline on synthetic data and assert successful co…”
- code/ingestion/fetch_nist.py: synthetic/fake INPUT data not authorized by the spec — “…script falls back to the synthetic data generator defined in ``c…”
- code/ingestion/fetch_nist.py: synthetic/fake INPUT data not authorized by the spec — “…whether to fall back to synthetic data.     """     # ``fetch_f…”
- code/ingestion/fetch_nist.py: synthetic/fake INPUT data not authorized by the spec — “…th) -> Path:     """     Generate a synthetic diffusion dataset using…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 33 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion/generate_synthetic.py: function `generate_random_smiles` returns a bare RNG draw (line 57) — a reported value computed from no real input; code/ingestion/generate_synthetic.py: function `select_random_solvent` returns a bare RNG draw (line 66) — a reported value computed from no real input; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…NIST TRC (or Zenodo) or generate a synthetic fallback. 2. **Featuriza…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/main.py --step featurize; python code/main.py --step train; python code/main.py --step evaluate; 1 command(s) failed: python -m pytest tests/contract/ -v (rc=2)

## Failing / missing run-book commands

- python code/main.py --step featurize -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-365-predicting-molecular-diffusion-coefficie/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-365-predicting-molecular-diffusion-coefficie/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step train -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-365-predicting-molecular-diffusion-coefficie/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-365-predicting-molecular-diffusion-coefficie/code/main.py': [Errno 2] No such file or directory

- python code/main.py --step evaluate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-365-predicting-molecular-diffusion-coefficie/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-365-predicting-molecular-diffusion-coefficie/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -v -> rc=2
=========
_________ ERROR collecting tests/contract/test_sensitivity_summary.py __________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-365-predicting-molecular-diffusion-coefficie/tests/contract/test_sensitivity_summary.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_sensitivity_summary.py:16: in <module>
    from training.generate_sensitivity_summary import generate_summary, STABILITY_THRESHOLD
E   ImportError: cannot import name 'STABILITY_THRESHOLD' from 'training.generate_sensitivity_summary' (/home/runner/work/llmXive/llmXive/projects/PROJ-365-predicting-molecular-diffusion-coefficie/code/training/generate_sensitivity_summary.py)
=========================== short test summary info ============================
ERROR tests/contract/test_sensitivity_summary.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.23s ===============================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
