# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/ingest/load_illusions.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.  The module can also be…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.ingest.load_illusions  --download  --output-dir data/raw`
  - script usage: `load_illusions.py [-h] {download_muller} ...`
  - argparse error: `load_illusions.py: error: argument command: invalid choice: 'data/raw' (choose from 'download_muller')`
- run-book command: `python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean`
  - script usage: `load_illusions.py [-h] {download_muller} ...`
  - argparse error: `load_illusions.py: error: argument command: invalid choice: 'data/raw' (choose from 'download_muller')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: src/ingest/load_illusions.py: synthetic/fake INPUT data not authorized by the spec — “…silently falling back to synthetic data.  The module can also be…”; 5 command(s) failed: python -m src.ingest.load_illusions  --download  --output-dir data/raw (rc=2); python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean (rc=2); python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 (rc=1); 9 declared deliverable(s) absent: data/clean/aligned_subjects.csv; data/clean/clean_muller_lyer.csv; data/clean/clean_ponzo.csv

## Failing / missing run-book commands

- python -m src.ingest.load_illusions  --download  --output-dir data/raw -> rc=2

usage: load_illusions.py [-h] {download_muller} ...
load_illusions.py: error: argument command: invalid choice: 'data/raw' (choose from 'download_muller')

- python -m src.ingest.load_illusions  --clean  --raw-dir data/raw  --clean-dir data/clean -> rc=2

usage: load_illusions.py [-h] {download_muller} ...
load_illusions.py: error: argument command: invalid choice: 'data/raw' (choose from 'download_muller')

- python -m src.model.predictive_coding  --input data/clean/clean_muller_lyer.csv  --output data/derived/precision_parameters.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: Error while finding module specification for 'src.model.predictive_coding' (ModuleNotFoundError: No module named 'src.model')

- python -m src.analysis.null_model  --input data/clean/clean_ponzo.csv  --output data/derived/ponzo_susceptibility.csv  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: Error while finding module specification for 'src.analysis.null_model' (ModuleNotFoundError: No module named 'src.analysis')

- python -m src.analysis.correlation  --precision data/derived/precision_parameters.csv  --susceptibility data/derived/ponzo_susceptibility.csv  --results outputs/correlation_results.json  --fig-dir outputs/figures  --bootstrap 1000  --permute 1000  --seed 42 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-406-investigating-neural-signatures-of-predi/bin/python: Error while finding module specification for 'src.analysis.correlation' (ModuleNotFoundError: No module named 'src.analysis')


## Declared deliverables still missing

- data/clean/aligned_subjects.csv
- data/clean/clean_muller_lyer.csv
- data/clean/clean_ponzo.csv
- data/derived/ponzo_null_parameters.csv
- data/derived/ponzo_susceptibility.csv
- data/derived/precision_parameters.csv
- data/merged/merged_results.csv
- data/raw/muller_lyer.parquet
- data/raw/ponzo.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/clean/aligned_subjects.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/clean/clean_muller_lyer.csv` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/clean/clean_muller_lyer.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/clean/clean_ponzo.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_null_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/ponzo_susceptibility.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/derived/precision_parameters.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/merged/merged_results.csv` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/raw/muller_lyer.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/ingest/load_illusions.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/muller_lyer.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ponzo.parquet` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
