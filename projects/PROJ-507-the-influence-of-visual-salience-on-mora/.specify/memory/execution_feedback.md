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

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/human_coding/annotations_template.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 18 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…r: If the path indicates synthetic data and --allow-synthetic is…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…help="Allow analysis of synthetic data (located in data/synth/)…”; code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…]          # Define synthetic data directory     synthetic_…”; every produced artifact is gitignored (data/raw/human_coding/annotations_template.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; overall deadline 300s exceeded; 1 run-book script(s) missing (plan/impl path mismatch): python code/00_pilot_power_analysis.py --config config/pilot.yaml; 3 command(s) failed: python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv (rc=-1); python code/03_process_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv (rc=1); python code/04_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv (rc=1); 3 declared deliverable(s) absent: data/processed/candidates_filtered.csv; data/processed/ground_truth_match.csv; data/processed/valid_scenarios.csv

## Failing / missing run-book commands

- python code/00_pilot_power_analysis.py --config config/pilot.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/00_pilot_power_analysis.py': [Errno 2] No such file or directory

- python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv -> rc=-1
2026-10-30 18:19:34 | INFO     | __main__             | Attempting to load Visual Genome via HuggingFace datasets (streaming).
2026-10-30 18:19:34 | WARNING  | __main__             | Streaming load failed (The `datasets` package cannot be imported in the current environment.). Falling back to direct image download.

2026-10-30 18:19:34,921 INFO __main__: Attempting to load Visual Genome via HuggingFace datasets (streaming).
2026-10-30 18:19:34,921 WARNING __main__: Streaming load failed (The `datasets` package cannot be imported in the current environment.). Falling back to direct image download.

[TIMEOUT after 120s]
- python code/03_process_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv -> rc=1

2026-10-30 18:21:33,993 INFO __main__: Loading annotations from data/raw/human_coding
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/03_process_human_coding.py", line 251, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/03_process_human_coding.py", line 170, in main
    annotations_df = _load_annotation_files(annotations_dir)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/03_process_human_coding.py", line 68, in _load_annotation_files
    raise ValueError(f"Annotation files are missing required columns: {missing}")
ValueError: Annotation files are missing required columns: {'annotator_id', 'rating'}

- python code/04_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv -> rc=1

2026-10-30 18:21:38,862 ERROR __main__: Input scenarios file missing: data/processed/scenarios.csv


## Declared deliverables still missing

- data/processed/candidates_filtered.csv
- data/processed/ground_truth_match.csv
- data/processed/valid_scenarios.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/candidates_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_filter.py` — IS a run-book command
    - `code/02_prepare_human_coding_dir.py` — IS a run-book command
    - `code/03_process_human_coding.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/candidates_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_match.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_process_human_coding.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ground_truth_match.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_scenarios.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_process_human_coding.py` — IS a run-book command
    - `code/human_coding.py` — NOT invoked by the run-book
    - `code/manipulation_check.py` — NOT invoked by the run-book
    - `code/survey_deploy.py` — NOT invoked by the run-book
    - `code/survey_sim.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_scenarios.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
