# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/human_validation.py: self-declared fabricated metric — “…generate a template     with placeholder scores (or simulate a real run if t…”
- code/human_validation.py: metric `score` assigned from an RNG draw (line 88)

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/derived/resource_monitoring_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ COMPUTE-ENVIRONMENT failure — RE-SCOPE the method, don't just edit the script

These commands failed because the analysis needs hardware the FREE, CPU-only CI runner does NOT have (a GPU/CUDA, 8-bit quantization via bitsandbytes, or more RAM than is available). This is NOT a code bug you can patch by tweaking the failing line — the analysis MUST run on a CPU-only free runner (Constitution IV). RE-SCOPE the approach: drop `load_in_8bit` / `device_map='cuda'` and load in default precision on CPU; use a SMALLER model; REDUCE the dataset subset / sample / batch size; prefer a CPU-tractable method. Change the METHOD, not just the line that threw:

- `python code/main.py --config code/config.yaml`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/human_validation.py: self-declared fabricated metric — “…generate a template     with placeholder scores (or simulate a real run if t…”; code/human_validation.py: metric `score` assigned from an RNG draw (line 88); every produced artifact is gitignored (data/derived/resource_monitoring_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/data_loader.py --download (rc=1); python code/data_loader.py --verify (rc=1); python code/main.py --config code/config.yaml (rc=-11); 3 declared deliverable(s) absent: data/derived/collapse_points.parquet; data/derived/stress_curves.parquet; data/validation/human_annotations.csv

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 353, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 333, in main
    config = get_config(args.config)
             ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_config() takes 0 positional arguments but 1 was given
- python code/data_loader.py --verify -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 353, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/code/data_loader.py", line 333, in main
    config = get_config(args.config)
             ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: get_config() takes 0 positional arguments but 1 was given
- python code/main.py --config code/config.yaml -> rc=-11
    WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1784797119.766212    2545 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: AVX2 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1784797122.559787    2545 cudart_stub.cc:31] Could not find cuda drivers on your machine, GPU will not be used.
E0000 00:00:1784797123.562530    2545 cuda_platform.cc:52] failed call to cuInit: INTERNAL: CUDA error: Failed call to cuInit: UNKNOWN ERROR (303)
2026-07-23 08:58:43,571 - jax._src.xla_bridge - INFO - Unable to initialize backend 'tpu': INTERNAL: Failed to open libtpu.so: libtpu.so: cannot open shared object file: No such file or directory
2026-07-23 08:58:43,571 - root - INFO - CPU-only enforcement check passed. No GPU devices detected.
- python code/analysis.py --validate-sss -> rc=1
    2026-07-23 08:59:00,295 - INFO - Running sensitivity analysis...
2026-07-23 08:59:00,295 - INFO - Starting sensitivity analysis for thresholds: [0.4, 0.45, 0.5, 0.55, 0.6]
2026-07-23 08:59:00,295 - ERROR - Data files missing: Required data files missing. Need /home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/data/derived/collapse_points.parquet and /home/runner/work/llmXive/llmXive/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow/data/derived/stress_curves.parquet. Run main.py and US2 tasks first.

## Declared deliverables still missing

- data/derived/collapse_points.parquet
- data/derived/stress_curves.parquet
- data/validation/human_annotations.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_config` — defined in `code/config.py`; called 7 way(s):

- code/main.py: config = get_config(args.config)
- code/data_loader.py: config = get_config(args.config)
- code/metrics.py: self.config = config or get_config()
- code/metrics.py: config = get_config()
- code/human_validation.py: config = get_config()
- code/validation_analysis.py: return get_config()
- code/analysis.py: config = get_config()

Make `get_config` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/collapse_points.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/validation_analysis.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/collapse_points.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/stress_curves.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — IS a run-book command
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/validation_analysis.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/stress_curves.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/validation/human_annotations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/human_validation.py` — NOT invoked by the run-book
    - `code/validation_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/human_annotations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `sensitivity_analysis.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[derived_path]`
- PRODUCER(s) to edit: `code/main.py`, `code/analysis.py`
- CONSUMER(s) that read it: `code/main.py`, `code/analysis.py`
  → Edit the producer so every required name [derived_path] is in `sensitivity_analysis.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
