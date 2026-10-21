# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”
- code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”
- code/utils/artifacts.py: synthetic/fake INPUT data not authorized by the spec — “…attempt any fallback or synthetic data generation.  If validati…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/single_run_results.json, data/raw/matrix_N1000_seed42.npy) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main --mode sweep --N 2000 --theta-min 0.5 --theta-max 3.0 --theta-step 0.1  --k 1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000`
  - script usage: `main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --theta-min 0.5 --theta-max 3.0 --theta-step 0.1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000`
- run-book command: `python -m code.main --mode sensitivity --N 1500 --theta 1.5 --k 2 --pattern random-sparse  --densities 0.05 0.1 0.2 0.3 0.4 0.5 --iterations 500 --seed-start 5000`
  - script usage: `main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]`
  - argparse error: `main.py: error: argument --mode: invalid choice: 'sensitivity' (choose from 'single', 'sweep')`
- run-book command: `python -m code.main --mode finite-size --Ns 500 1000 1500 2000 --theta 1.5 --k 1  --pattern diagonal --iterations 500 --seed-start 8000`
  - script usage: `main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]`
  - argparse error: `main.py: error: argument --mode: invalid choice: 'finite-size' (choose from 'single', 'sweep')`
- run-book command: `python -m code.main --mode aggregate     # writes data/processed/aggregated_thresholds.json, exit 0`
  - script usage: `main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]`
  - argparse error: `main.py: error: argument --mode: invalid choice: 'aggregate' (choose from 'single', 'sweep')`
- run-book command: `python -m code.main --mode fit           # writes data/processed/threshold_fit.json, exit 0`
  - script usage: `main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]`
  - argparse error: `main.py: error: argument --mode: invalid choice: 'fit' (choose from 'single', 'sweep')`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/generate_sensitivity_report.py: synthetic/fake INPUT data not authorized by the spec — “…tistical correlations in simulated data. No physical system is m…”; code/research.md: synthetic/fake INPUT data not authorized by the spec — “…correlations within the simulated data. - **Role**: The algorit…”; code/utils/artifacts.py: synthetic/fake INPUT data not authorized by the spec — “…attempt any fallback or synthetic data generation.  If validati…”; every produced artifact is gitignored (data/processed/single_run_results.json, data/raw/matrix_N1000_seed42.npy) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 8 command(s) failed: python -m pytest tests/contract/test_schemas.py -v   # all tests PASSED, none SKIPPED (rc=4); python -m code.main --mode sweep --N 2000 --theta-min 0.5 --theta-max 3.0 --theta-step 0.1  --k 1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000 (rc=2); python -m code.main --mode sensitivity --N 1500 --theta 1.5 --k 2 --pattern random-sparse  --densities 0.05 0.1 0.2 0.3 0.4 0.5 --iterations 500 --seed-start 5000 (rc=2); 3 declared deliverable(s) absent: data/figures/outlier_probability_vs_theta.png; data/processed/sensitivity_metadata.json; data/processed/sensitivity_variation.csv

## Failing / missing run-book commands

- python -m pytest tests/contract/test_schemas.py -v   # all tests PASSED, none SKIPPED -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m code.main --mode sweep --N 2000 --theta-min 0.5 --theta-max 3.0 --theta-step 0.1  --k 1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000 -> rc=2

usage: main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]
               [--theta THETA] [--k K] [--pattern PATTERN]
main.py: error: unrecognized arguments: --theta-min 0.5 --theta-max 3.0 --theta-step 0.1 2 5 --patterns diagonal block-sparse random-sparse --iterations 500 --seed-start 1000

- python -m code.main --mode sensitivity --N 1500 --theta 1.5 --k 2 --pattern random-sparse  --densities 0.05 0.1 0.2 0.3 0.4 0.5 --iterations 500 --seed-start 5000 -> rc=2

usage: main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]
               [--theta THETA] [--k K] [--pattern PATTERN]
main.py: error: argument --mode: invalid choice: 'sensitivity' (choose from 'single', 'sweep')

- python -m code.main --mode finite-size --Ns 500 1000 1500 2000 --theta 1.5 --k 1  --pattern diagonal --iterations 500 --seed-start 8000 -> rc=2

usage: main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]
               [--theta THETA] [--k K] [--pattern PATTERN]
main.py: error: argument --mode: invalid choice: 'finite-size' (choose from 'single', 'sweep')

- python -m code.main --mode aggregate     # writes data/processed/aggregated_thresholds.json, exit 0 -> rc=2

usage: main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]
               [--theta THETA] [--k K] [--pattern PATTERN]
main.py: error: argument --mode: invalid choice: 'aggregate' (choose from 'single', 'sweep')

- python -m code.main --mode fit           # writes data/processed/threshold_fit.json, exit 0 -> rc=2

usage: main.py [-h] --mode {single,sweep} [--N N] [--seed SEED]
               [--theta THETA] [--k K] [--pattern PATTERN]
main.py: error: argument --mode: invalid choice: 'fit' (choose from 'single', 'sweep')

- python -m pytest tests/contract/ -v        # per-file schema validation; FAILS on missing files -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python -m pytest tests/integration/ -v     # reproducibility: top eigenvalue within 1e-6 of reference -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-551-asymptotic-behavior-of-random-matrix-eig/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #



## Declared deliverables still missing

- data/figures/outlier_probability_vs_theta.png
- data/processed/sensitivity_metadata.json
- data/processed/sensitivity_variation.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/figures/outlier_probability_vs_theta.png` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/plot_outlier_probability.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/figures/outlier_probability_vs_theta.png` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_metadata_recorder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_variation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity_variation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_variation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
