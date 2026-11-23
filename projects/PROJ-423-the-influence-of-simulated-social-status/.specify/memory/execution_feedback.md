# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/decision_record.json: synthetic/fake INPUT data not authorized by the spec — “…act": "The pipeline uses synthetic data generation based on lite…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…rovides functionality to generate synthetic research data simulating…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic dataset for the social s…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic data with N={n} and seed={see…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…and-line entry point for synthetic data generation.      Parses…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…ed, and output path.     Generates the synthetic dataset and saves it to…”
- code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic research data")     pars…”
- code/simulate.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic data for the specified d…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/preprocess.py`
  - script usage: `preprocess.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `preprocess.py: error: the following arguments are required: --input, --output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 fabricated/simulated-result signal(s) — results are not real measurements: code/decision_record.json: synthetic/fake INPUT data not authorized by the spec — “…act": "The pipeline uses synthetic data generation based on lite…”; code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…rovides functionality to generate synthetic research data simulating…”; code/generate_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic dataset for the social s…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/power_analysis.py; 4 command(s) failed: python code/simulate.py (rc=1); python code/preprocess.py (rc=2); python code/analysis.py (rc=1); 3 declared deliverable(s) absent: data/processed/cleaned_data.csv; data/processed/outcome_type.json; data/processed/structure_config.json

## Failing / missing run-book commands

- python code/power_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/code/power_analysis.py': [Errno 2] No such file or directory
- python code/simulate.py -> rc=1
    Simulation or validation failed: name 'sys' is not defined
- python code/preprocess.py -> rc=2
    usage: preprocess.py [-h] --input INPUT --output OUTPUT
                     [--structure-output STRUCTURE_OUTPUT] [--seed SEED]
preprocess.py: error: the following arguments are required: --input, --output
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/code/analysis.py", line 43, in <module>
    logger = setup_logger("analysis", "logs/analysis.log")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/code/logger.py", line 26, in setup_logger
    fh = logging.FileHandler(log_file)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/logs/analysis.log'
- python code/report.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-423-the-influence-of-simulated-social-status/code/report.py", line 38, in <module>
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    ^^^
NameError: name 'sys' is not defined. Did you mean: 'sns'?

## Declared deliverables still missing

- data/processed/cleaned_data.csv
- data/processed/outcome_type.json
- data/processed/structure_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/outcome_type.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/outcome_type.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/structure_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/structure_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
