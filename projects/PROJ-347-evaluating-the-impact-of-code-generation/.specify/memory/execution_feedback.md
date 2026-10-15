# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/download_devign.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     """     # ---------…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/download_devign.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.     """     # ---------…”; 1 command(s) failed: python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.0 0.5 0.9 (rc=1); 3 declared deliverable(s) absent: data/checksums.json; data/processed/human_python.csv; data/raw/juliet/python_vuln.csv

## Failing / missing run-book commands

- python -m src.run_pipeline  --seed 42  --max-pairs 300  --confidence-thresholds 0.0 0.5 0.9 -> rc=1
-impact-of-code-generation/data/raw/devign/devign.csv
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/src/run_pipeline.py", line 72, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/src/run_pipeline.py", line 59, in main
    download_devign_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/code/download_devign.py", line 110, in main
    download_file(RAW_CSV_URL, CSV_DEST)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-347-evaluating-the-impact-of-code-generation/code/download_devign.py", line 49, in download_file
    r.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/Juliet-Test-Suite/SARD/master/data/python_vuln.csv


## Declared deliverables still missing

- data/checksums.json
- data/processed/human_python.csv
- data/raw/juliet/python_vuln.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_devign.py` — NOT invoked by the run-book
    - `code/download_juliet.py` — NOT invoked by the run-book
    - `src/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/human_python.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_human_python.py` — NOT invoked by the run-book
    - `src/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/human_python.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/juliet/python_vuln.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_devign.py` — NOT invoked by the run-book
    - `code/download_juliet.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/juliet/python_vuln.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
