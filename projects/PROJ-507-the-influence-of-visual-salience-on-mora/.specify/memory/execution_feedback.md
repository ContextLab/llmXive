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

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 18 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…r: If the path indicates synthetic data and --allow-synthetic is…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…help="Allow analysis of synthetic data (located in data/synth/)…”; code/data_hygiene.py: synthetic/fake INPUT data not authorized by the spec — “…]          # Define synthetic data directory     synthetic_…”; 6 run-book script(s) missing (plan/impl path mismatch): python code/00_pilot_power_analysis.py --config config/pilot.yaml; python code/04_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv; python code/03_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv; 1 command(s) failed: python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv (rc=1); 4 declared deliverable(s) absent: data/processed/candidates_filtered.csv; data/processed/cleaned_responses.csv; data/processed/valid_scenarios.csv

## Failing / missing run-book commands

- python code/00_pilot_power_analysis.py --config config/pilot.yaml -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/00_pilot_power_analysis.py': [Errno 2] No such file or directory

- python code/01_ingest_and_filter.py  --max-scenarios 30  --output data/processed/candidates_filtered.csv -> rc=1
ience-on-mora/lib/python3.11/site-packages/datasets/load.py", line 1819, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'open_images' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/open_images to ask for access.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 341, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 338, in main
    ingest_and_filter(num_samples=num_samples, tags=args.tags, output_csv=output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/01_ingest_and_filter.py", line 179, in ingest_and_filter
    raise DataFetchError(
data_prep.DataFetchError: Verified source requested but FiftyOne is not installed.

- python code/04_human_coding.py  --input data/processed/candidates_filtered.csv  --output data/processed/scenarios.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/04_human_coding.py': [Errno 2] No such file or directory

- python code/03_manipulate_stimuli.py  --input data/processed/scenarios.csv  --output data/processed/stimuli_manifest.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/03_manipulate_stimuli.py': [Errno 2] No such file or directory

- python code/04_survey_deployment.py  --mode pilot  --participants 10  --output data/processed/responses_raw.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/04_survey_deployment.py': [Errno 2] No such file or directory

- python code/05_data_cleaning.py  --input data/processed/responses_raw.csv  --output data/processed/responses_cleaned.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/05_data_cleaning.py': [Errno 2] No such file or directory

- python code/06_analysis_clmm.py  --input data/processed/responses_cleaned.csv  --output data/processed/analysis_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-507-the-influence-of-visual-salience-on-mora/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-507-the-influence-of-visual-salience-on-mora/code/06_analysis_clmm.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/candidates_filtered.csv
- data/processed/cleaned_responses.csv
- data/processed/valid_scenarios.csv
- data/raw/checksums.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `fiftyone` to the project's `requirements.txt` and `pip install fiftyone`.
- **Verified**: this loads **5** real records with fields: image_id, image_url, width, height, tags, bounding_boxes.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import fiftyone as fo
import fiftyone.zoo as foz

# Load a tiny subset of the Open Images V6 validation split to keep the download fast
dataset = foz.load_zoo_dataset(
    "open-images-v6",
    split="validation",
    max_samples=5,
    dataset_name="tmp_open_images_v6",
)

print(f"RECORDS={len(dataset)}")
# Map FiftyOne fields to the requested schema (the dataset contains these fields internally)
fields = [
    "image_id",
    "image_url",
    "width",
    "height",
    "tags",
    "bounding_boxes",
]
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/candidates_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_filter.py` — IS a run-book command
    - `code/03_process_human_coding.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/candidates_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_responses.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_cleaning.py` — NOT invoked by the run-book
    - `code/profile_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_responses.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/valid_scenarios.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_process_human_coding.py` — NOT invoked by the run-book
    - `code/human_coding.py` — NOT invoked by the run-book
    - `code/manipulation_check.py` — NOT invoked by the run-book
    - `code/survey_deploy.py` — NOT invoked by the run-book
    - `code/survey_sim.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/valid_scenarios.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_ingest_and_filter.py` — IS a run-book command
    - `code/verify_data_integrity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
