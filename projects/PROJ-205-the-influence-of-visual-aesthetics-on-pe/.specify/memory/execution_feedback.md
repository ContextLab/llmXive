# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…""Return the path to the mock data CSV for benchmarking."""…”
- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…0:         # Fallback to mock data ONLY if explicitly reque…”
- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…# We will check for mock data if real is missing, as p…”
- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate synthetic mock data for power anal…”
- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…"     Generate synthetic mock data for power analysis if no…”
- code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…a mode where we generate mock data for benchmarking     # (…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…""Return the path to the mock data CSV for benchmarking."""…”; code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…0:         # Fallback to mock data ONLY if explicitly reque…”; code/analysis/06_power_analysis.py: synthetic/fake INPUT data not authorized by the spec — “…# We will check for mock data if real is missing, as p…”; 1 run-book script(s) missing (plan/impl path mismatch): python 03_mixed_effects.py --input ../../data/raw/participants.csv --output ../../data/processed/mixed_effects_results.json; 2 command(s) failed: python code/analysis/01_anova.py --input ../../data/raw/participants.csv --output ../../data/processed/anova_results.json (rc=1); python code/analysis/02_pairwise.py --input ../../data/raw/participants.csv --output ../../data/processed/pairwise_results.json (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_data.csv; data/raw/submissions.csv

## Failing / missing run-book commands

- python code/analysis/01_anova.py --input ../../data/raw/participants.csv --output ../../data/processed/anova_results.json -> rc=1
    Loading data from ../../data/raw/participants.csv...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 268, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 236, in main
    df = load_wide_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/01_anova.py", line 51, in load_wide_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: ../../data/raw/participants.csv
- python code/analysis/02_pairwise.py --input ../../data/raw/participants.csv --output ../../data/processed/pairwise_results.json -> rc=1
    Loading data from ../../data/raw/participants.csv...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/02_pairwise.py", line 187, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/02_pairwise.py", line 166, in main
    df = load_wide_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/analysis/02_pairwise.py", line 50, in load_wide_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: ../../data/raw/participants.csv
- python 03_mixed_effects.py --input ../../data/raw/participants.csv --output ../../data/processed/mixed_effects_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe/03_mixed_effects.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/cleaned_data.csv
- data/raw/submissions.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/01_preprocess.py` — NOT invoked by the run-book
    - `code/analysis/01_anova.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/submissions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/survey/app.py` — NOT invoked by the run-book
    - `code/analysis/06_power_analysis.py` — NOT invoked by the run-book
    - `code/analysis/01_preprocess.py` — NOT invoked by the run-book
    - `code/utils/truncate_metadata.py` — NOT invoked by the run-book
    - `code/utils/helpers.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/submissions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
