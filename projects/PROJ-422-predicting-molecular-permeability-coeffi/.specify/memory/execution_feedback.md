# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/train.py: synthetic/fake INPUT data not authorized by the spec — “…Data]:         """Create dummy graph data objects from feature vec…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/train.py: synthetic/fake INPUT data not authorized by the spec — “…Data]:         """Create dummy graph data objects from feature vec…”; 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 2 command(s) failed: python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1); 2 declared deliverable(s) absent: data/processed/processed_data.csv; data/raw/checksums.json

## Failing / missing run-book commands

- python code/analysis/train.py --config config.yaml -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py", line 27, in <module>
    from models.gnn import MPNN, create_mpnn_model, train_epoch, validate_epoch
ImportError: cannot import name 'create_mpnn_model' from 'models.gnn' (/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models/gnn.py)

- python code/analysis/explain.py -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/explain.py", line 22, in <module>
    from models.gnn import MPNN, create_mpnn_model
ImportError: cannot import name 'create_mpnn_model' from 'models.gnn' (/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models/gnn.py)

- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file

## Declared deliverables still missing

- data/processed/processed_data.csv
- data/raw/checksums.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/processed_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/split.py` — NOT invoked by the run-book
    - `code/models/gnn.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
