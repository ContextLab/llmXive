# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/simulation/generator.py: self-declared fabricated metric — “…"se": 0.1,  # arbitrary constant standard error…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/base_template.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --mode dry-run --replicates 10 --levels 0 0.1 --seed 42`
  - script usage: `main.py [-h] [--mode {dry-run,full}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --replicates 10 --levels 0 0.1`
- run-book command: `python code/main.py --validate-contracts`
  - script usage: `main.py [-h] [--mode {dry-run,full}] [--seed SEED]`
  - argparse error: `main.py: error: unrecognized arguments: --validate-contracts`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/simulation/generator.py: self-declared fabricated metric — “…"se": 0.1,  # arbitrary constant standard error…”; every produced artifact is gitignored (data/processed/base_template.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/main.py --mode full --seed 12345 (rc=1); python code/main.py --mode dry-run --replicates 10 --levels 0 0.1 --seed 42 (rc=2); python code/main.py --validate-contracts (rc=2); 3 declared deliverable(s) absent: data/results/aggregated_metrics.csv; data/results/reml_failures.json; data/results/stability_analysis.json

## Failing / missing run-book commands

- python code/main.py --mode full --seed 12345 -> rc=1

2026-10-25 10:08:20,742 INFO __main__: Generating 900 replicates for τ²=0.0
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 210, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 164, in main
    metrics = _run_simulation(tau2_levels, replicates, args.seed, base_csv)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/main.py", line 96, in _run_simulation
    mr = MetricsResult(
         ^^^^^^^^^^^^^^
TypeError: MetricsResult.__init__() got an unexpected keyword argument 'tau_squared'

- python code/main.py --mode dry-run --replicates 10 --levels 0 0.1 --seed 42 -> rc=2

usage: main.py [-h] [--mode {dry-run,full}] [--seed SEED]
main.py: error: unrecognized arguments: --replicates 10 --levels 0 0.1

- python code/main.py --validate-contracts -> rc=2

usage: main.py [-h] [--mode {dry-run,full}] [--seed SEED]
main.py: error: unrecognized arguments: --validate-contracts

- python -m pytest tests/unit/ -> rc=2
nei
configfile: pyproject.toml
collected 74 items / 1 error

==================================== ERRORS ====================================
________________ ERROR collecting tests/unit/test_generator.py _________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/unit/test_generator.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_generator.py:23: in <module>
    from simulation.generator import (
E   ImportError: cannot import name 'SimulationResult' from 'simulation.generator' (/home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/code/simulation/generator.py)
=========================== short test summary info ============================
ERROR tests/unit/test_generator.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.77s ===============================


- python -m pytest tests/integration/ -> rc=1
onkeypatch.syspath_prepend(str(repo_root))
    
        # Run the pipeline in dry‑run mode (small subset, fast).
        exit_code = _run_cmd(
            ["code/main.py", "--mode", "dry-run", "--seed", "42"]
        )
>       assert exit_code == 0, "Pipeline execution failed"
E       AssertionError: Pipeline execution failed
E       assert 1 == 0

tests/integration/test_pipeline.py:43: AssertionError
=============================== warnings summary ===============================
tests/integration/test_pipeline.py:30
  /home/runner/work/llmXive/llmXive/projects/PROJ-417-assessing-the-impact-of-data-heterogenei/tests/integration/test_pipeline.py:30: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.timeout(300)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_pipeline.py::test_full_pipeline_dry_run - Asser...
========================= 1 failed, 1 warning in 0.92s =========================



## Declared deliverables still missing

- data/results/aggregated_metrics.csv
- data/results/reml_failures.json
- data/results/stability_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/aggregated_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/aggregate_metrics.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_aggregated_metrics.py` — NOT invoked by the run-book
    - `code/visualization/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/aggregated_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/reml_failures.json` is declared but was NOT written. Scripts referencing it:
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/simulation/estimators.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/reml_failures.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/reporting/report_gen.py` — NOT invoked by the run-book
    - `code/run_sensitivity_sweep.py` — NOT invoked by the run-book
    - `code/run_stability_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
