# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…r: If the path indicates synthetic data and --allow-synthetic is…”
- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…help="Allow analysis of synthetic data (located in data/synth/)…”
- code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…]          # Define synthetic data directory     synthetic_…”
- code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…'{file_path}' is in the synthetic data directory."     elif is_…”
- code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…r: Attempting to analyze synthetic data from '{file_path}'. "…”
- code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…ntend to run analysis on synthetic data for testing purposes."…”
- code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…ogger.warning(f"Allowing synthetic data analysis: {file_path}. T…”
- code/data_prep.py: synthetic/fake INPUT data not authorized by the spec — “…itly enabled. Generating synthetic data.")                     #…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/03_process_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv`
  - script usage: `03_process_human_coding.py [-h] --annotations-dir ANNOTATIONS_DIR`
  - argparse error: `03_process_human_coding.py: error: the following arguments are required: --annotations-dir, --candidates-csv, --valid-output, --ground-truth-output`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 18 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…r: If the path indicates synthetic data and --allow-synthetic is…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…help="Allow analysis of synthetic data (located in data/synth/)…”; code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…]          # Define synthetic data directory     synthetic_…”; 6 run-book script(s) missing (plan/impl path mismatch): python code/00_pilot_power_analysis.py --config config/pilot.yaml; python code/02_prepare_human_coding_dir.py   # creates data/raw/human_coding/; python code/04_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv; 2 command(s) failed: python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv (rc=1); python code/03_process_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv (rc=2); 2 declared deliverable(s) absent: data/processed/candidates_filtered.csv; data/processed/valid_scenarios.csv

## Failing / missing run-book commands

- python code/00_pilot_power_analysis.py --config config/pilot.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/00_pilot_power_analysis.py': [Errno 2] No such file or directory

- python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv -> rc=1
1.0.0', 'region_descriptions_v1.2.0', 'question_answers_v1.0.0', 'question_answers_v1.2.0', 'objects_v1.0.0', 'objects_v1.2.0', 'attributes_v1.0.0', 'attributes_v1.2.0', 'relationships_v1.0.0', 'relationships_v1.2.0']

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 302, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 295, in main
    ingest_and_filter(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 156, in ingest_and_filter
    raise DataFetchError(
data_prep.DataFetchError: Unable to load Open Images dataset: BuilderConfig 'objects' not found. Available: ['region_descriptions_v1.0.0', 'region_descriptions_v1.2.0', 'question_answers_v1.0.0', 'question_answers_v1.2.0', 'objects_v1.0.0', 'objects_v1.2.0', 'attributes_v1.0.0', 'attributes_v1.2.0', 'relationships_v1.0.0', 'relationships_v1.2.0']

- python code/02_prepare_human_coding_dir.py   # creates data/raw/human_coding/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/02_prepare_human_coding_dir.py': [Errno 2] No such file or directory

- python code/03_process_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv -> rc=2

usage: 03_process_human_coding.py [-h] --annotations-dir ANNOTATIONS_DIR
                                  --candidates-csv CANDIDATES_CSV
                                  --valid-output VALID_OUTPUT
                                  --ground-truth-output GROUND_TRUTH_OUTPUT
03_process_human_coding.py: error: the following arguments are required: --annotations-dir, --candidates-csv, --valid-output, --ground-truth-output

- python code/04_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/04_manipulate_stimuli.py': [Errno 2] No such file or directory

- python code/05_survey_deployment.py  --mode pilot  --participants 10  --output data/processed/responses_raw.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/05_survey_deployment.py': [Errno 2] No such file or directory

- python code/06_data_cleaning.py  --input data/processed/responses_raw.csv  --output data/processed/responses_cleaned.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/06_data_cleaning.py': [Errno 2] No such file or directory

- python code/07_analysis_clmm.py  --input data/processed/responses_cleaned.csv  --output data/processed/analysis_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/07_analysis_clmm.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/candidates_filtered.csv
- data/processed/valid_scenarios.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/candidates_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_filter.py` — IS a run-book command
    - `code/03_process_human_coding.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/candidates_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_scenarios.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_process_human_coding.py` — IS a run-book command
    - `code/human_coding.py` — NOT invoked by the run-book
    - `code/manipulation_check.py` — NOT invoked by the run-book
    - `code/survey_deploy.py` — NOT invoked by the run-book
    - `code/survey_sim.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_scenarios.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
