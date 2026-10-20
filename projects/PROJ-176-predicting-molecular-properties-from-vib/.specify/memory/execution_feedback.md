# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…str, np.ndarray]:     """Generate synthetic noise for domain shift s…”
- code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic validation data (Domain Shift Simulation…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/qm9.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py train --max-samples 30000`
  - script usage: `main.py [-h] {download,preprocess,train,evaluate,validate} ...`
  - argparse error: `main.py: error: unrecognized arguments: --max-samples 30000`
- run-book command: `python code/main.py evaluate --checkpoint models/checkpoint_best.pt`
  - script usage: `main.py [-h] {download,preprocess,train,evaluate,validate} ...`
  - argparse error: `main.py: error: unrecognized arguments: --checkpoint models/checkpoint_best.pt`
- run-book command: `python code/main.py validate --checkpoint models/checkpoint_best.pt`
  - script usage: `main.py [-h] {download,preprocess,train,evaluate,validate} ...`
  - argparse error: `main.py: error: unrecognized arguments: --checkpoint models/checkpoint_best.pt`
- run-book command: `python code/main.py control --checkpoint models/checkpoint_best.pt`
  - script usage: `main.py [-h] {download,preprocess,train,evaluate,validate} ...`
  - argparse error: `main.py: error: argument command: invalid choice: 'control' (choose from 'download', 'preprocess', 'train', 'evaluate', 'validate')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…str, np.ndarray]:     """Generate synthetic noise for domain shift s…”; code/evaluation/validate.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic validation data (Domain Shift Simulation…”; every produced artifact is gitignored (data/raw/qm9.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 8 command(s) failed: python code/main.py download (rc=1); python code/main.py preprocess (rc=1); python code/main.py train --max-samples 30000 (rc=2); 3 declared deliverable(s) absent: data/processed/aligned_dataset.npz; data/processed/alignment_report.json; data/raw/ir_spectra.parquet

## Failing / missing run-book commands

- python code/main.py download -> rc=1
ta/raw/qm9.parquet
2026-10-20 10:15:55,339 - data.download - INFO - Downloading IR spectra dataset from https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet
2026-10-20 10:15:55,448 - data.download - ERROR - Data ingestion failed: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/data/download.py", line 146, in main
    ir_path = download_ir_spectra()
              ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/data/download.py", line 66, in download_ir_spectra
    response.raise_for_status()  # Fail fast on HTTP errors
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url: https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet

- python code/main.py preprocess -> rc=1
-properties-from-vib/code/data/preprocess.py", line 97, in main
    ir_df = load_ir_spectra_data()
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-176-predicting-molecular-properties-from-vib/code/data/preprocess.py", line 25, in load_ir_spectra_data
    return pd.read_parquet(ir_path)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 667, in read_parquet
    return impl.read(
           ^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 267, in read
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 140, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 882, in get_handle
    handle = open(handle, ioargs.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/ir_spectra.parquet'

- python code/main.py train --max-samples 30000 -> rc=2
2026-10-20 10:15:59 - molecular_properties - INFO - Starting molecular properties prediction pipeline

usage: main.py [-h] {download,preprocess,train,evaluate,validate} ...
main.py: error: unrecognized arguments: --max-samples 30000

- python code/main.py evaluate --checkpoint models/checkpoint_best.pt -> rc=2
2026-10-20 10:16:00 - molecular_properties - INFO - Starting molecular properties prediction pipeline

usage: main.py [-h] {download,preprocess,train,evaluate,validate} ...
main.py: error: unrecognized arguments: --checkpoint models/checkpoint_best.pt

- python code/main.py validate --checkpoint models/checkpoint_best.pt -> rc=2
2026-10-20 10:16:02 - molecular_properties - INFO - Starting molecular properties prediction pipeline

usage: main.py [-h] {download,preprocess,train,evaluate,validate} ...
main.py: error: unrecognized arguments: --checkpoint models/checkpoint_best.pt

- python code/main.py control --checkpoint models/checkpoint_best.pt -> rc=2
2026-10-20 10:16:03 - molecular_properties - INFO - Starting molecular properties prediction pipeline

usage: main.py [-h] {download,preprocess,train,evaluate,validate} ...
main.py: error: argument command: invalid choice: 'control' (choose from 'download', 'preprocess', 'train', 'evaluate', 'validate')

- python -m pytest tests/ -v > logs/pytest.log 2>&1 -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-176-predicting-molecular-properties-from-vib/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.13.5, cov-7.1.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: >


- python -m pytest tests/ -v > logs/pytest.log 2>&1 -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-176-predicting-molecular-properties-from-vib/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.13.5, cov-7.1.0, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: >



## Declared deliverables still missing

- data/processed/aligned_dataset.npz
- data/processed/alignment_report.json
- data/raw/ir_spectra.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_dataset.npz` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.npz` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alignment_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alignment_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ir_spectra.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/scripts/profile_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ir_spectra.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
