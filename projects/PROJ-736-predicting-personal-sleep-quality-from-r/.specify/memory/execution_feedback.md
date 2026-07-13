# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ource.     Falls back to simulated data if the real source is un…”
- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…a ({e}). Falling back to simulated data for pipeline execution."…”
- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ution.")         # Write simulated data to file to ensure the pi…”
- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Wrote simulated behavioral data to {output_path}")…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data/download_hcp.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ource.     Falls back to simulated data if the real source is un…”; code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…a ({e}). Falling back to simulated data for pipeline execution."…”; code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ution.")         # Write simulated data to file to ensure the pi…”; 2 command(s) failed: python code/data/download_hcp.py (rc=1); python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/predictions.npy

## Failing / missing run-book commands

- python code/data/download_hcp.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/download_hcp.py", line 213, in <module>
    sys.exit(0 if main() else 1)
                  ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/download_hcp.py", line 178, in main
    ensure_dirs()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/config.py", line 42, in ensure_dirs
    path.mkdir(parents=True, exist_ok=True)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/pathlib.py", line 1116, in mkdir
    os.mkdir(self, mode)
FileExistsError: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/data/raw/behavioral/hcp1200_behavioral_data.csv'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/main.py", line 116, in <module>
    sys.exit(run_pipeline())
             ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/main.py", line 38, in run_pipeline
    ensure_dirs()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/config.py", line 42, in ensure_dirs
    path.mkdir(parents=True, exist_ok=True)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/pathlib.py", line 1116, in mkdir
    os.mkdir(self, mode)
FileExistsError: [Errno 17] File exists: '/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/data/raw/behavioral/hcp1200_behavioral_data.csv'

## Declared deliverables still missing

- data/processed/predictions.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/predictions.npy` is declared but was NOT written. Scripts referencing it:
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
    - `code/modeling/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/predictions.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
