# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/descriptive_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…synthesis.     """     # Mock data for testing     class Mo…”
- code/data/cleaner.py: synthetic/fake INPUT data not authorized by the spec — “…str(json_file):  # Skip mock data in production…”
- code/data/collector.py: synthetic/fake INPUT data not authorized by the spec — “…e")          # Check for mock data in production/CI (strict…”
- code/data/collector.py: synthetic/fake INPUT data not authorized by the spec — “…raise RuntimeError("Mock data detected in production/C…”
- code/data/extractor.py: synthetic/fake INPUT data not authorized by the spec — “…str(json_file):  # Skip mock data in production…”
- code/data/mock_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Mock Data Generator for ClinicalTr…”
- code/data/mock_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…=True, exist_ok=True)  # Mock Data Records # Structure matches the…”
- code/data/mock_data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…, indent=2)      print(f"Mock data generated successfully a…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/cleaned_studies.csv/cleaned_studies.csv: header only, ZERO data rows — the analysis produced no rows
- every produced artifact is gitignored (data/processed/cleaned_studies.csv/cleaned_studies.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/data/collector.py --output data/raw/studies.json`
  - script usage: `collector.py [-h] --start-year START_YEAR --end-year END_YEAR`
  - argparse error: `collector.py: error: the following arguments are required: --start-year, --end-year`
- run-book command: `python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --viz-dir viz/`
  - script usage: `meta_analysis.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `meta_analysis.py: error: unrecognized arguments: --viz-dir viz/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/descriptive_synthesis.py: synthetic/fake INPUT data not authorized by the spec — “…synthesis.     """     # Mock data for testing     class Mo…”; code/data/cleaner.py: synthetic/fake INPUT data not authorized by the spec — “…str(json_file):  # Skip mock data in production…”; code/data/collector.py: synthetic/fake INPUT data not authorized by the spec — “…e")          # Check for mock data in production/CI (strict…”; 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/cleaned_studies.csv/cleaned_studies.csv: header only, ZERO data rows — the analysis produced no rows; every produced artifact is gitignored (data/processed/cleaned_studies.csv/cleaned_studies.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/data/collector.py --output data/raw/studies.json (rc=2); python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv (rc=1); python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --viz-dir viz/ (rc=2); 4 declared deliverable(s) absent: data/processed/cleaned_studies.csv; data/processed/effect_sizes.csv; data/raw/verified_snapshot_2026.json

## Failing / missing run-book commands

- python code/data/collector.py --output data/raw/studies.json -> rc=2

usage: collector.py [-h] --start-year START_YEAR --end-year END_YEAR
collector.py: error: the following arguments are required: --start-year, --end-year

- python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv -> rc=1
ode/analysis/effect_sizes.py", line 323, in main
    studies_df = pd.read_csv(args.input)
                 ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
IsADirectoryError: [Errno 21] Is a directory: 'data/processed/cleaned_studies.csv'

- python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --viz-dir viz/ -> rc=2

usage: meta_analysis.py [-h] --input INPUT --output OUTPUT
                        [--plots-dir PLOTS_DIR]
meta_analysis.py: error: unrecognized arguments: --viz-dir viz/

- python -m pytest tests/ -> rc=2
66971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/contract/test_assessment_schema.py
ERROR tests/contract/test_effect_size_schema.py - pydantic.errors.PydanticUse...
ERROR tests/contract/test_participant_schema.py - pydantic.errors.PydanticUse...
ERROR tests/integration/test_analysis_pipeline.py - pydantic.errors.PydanticU...
ERROR tests/unit/test_analysis.py - pydantic.errors.PydanticUserError: Decora...
ERROR tests/unit/test_data_storage.py - pydantic.errors.PydanticUserError: De...
ERROR tests/unit/test_edge_cases.py
ERROR tests/unit/test_hash_artifacts.py
ERROR tests/unit/test_meta_analysis_threshold.py
ERROR tests/unit/test_setup_project.py
ERROR tests/unit/test_validators.py
ERROR tests/unit/test_verify_output.py - TypeError: get_data_path() missing 1...
!!!!!!!!!!!!!!!!!!! Interrupted: 12 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 13 warnings, 12 errors in 3.69s ========================



## Declared deliverables still missing

- data/processed/cleaned_studies.csv
- data/processed/effect_sizes.csv
- data/raw/verified_snapshot_2026.json
- data/results/thin_slice_result.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_studies.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bias.py` — NOT invoked by the run-book
    - `code/analysis/effect_sizes.py` — IS a run-book command
    - `code/data/cleaner.py` — IS a run-book command
    - `code/data/verify_output.py` — NOT invoked by the run-book
    - `code/setup_project.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `scripts/run_cleaner.py` — NOT invoked by the run-book
    - `scripts/run_t019_verification.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_studies.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/effect_sizes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/bias.py` — NOT invoked by the run-book
    - `code/analysis/descriptive_synthesis.py` — NOT invoked by the run-book
    - `code/analysis/effect_sizes.py` — IS a run-book command
    - `code/analysis/meta_analysis.py` — IS a run-book command
    - `code/data/thin_slice.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/effect_sizes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/verified_snapshot_2026.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/collector.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/verified_snapshot_2026.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/thin_slice_result.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/thin_slice.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/thin_slice_result.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
