# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…cal mode, this creates a mock dataset structure.     In real m…”
- code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…)         logger.info(f"Mock dataset created at: {mock_path}"…”
- code/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…l_trials = []          # Mock data generation is FORBIDDEN.…”
- code/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…s is a limitation of the mock data structure.…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/ds001435/dataset_description.json, data/raw/ds001435/participants.tsv, data/raw/ds001435/sub-01/func/sub-01_task-rsvp_events.tsv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocess.py`
  - script usage: `preprocess.py [-h] --data_dir DATA_DIR [--output_path OUTPUT_PATH]`
  - argparse error: `preprocess.py: error: the following arguments are required: --data_dir`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…cal mode, this creates a mock dataset structure.     In real m…”; code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…)         logger.info(f"Mock dataset created at: {mock_path}"…”; code/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…l_trials = []          # Mock data generation is FORBIDDEN.…”; every produced artifact is gitignored (data/raw/ds001435/dataset_description.json, data/raw/ds001435/participants.tsv, data/raw/ds001435/sub-01/func/sub-01_task-rsvp_events.tsv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/visualize.py; python code/run_pipeline.py; 3 command(s) failed: python code/preprocess.py (rc=2); python code/model_fit.py (rc=1); python -m pytest tests/ (rc=1); 1 declared deliverable(s) absent: data/processed/analysis.csv

## Failing / missing run-book commands

- python code/preprocess.py -> rc=2

usage: preprocess.py [-h] --data_dir DATA_DIR [--output_path OUTPUT_PATH]
                     [--schema_path SCHEMA_PATH]
                     [--ivt_threshold IVT_THRESHOLD]
                     [--min_fixation_ms MIN_FIXATION_MS]
preprocess.py: error: the following arguments are required: --data_dir

- python code/model_fit.py -> rc=1

{"timestamp": "2026-10-09T13:24:09.019460", "level": "ERROR", "logger": "model_fit", "message": "Pipeline failed: Analysis CSV not found at data/processed/analysis.csv. Run preprocessing first."}

- python code/visualize.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py': [Errno 2] No such file or directory

- python code/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/run_pipeline.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/model_fit.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
