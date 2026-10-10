# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…rror, non‑200 response), generate a small synthetic EEG/trajectory CSV for l…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…e."     )      # Minimal synthetic data – 2 participants, 2 tria…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…)     logger.info(f"Synthetic dataset written to {dest}")  # -…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…Corpus or fall back to a synthetic     dataset. The function is idempot…”
- code/download.py: synthetic/fake INPUT data not authorized by the spec — “…or generate a "         "synthetic fallback dataset."     )     parser.add_a…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/synthetic_navigation_data.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocess.py`
  - script usage: `preprocess.py [-h] [--config CONFIG] --input INPUT --output OUTPUT`
  - argparse error: `preprocess.py: error: the following arguments are required: --input, --output`
- run-book command: `python code/viz.py`
  - script usage: `viz.py [-h] --data DATA [--sensitivity-data SENSITIVITY_DATA] --output`
  - argparse error: `viz.py: error: the following arguments are required: --data, --output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/download.py: synthetic/fake INPUT data not authorized by the spec — “…rror, non‑200 response), generate a small synthetic EEG/trajectory CSV for l…”; code/download.py: synthetic/fake INPUT data not authorized by the spec — “…e."     )      # Minimal synthetic data – 2 participants, 2 tria…”; code/download.py: synthetic/fake INPUT data not authorized by the spec — “…)     logger.info(f"Synthetic dataset written to {dest}")  # -…”; every produced artifact is gitignored (data/raw/synthetic_navigation_data.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/preprocess.py (rc=2); python code/analysis.py (rc=1); python code/viz.py (rc=2)

## Failing / missing run-book commands

- python code/preprocess.py -> rc=2

usage: preprocess.py [-h] [--config CONFIG] --input INPUT --output OUTPUT
preprocess.py: error: the following arguments are required: --input, --output

- python code/analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/analysis.py", line 18, in <module>
    from config_loader import load_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/config_loader.py", line 14, in <module>
    from .logging_config import get_logger
ImportError: attempted relative import with no known parent package

- python code/viz.py -> rc=2

usage: viz.py [-h] --data DATA [--sensitivity-data SENSITIVITY_DATA] --output
              OUTPUT [--electrodes ELECTRODES [ELECTRODES ...]]
viz.py: error: the following arguments are required: --data, --output

- python -m pytest tests/ -v -> rc=3
NALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/.venv/lib/python3.11/site-packages/_pytest/debugging.py", line 66, in pytest_configure
INTERNALERROR>     import pdb
INTERNALERROR>   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pdb.py", line 77, in <module>
INTERNALERROR>     import code
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/__init__.py", line 12, in <module>
INTERNALERROR>     from .analysis import FeasibilityError, load_processed_data, fit_linear_mixed_effects_model, run_sensitivity_sweep, main as analysis_main
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/analysis.py", line 18, in <module>
INTERNALERROR>     from config_loader import load_config
INTERNALERROR>   File "/home/runner/work/llmXive/llmXive/projects/PROJ-530-neural-correlates-of-error-monitoring-du/code/config_loader.py", line 14, in <module>
INTERNALERROR>     from .logging_config import get_logger
INTERNALERROR> ImportError: attempted relative import with no known parent package

