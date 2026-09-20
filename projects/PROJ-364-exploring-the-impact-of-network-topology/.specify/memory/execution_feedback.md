# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/contracts/analysis.schema.yaml: synthetic/fake INPUT data not authorized by the spec — “…description: Warning if synthetic data was detected.     proper…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Validation…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…rsioned, and checksummed synthetic datasets strictly for pipeline va…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…st be logged to indicate synthetic data usage. """ import os imp…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “….DataFrame]:     """     Generate deterministic synthetic defect coordinates.…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…f"Generating {n_samples} synthetic samples with {n_defects_per_samp…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…adata dictionary for the synthetic dataset."""     return {…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, str]:     """     Generate a synthetic dataset for validation p…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/synthetic_defects.csv/synthetic_defects.csv, data/raw/synthetic_defects.csv/synthetic_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 13 fabricated/simulated-result signal(s) — results are not real measurements: code/contracts/analysis.schema.yaml: synthetic/fake INPUT data not authorized by the spec — “…description: Warning if synthetic data was detected.     proper…”; code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Validation…”; code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…rsioned, and checksummed synthetic datasets strictly for pipeline va…”; every produced artifact is gitignored (data/raw/synthetic_defects.csv/synthetic_defects.csv, data/raw/synthetic_defects.csv/synthetic_metadata.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 run-book script(s) missing (plan/impl path mismatch): python code/utils/checksum_data.py data/raw/synthetic_defects.csv; python code/main.py --config code/config.yaml; 1 command(s) failed: python code/src/data_ingestion/generate_synthetic.py --output data/raw/synthetic_defects.csv --seed 42 (rc=1)

## Failing / missing run-book commands

- python code/src/data_ingestion/generate_synthetic.py --output data/raw/synthetic_defects.csv --seed 42 -> rc=1
    2026-09-20 09:25:58 - llmXive.data_ingestion - WARNING - === SYNTHETIC DATA GENERATION MODE ===
2026-09-20 09:25:58 - llmXive.data_ingestion - WARNING - This dataset is generated for pipeline validation ONLY.
2026-09-20 09:25:58 - llmXive.data_ingestion - WARNING - Do not use for scientific hypothesis testing.
2026-09-20 09:25:58 - llmXive.data_ingestion - ERROR - Failed to generate synthetic data: generate_checksum_manifest() got an unexpected keyword argument 'root_dir'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data_ingestion/generate_synthetic.py", line 181, in main
    result = generate_synthetic_dataset(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data_ingestion/generate_synthetic.py", line 143, in generate_synthetic_dataset
    manifest_data = generate_checksum_manifest(files_to_hash, root_dir=out_path)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: generate_checksum_manifest() got an unexpected keyword argument 'root_dir'
- python code/utils/checksum_data.py data/raw/synthetic_defects.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/utils/checksum_data.py': [Errno 2] No such file or directory
- python code/main.py --config code/config.yaml -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/main.py': [Errno 2] No such file or directory

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `generate_checksum_manifest` — defined in `code/src/utils/checksum.py`; called 3 way(s):

- code/tests/unit/test_checksum.py: result_path = generate_checksum_manifest([str(file1), str(file2)], manifest_path)
- code/tests/unit/test_checksum.py: generate_checksum_manifest([str(file_path)], manifest_path)
- code/src/data_ingestion/generate_synthetic.py: manifest_data = generate_checksum_manifest(files_to_hash, root_dir=out_path)

Make `generate_checksum_manifest` in `code/src/utils/checksum.py` accept ALL of the above.
