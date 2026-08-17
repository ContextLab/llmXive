# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aFrame:     """     Load simulated student data from CSV.      Args:…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with simulated student records.      Raises:         Fi…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…ileNotFoundError: If the simulated data file does not exist.…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aise FileNotFoundError(f"Simulated data file not found at: {file…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading simulated student data from: {file_path}")…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…raise ValueError(f"Simulated data missing required columns…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “….info(f"Loaded {len(df)} simulated student records")     return df  def val…”
- code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Merge real and simulated datasets.      Args:         real…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate/explanation_generator.py --problem-id sample_001 --mode all`
  - script usage: `explanation_generator.py [-h] [--output-dir OUTPUT_DIR]`
  - argparse error: `explanation_generator.py: error: unrecognized arguments: --mode all`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 45 fabricated/simulated-result signal(s) — results are not real measurements: code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…aFrame:     """     Load simulated student data from CSV.      Args:…”; code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…:         DataFrame with simulated student records.      Raises:         Fi…”; code/analyze/merge_real_data.py: synthetic/fake INPUT data not authorized by the spec — “…ileNotFoundError: If the simulated data file does not exist.…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/download/fetch_datasets.py; 4 command(s) failed: python code/generate/explanation_generator.py --problem-id sample_001 --mode all (rc=2); python code/simulate/calibration.py --pilot-data data/pilot/human_calibration.csv (rc=1); python code/simulate/run_simulation.py --num-students 2000 --conditions neural,symbolic,neuro_symbolic (rc=1); 4 declared deliverable(s) absent: data/derived/combined_logs.csv; data/derived/real_student_data_validated.csv; data/derived/rt_distribution_validation.json

## Failing / missing run-book commands

- python code/download/fetch_datasets.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/download/fetch_datasets.py': [Errno 2] No such file or directory
- python code/generate/explanation_generator.py --problem-id sample_001 --mode all -> rc=2
    usage: explanation_generator.py [-h] [--output-dir OUTPUT_DIR]
                                [--problem-id PROBLEM_ID]
                                [--problem-type PROBLEM_TYPE]
explanation_generator.py: error: unrecognized arguments: --mode all
- python code/simulate/calibration.py --pilot-data data/pilot/human_calibration.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/simulate/calibration.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/simulate/run_simulation.py --num-students 2000 --conditions neural,symbolic,neuro_symbolic -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/simulate/run_simulation.py", line 8, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/analyze/mixed_effects.py --input data/derived/simulation_logs.csv --output data/derived/regression_results.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin/code/analyze/mixed_effects.py", line 17, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/derived/combined_logs.csv
- data/derived/real_student_data_validated.csv
- data/derived/rt_distribution_validation.json
- data/pilot/raw_pilot_data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/combined_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/combined_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/real_student_data_validated.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/real_student_data_validated.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rt_distribution_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/simulate/validate_rt_distribution.py` — NOT invoked by the run-book
    - `code/simulate/run_simulation.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/rt_distribution_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/pilot/raw_pilot_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/simulate/calculate_calibration_metrics.py` — NOT invoked by the run-book
    - `code/simulate/calibration.py` — IS a run-book command
    - `code/download/check_pilot_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/pilot/raw_pilot_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
