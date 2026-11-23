# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/train.py: self-declared fabricated metric — “…shuffling y and calculating a dummy score (e.g., 0 or random).…”
- code/data/train.py: self-declared fabricated metric — “…Actually, let's just return a mock result structure to satisfy the sign…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/data/train.py: self-declared fabricated metric — “…shuffling y and calculating a dummy score (e.g., 0 or random).…”; code/data/train.py: self-declared fabricated metric — “…Actually, let's just return a mock result structure to satisfy the sign…”; 3 command(s) failed: python code/data/features.py (rc=1); python code/data/preprocess.py (rc=1); python code/data/train.py (rc=1); 4 declared deliverable(s) absent: data/processed/deviation.csv; data/processed/exclusion_summary.json; data/processed/features.csv

## Failing / missing run-book commands

- python code/data/features.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/features.py", line 19, in <module>
    from features import extract_features_batch
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/features.py", line 19, in <module>
    from features import extract_features_batch
ImportError: cannot import name 'extract_features_batch' from partially initialized module 'features' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/features.py)
- python code/data/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/preprocess.py", line 241, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/preprocess.py", line 197, in main
    os.makedirs(paths.processed, exist_ok=True)
                ^^^^^^^^^^^^^^^
AttributeError: 'ProjectPaths' object has no attribute 'processed'
- python code/data/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/train.py", line 395, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-925-llmxive-follow-up-extending-lens-rethink/code/data/train.py", line 359, in main
    seeds = config.get("seeds", [42, 123, 456, 789, 101112])
            ^^^^^^^^^^
AttributeError: 'RunConfig' object has no attribute 'get'

## Declared deliverables still missing

- data/processed/deviation.csv
- data/processed/exclusion_summary.json
- data/processed/features.csv
- data/raw/pick-a-pic.parquet

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `ProjectPaths` (in `code/config.py`) — accessed via method/attribute names this round: `processed`

`ProjectPaths` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `ProjectPaths` across the codebase must stop raising `AttributeError`/`TypeError`.

`ProjectPaths.processed` call sites (0):

### class `RunConfig` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`RunConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `RunConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`RunConfig.get` call sites (10):
- code/validation_t014b.py: caption = row.get("caption")
- code/validation_t014b.py: stored_val = row.get("linguistic_uncertainty_proxy")
- code/utils/exclusion_processor.py: reason = record.get('reason', 'UNKNOWN')
- code/utils/validation.py: properties = schema.get('properties', {})
- code/utils/validation.py: required_fields = schema.get('required', [])
- code/utils/validation.py: field_type = field_schema.get('type', 'string')
- code/utils/validation.py: description = field_schema.get('description', '')
- code/utils/validation.py: required_cols = schema.get('required', [])
- code/utils/validation.py: row_dict = {k: v for k, v in row.items() if k in schema.get('properties', {})}
- code/data/train.py: seeds = config.get("seeds", [42, 123, 456, 789, 101112])

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/deviation.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validation_t029b.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/train.py` — IS a run-book command
    - `code/tests/test_preprocess.py` — NOT invoked by the run-book
    - `code/tests/contract/test_deviation_target_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/deviation.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/exclusion_processor.py` — NOT invoked by the run-book
    - `code/tests/test_t015b_exclusion_processor.py` — NOT invoked by the run-book
    - `code/tests/test_features.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validation_t029b.py` — NOT invoked by the run-book
    - `code/features.py` — NOT invoked by the run-book
    - `code/validation_t014b.py` — NOT invoked by the run-book
    - `code/utils/validation.py` — NOT invoked by the run-book
    - `code/models/linguistic_feature_vector.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/features.py` — IS a run-book command
    - `code/data/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pick-a-pic.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/utils/validation.py` — NOT invoked by the run-book
    - `code/utils/errors.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/data/features.py` — IS a run-book command
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/tests/test_t014b_validation.py` — NOT invoked by the run-book
    - `code/tests/test_features.py` — NOT invoked by the run-book
    - `code/tests/test_download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/pick-a-pic.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
