# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…handle it downstream or generate synthetic images if needed (not im…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic cognitive data if real d…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic cognitive data for N={n}...")     set_r…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic fallback data if proxy l…”
- code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…Stub for generating a synthetic dataset when real data cannot be…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…handle it downstream or generate synthetic images if needed (not im…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic cognitive data if real d…”; code/01_data_acquisition.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic cognitive data for N={n}...")     set_r…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/04_sensitivity.py; python code/05_reporting.py; 2 command(s) failed: python code/02_visual_metrics.py (rc=-1); python code/03_analysis.py (rc=1); 4 declared deliverable(s) absent: data/processed/final_analysis_data_all.csv; data/processed/final_analysis_data_object_only.csv; data/processed/merged_data.csv

## Failing / missing run-book commands

- python code/02_visual_metrics.py -> rc=-1


[TIMEOUT after 120s]
- python code/03_analysis.py -> rc=1
2026-10-10 06:31:31 - utils - INFO - Random seed set to 42
2026-10-10 06:31:31 - __main__ - INFO - Starting statistical analysis pipeline...
2026-10-10 06:31:31 - __main__ - ERROR - Analysis data file not found: data/processed/final_analysis_data_all.csv or data/processed/final_analysis_data_object_only.csv


- python code/04_sensitivity.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/04_sensitivity.py': [Errno 2] No such file or directory

- python code/05_reporting.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-479-the-impact-of-visual-distraction-on-cogn/code/05_reporting.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/final_analysis_data_all.csv
- data/processed/final_analysis_data_object_only.csv
- data/processed/merged_data.csv
- data/raw/cognitive_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_analysis_data_all.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_visual_metrics.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis_data_all.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_analysis_data_object_only.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_visual_metrics.py` — IS a run-book command
    - `code/03_analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_analysis_data_object_only.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_acquisition.py` — IS a run-book command
    - `code/02_visual_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/merged_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/cognitive_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_acquisition.py` — IS a run-book command
    - `code/02_visual_metrics.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/cognitive_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
