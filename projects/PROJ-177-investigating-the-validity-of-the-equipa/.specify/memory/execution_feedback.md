# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…ault test parameters for synthetic dataset generation.  This module…”
- code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…efault configuration for synthetic test datasets.          Returns:…”
- code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…"purpose": "Synthetic test data generation for pipeline…”
- code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…ault test parameters for synthetic datasets."     )     parser.add_a…”
- code/verify_energy_implementation.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generate synthetic data with known ground t…”

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -m code.data_ingestion --download --zenodo-id 10.5281/zenodo.1456789`
- `python -m code.main`
- `python -m code.main --seed 42`

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m code.main --seed 42`
  - script usage: `main.py [-h]`
  - argparse error: `main.py: error: unrecognized arguments: --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…ault test parameters for synthetic dataset generation.  This module…”; code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…efault configuration for synthetic test datasets.          Returns:…”; code/generate_test_params.py: synthetic/fake INPUT data not authorized by the spec — “…"purpose": "Synthetic test data generation for pipeline…”; 3 command(s) failed: python -m code.data_ingestion --download --zenodo-id 10.5281/zenodo.1456789 (rc=1); python -m code.main (rc=1); python -m code.main --seed 42 (rc=2); 3 declared deliverable(s) absent: data/derived/energy_samples.csv; data/derived/test_nonthermal_data.csv; data/derived/test_thermal_data.csv

## Failing / missing run-book commands

- python -m code.data_ingestion --download --zenodo-id 10.5281/zenodo.1456789 -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-177-investigating-the-validity-of-the-equipa/code/.venv/bin/python: No module named code.data_ingestion
- python -m code.main -> rc=1
    <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-177-investigating-the-validity-of-the-equipa/code/main.py", line 209, in main
    ret = run_ingestion(args)
          ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-177-investigating-the-validity-of-the-equipa/code/main.py", line 60, in run_ingestion
    from ingestion import main as ingestion_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-177-investigating-the-validity-of-the-equipa/code/ingestion.py", line 27, in <module>
    logging.FileHandler('logs/pipeline.log')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-177-investigating-the-validity-of-the-equipa/logs/pipeline.log'
- python -m code.main --seed 42 -> rc=2
    usage: main.py [-h]
               [--stage {all,checksum_raw,hash_artifacts,ingest,stats,sensitivity,regression,dry_run}]
               [--config CONFIG] [--verbose] [--sample-ratio SAMPLE_RATIO]
               [--alpha ALPHA] [--thresholds THRESHOLDS]
               [--data-source DATA_SOURCE] [--local-only] [--allow-incomplete]
main.py: error: unrecognized arguments: --seed 42

## Declared deliverables still missing

- data/derived/energy_samples.csv
- data/derived/test_nonthermal_data.csv
- data/derived/test_thermal_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/energy_samples.csv` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — NOT invoked by the run-book
    - `code/main.py` — NOT invoked by the run-book
    - `code/generate_statistical_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/energy_samples.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/test_nonthermal_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_test_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/test_nonthermal_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/test_thermal_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_test_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/test_thermal_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
