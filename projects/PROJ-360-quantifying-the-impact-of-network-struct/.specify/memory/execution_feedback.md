# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/compute_metrics.py: self-declared fabricated metric — “…needed.     Currently returns dummy values or 0.0 if not computed in T0…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/metrics.csv: header only, ZERO data rows — the analysis produced no rows
- results/correlations.json: results file is EMPTY ([]) — the analysis produced no values

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/compute_metrics.py: self-declared fabricated metric — “…needed.     Currently returns dummy values or 0.0 if not computed in T0…”; 2 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/metrics.csv: header only, ZERO data rows — the analysis produced no rows; results/correlations.json: results file is EMPTY ([]) — the analysis produced no values; 2 command(s) failed: python code/download.py --limit 50 --output data/raw/cif/ (rc=1); python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ (rc=1); 1 declared deliverable(s) absent: data/processed/filtered_features.csv

## Failing / missing run-book commands

- python code/download.py --limit 50 --output data/raw/cif/ -> rc=1
    2026-07-22 15:17:18,080 - download_logger - ERROR - MP_API_KEY not set in environment. Please set MP_API_KEY environment variable.
- python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/ -> rc=1
    2026-07-22 15:17:19,493 - network_logger - ERROR - No CIF files found in data/raw/cif

## Declared deliverables still missing

- data/processed/filtered_features.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `Config` (in `code/config.py`) — accessed via method/attribute names this round: `get`

`Config` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `Config` across the codebase must stop raising `AttributeError`/`TypeError`.

`Config.get` call sites (25):
- code/runtime_monitor.py: return data.get("start_epoch")
- code/report.py: r2_interpretation = performance_data.get("r2_interpretation")
- code/config.py: Compatible with dict.get() usage.
- code/config.py: return self._config_data.get(key, default)
- code/config.py: print(f"MP_API_KEY: {config.get('MP_API_KEY', 'Not set')}")
- code/config.py: print(f"RANDOM_SEED: {config.get('RANDOM_SEED')}")
- code/config.py: print(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")
- code/construct_network.py: return fallback_radii.get(element, 1.0)
- code/compute_metrics.py: material_data = manifest['materials'].get(material_id)
- code/compute_metrics.py: k_x = material_data.get('k_x')
- code/compute_metrics.py: k_y = material_data.get('k_y')
- code/compute_metrics.py: k_z = material_data.get('k_z')
- code/compute_metrics.py: for mat_id, mat_info in manifest.get('materials', {}).items():
- code/compute_metrics.py: mat_id = row.get("material_id")
- code/compute_metrics.py: scalar = thermal_scalars.get(mat_id)
- code/compute_metrics.py: scalar = thermal_scalars.get(material_id)
- code/download.py: response = requests.get(url, headers=headers, params=params, timeout=timeout)
- code/download.py: materials = data.get("data", [])
- code/download.py: material_id = material.get("material_id")
- code/download.py: thermo = material.get("thermo", {})
- code/download.py: thermal_cond = material.get("thermal_conductivity")
- code/download.py: "k_xx": thermal_cond.get('k_xx'),
- code/download.py: "k_yy": thermal_cond.get('k_yy'),
- code/download.py: "k_zz": thermal_cond.get('k_zz'),
- code/download.py: response = requests.get(url, headers=headers, timeout=timeout)

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/filtered_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/integration_test.py` — NOT invoked by the run-book
    - `code/validate_artifacts.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/filtered_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
