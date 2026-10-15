# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Generate minimal dummy raw input files for the gut‑microb…”
- code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…t:     """Create the two dummy raw input files.      Returns:…”
- code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…f"Error while generating dummy data: {exc}", file=sys.stderr…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/clr_abundances.parquet, data/processed/ingest_provenance.json, data/raw/ingest_validation.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Generate minimal dummy raw input files for the gut‑microb…”; code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…t:     """Create the two dummy raw input files.      Returns:…”; code/src/pipeline/generate_dummy_data.py: synthetic/fake INPUT data not authorized by the spec — “…f"Error while generating dummy data: {exc}", file=sys.stderr…”; every produced artifact is gitignored (data/processed/clr_abundances.parquet, data/processed/ingest_provenance.json, data/raw/ingest_validation.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python -m src.pipeline.run_permutation --iterations 1000 --seed 42 (rc=1); python -m pytest -q src/tests (rc=4); 3 declared deliverable(s) absent: data/processed/filtered_samples.parquet; data/processed/patient_outcome_slopes.parquet; data/processed/patient_taxon_slopes.parquet

## Failing / missing run-book commands

- python -m src.pipeline.run_permutation --iterations 1000 --seed 42 -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/run_permutation.py", line 78, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/run_permutation.py", line 67, in main
    run_permutation(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/permutation.py", line 214, in run_permutation
    clr = _encode_sex(clr)
          ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-331-investigating-the-correlation-between-gu/code/src/pipeline/permutation.py", line 131, in _encode_sex
    df["sex"] = df["sex"].map({"M": 0, "F": 1})
                ~~^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 4102, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/indexes/base.py", line 3812, in get_loc
    raise KeyError(key) from err
KeyError: 'sex'

- python -m pytest -q src/tests -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: src/tests



## Declared deliverables still missing

- data/processed/filtered_samples.parquet
- data/processed/patient_outcome_slopes.parquet
- data/processed/patient_taxon_slopes.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/preprocess.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_correlation_only.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_preprocess_default.py` — NOT invoked by the run-book
    - `code/src/pipeline/run_us1.py` — NOT invoked by the run-book
    - `code/tests/test_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_correlation_adj.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/test_preprocess_default_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_outcome_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_outcome_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/patient_taxon_slopes.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/pipeline/correlation.py` — NOT invoked by the run-book
    - `code/src/pipeline/slopes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/patient_taxon_slopes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
