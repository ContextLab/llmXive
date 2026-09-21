# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Belief Upd…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “….DataFrame]:     """     Generate a complete synthetic dataset for model valida…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…}          logger.info(f"Generated synthetic dataset: {n_participants…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main entry point for synthetic data generation."""     parse…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic behavioral data for mode…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Starting synthetic data generation")     logger.…”
- code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…)          logger.info("Synthetic data generation completed suc…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/utils/io.py --verify-checksums`
  - script usage: `io.py [-h] {verify-checksums} ...`
  - argparse error: `io.py: error: unrecognized arguments: --verify-checksums`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Belief Upd…”; code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “….DataFrame]:     """     Generate a complete synthetic dataset for model valida…”; code/modeling/synthetic_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…}          logger.info(f"Generated synthetic dataset: {n_participants…”; 6 command(s) failed: python code/utils/io.py --verify-checksums (rc=2); python code/main.py --stage preprocessing (rc=1); python code/main.py --stage modeling (rc=1); 1 declared deliverable(s) absent: data/reports/qc_summary.json

## Failing / missing run-book commands

- python code/utils/io.py --verify-checksums -> rc=2
    usage: io.py [-h] {verify-checksums} ...
io.py: error: unrecognized arguments: --verify-checksums
- python code/main.py --stage preprocessing -> rc=1
    __.py:50: FutureWarning: 
ArviZ is undergoing a major refactor to improve flexibility and extensibility while maintaining a user-friendly interface.
Some upcoming changes may be backward incompatible.
For details and migration guidance, visit: https://python.arviz.org/en/latest/user_guide/migration_guide.html
  warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 35, in <module>
    from openneuro import client
ModuleNotFoundError: No module named 'openneuro'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 19, in <module>
    from preprocessing.data_download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 37, in <module>
    raise ImportError(
ImportError: The 'openneuro' package is required for data download. Please install it via: pip install openneuro
- python code/main.py --stage modeling -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 35, in <module>
    from openneuro import client
ModuleNotFoundError: No module named 'openneuro'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 19, in <module>
    from preprocessing.data_download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 37, in <module>
    raise ImportError(
ImportError: The 'openneuro' package is required for data download. Please install it via: pip install openneuro
- python code/main.py --stage analysis -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 35, in <module>
    from openneuro import client
ModuleNotFoundError: No module named 'openneuro'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 19, in <module>
    from preprocessing.data_download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 37, in <module>
    raise ImportError(
ImportError: The 'openneuro' package is required for data download. Please install it via: pip install openneuro
- python code/main.py --stage sensitivity -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 35, in <module>
    from openneuro import client
ModuleNotFoundError: No module named 'openneuro'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 19, in <module>
    from preprocessing.data_download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 37, in <module>
    raise ImportError(
ImportError: The 'openneuro' package is required for data download. Please install it via: pip install openneuro
- python code/main.py --stage reporting -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 35, in <module>
    from openneuro import client
ModuleNotFoundError: No module named 'openneuro'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/main.py", line 19, in <module>
    from preprocessing.data_download import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/code/preprocessing/data_download.py", line 37, in <module>
    raise ImportError(
ImportError: The 'openneuro' package is required for data download. Please install it via: pip install openneuro

## Declared deliverables still missing

- data/reports/qc_summary.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/reports/qc_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocessing/qc_reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/qc_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
