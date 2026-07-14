# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/config.py: self-declared fabricated metric — “…Thresholds / memory limits – placeholder values (real values are defined # e…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py --phase evaluate`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/config.py: self-declared fabricated metric — “…Thresholds / memory limits – placeholder values (real values are defined # e…”; 1 command(s) failed: python code/main.py --phase evaluate (rc=1); 1 declared deliverable(s) absent: data/raw/dense_baseline_frames.npy

## Failing / missing run-book commands

- python code/main.py --phase evaluate -> rc=1
    ine frames...

[download_dense_baseline] Failed to download from HF Hub: 401 Client Error. (Request ID: Root=1-6a566072-14d33021312cc764498f10c3;6746a3b4-e705-4ee0-9123-2bc3a5e9250e)

Repository Not Found for url: https://huggingface.co/realestate10k/dense_baseline_v1/resolve/main/dense_baseline_frames.npy.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.
[download_dense_baseline] ERROR: 401 Client Error. (Request ID: Root=1-6a566072-14d33021312cc764498f10c3;6746a3b4-e705-4ee0-9123-2bc3a5e9250e)

Repository Not Found for url: https://huggingface.co/realestate10k/dense_baseline_v1/resolve/main/dense_baseline_frames.npy.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 163, in <module>
    main(sys.argv[1:])
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 158, in main
    phase_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 112, in phase_extract_features
    extract_features_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/data/extract_features.py", line 42, in main
    stratum_path = stratified_dir / stratum
                   ~~~~~~~~~~~~~~~^~~~~~~~~
TypeError: unsupported operand type(s) for /: 'str' and 'str'
- python code/main.py --phase compute_geometry -> rc=1
    ome/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 158, in main
    phase_func()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/main.py", line 122, in phase_compute_geometry
    geometry_pipeline_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/geometry/run_pipeline.py", line 47, in main
    raise e
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/geometry/run_pipeline.py", line 42, in main
    aggregate_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/geometry/aggregate_warps.py", line 106, in main
    warped_paths = scan_warped_frames(results_dir)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/code/geometry/aggregate_warps.py", line 37, in scan_warped_frames
    for p in results_dir.glob("*.npy")
             ^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'glob'
- python code/main.py --phase evaluate -> rc=1
    [main] Running evaluation and reporting …
Loading metrics data...

Unexpected error during report generation: unsupported operand type(s) for /: 'str' and 'str'

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `ensure_directories` — defined in `code/config.py`; called 19 way(s):

- code/config.py: - ``ensure_directories()`` – creates all standard dirs.
- code/config.py: - ``ensure_directories(Path)`` – creates a single custom dir.
- code/config.py: - ``ensure_directories([Path, Path, ...])`` – creates a list of dirs.
- code/config.py: - ``ensure_directories(Path, Path, ...)`` – creates multiple dirs.
- code/config.py: - ``ensure_directories(Path, [Path, Path])`` – mixed positional/iterable.
- code/main.py: ensure_directories()
- code/main.py: ensure_directories(get_raw_dir())
- code/validate_quickstart.py: ensure_directories()
- code/geometry/run_pipeline.py: ensure_directories()
- code/geometry/aggregate_warps.py: ensure_directories([results_dir])
- code/data/schemas.py: ensure_directories()
- code/eval/download_dense_baseline.py: ensure_directories(target_dir)
- code/eval/download_dense_baseline.py: ensure_directories(raw_dir)
- code/eval/quickstart_validator.py: ensure_directories()
- code/eval/run_dense_baseline.py: ensure_directories()
- code/eval/anova.py: ensure_directories()
- code/eval/sensitivity.py: ensure_directories(results_dir)
- code/eval/sensitivity.py: ensure_directories()
- code/eval/metrics.py: ensure_directories()  # create standard dirs if missing

Make `ensure_directories` in `code/config.py` accept ALL of the above.

### class `MemoryMonitor` (in `code/utils/memory_monitor.py`) — accessed via method/attribute names this round: `start`

`MemoryMonitor` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/utils/memory_monitor.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `MemoryMonitor` across the codebase must stop raising `AttributeError`/`TypeError`.

`MemoryMonitor.start` call sites (2):
- code/utils/memory_monitor.py: monitor.start()
- code/utils/memory_monitor.py: self._thread.start()

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/dense_baseline_frames.npy` is declared but was NOT written. Scripts referencing it:
    - `code/eval/download_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/quickstart_validator.py` — NOT invoked by the run-book
    - `code/eval/run_dense_baseline.py` — NOT invoked by the run-book
    - `code/eval/sensitivity.py` — NOT invoked by the run-book
    - `code/eval/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/dense_baseline_frames.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/dense_baseline_frames.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/dense_baseline_frames.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/eval/download_dense_baseline.py`, `code/eval/quickstart_validator.py`, `code/eval/run_dense_baseline.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-843-llmxive-follow-up-extending-latent-spati/data/results/sparse_warped_frames.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`, `code/geometry/run_pipeline.py`, `code/geometry/aggregate_warps.py`, `code/eval/quickstart_validator.py`, `code/eval/sensitivity.py`, `code/eval/metrics.py`.
