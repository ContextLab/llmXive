# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/analysis/regression.py: self-declared fabricated metric — “…pant_id.     # Here we return dummy values for the pipeline to run.…”
- code/src/analysis/robustness.py: self-declared fabricated metric — “…df):     # Simplified: return dummy values     return {"r": 0.2, "p": 0…”
- code/src/analysis/robustness.py: self-declared fabricated metric — “…ta):     # Simplified: return dummy values     return {"ci_lower": 0.05…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/src/analysis/regression.py: self-declared fabricated metric — “…pant_id.     # Here we return dummy values for the pipeline to run.…”; code/src/analysis/robustness.py: self-declared fabricated metric — “…df):     # Simplified: return dummy values     return {"r": 0.2, "p": 0…”; code/src/analysis/robustness.py: self-declared fabricated metric — “…ta):     # Simplified: return dummy values     return {"ci_lower": 0.05…”; 4 command(s) failed: python code/data/download.py (rc=1); python code/data/validate_data.py (rc=1); python code/data/preprocess.py (rc=1); 7 declared deliverable(s) absent: data/derived/auditory_trials.csv; data/derived/trial_data.csv; data/derived/visual_trials.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
    2026-07-14 00:16:47,859 - INFO - Starting data download (T005)...
2026-07-14 00:16:47,859 - INFO - Attempting to download dataset from: https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv
2026-07-14 00:16:47,951 - ERROR - Failed to download from https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv
2026-07-14 00:16:47,952 - INFO - Failed, trying next URL...
2026-07-14 00:16:47,952 - ERROR - ERROR: Could not download a valid behavioral dataset from any source.
2026-07-14 00:16:47,952 - ERROR - Project blocked. No real data source available.
- python code/data/validate_data.py -> rc=1
    2026-07-14 00:16:48,474 - INFO - Starting data validation (T006)...
2026-07-14 00:16:48,475 - ERROR - Could not find downloaded dataset. Expected one of: ['data/behavioral_data.csv', 'data/downloaded/behavioral_data.csv', 'data/ds003386_behavioral.csv', 'data/downloaded/ds003386_behavioral.csv']
2026-07-14 00:16:48,475 - INFO - Validation report written to data/validation_report.json
- python code/data/preprocess.py -> rc=1
    2026-07-14 00:16:48,892 - INFO - Starting data preprocessing (T012)...
2026-07-14 00:16:48,892 - INFO - Output directory ready: /home/runner/work/llmXive/llmXive/projects/PROJ-179-the-influence-of-metacognitive-awareness/code/data/derived
2026-07-14 00:16:48,892 - ERROR - No input CSV found in data/ directory. Run T005 first.
- python code/analysis.py -> rc=1
    2026-07-14 00:16:48,985 - INFO - Starting data availability validation (T004)...
2026-07-14 00:16:48,985 - INFO - Checking OpenNeuro ds003386 availability...
2026-07-14 00:16:48,985 - WARNING - OpenNeuro ds003386 check result: OpenNeuro ds003386 not found locally.
2026-07-14 00:16:48,985 - INFO - Scanning for alternative behavioral datasets...
2026-07-14 00:16:48,986 - ERROR - ERROR: Project blocked. No valid behavioral dataset found.
2026-07-14 00:16:48,986 - ERROR - OpenNeuro ds003386 lacks required behavioral fields. Aborting.
2026-07-14 00:16:48,986 - ERROR - Please download a valid behavioral dataset containing 'confidence_rating' and 'source_label' to the data/ directory.
{"status": "FAIL", "message": "ERROR: Project blocked. OpenNeuro ds003386 lacks required behavioral fields. Aborting."}

2026-07-14 00:16:48,983 - llmXive - INFO - Starting full analysis pipeline...

## Declared deliverables still missing

- data/derived/auditory_trials.csv
- data/derived/trial_data.csv
- data/derived/visual_trials.csv
- data/results/bootstrap_config.json
- data/results/primary_analysis.json
- data/results/regression_analysis.json
- data/results/robustness_analysis.json

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### class `AppConfig` (in `code/config/env_config.py`) — accessed via method/attribute names this round: `get`

`AppConfig` is used like a logger: different scripts call DIFFERENT method names on it, and the set grows every round. Adding only the name(s) above will fail next round on the NEXT name. Make the class tolerant of ANY method name **without removing the ones it already has**, by either:
  1. defining the full method set explicitly (keep existing methods like the ones already in `code/config/env_config.py` AND add the missing ones), or
  2. adding a permissive fallback so unknown attributes resolve to a no-op callable, e.g.:

     ```python
     def __getattr__(self, name):
         # any logger-style call (.info/.debug/.warning/.error/...) becomes a tolerant no-op
         def _noop(*args, **kwargs):
             return None
         return _noop
     ```

Whichever you choose, every call site of `AppConfig` across the codebase must stop raising `AttributeError`/`TypeError`.

`AppConfig.get` call sites (25):
- code/src/analysis/bootstrap.py: BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/analysis/bootstrap.py: n_resamples = CONFIG.get("analysis", {}).get("bootstrap_count", DEFAULT_BOOTSTRAP_COUNT)
- code/src/analysis/robustness.py: BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/analysis/diagnostics.py: base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/analysis/diagnostics.py: results_dir = Path(base_dir) / config.get("paths", {}).get("results", "data/results")
- code/src/analysis/diagnostics.py: derived_dir = Path(base_dir) / config.get("paths", {}).get("derived_data", "data/derived")
- code/src/analysis/diagnostics.py: residuals = regression_results.get("residuals", [])
- code/src/analysis/diagnostics.py: y_values = regression_results.get("y_values", [])
- code/src/analysis/diagnostics.py: "normality_passed": normality_result.get("is_normal", False),
- code/src/analysis/diagnostics.py: "homoscedasticity_passed": homoscedasticity_result.get("is_homoscedastic", False),
- code/src/analysis/diagnostics.py: "collinearity_flagged": vif_result.get("collinearity_flag", False),
- code/src/analysis/diagnostics.py: normality_result.get("is_normal", False) and
- code/src/analysis/diagnostics.py: homoscedasticity_result.get("is_homoscedastic", False) and
- code/src/analysis/diagnostics.py: not vif_result.get("collinearity_flag", False)
- code/src/analysis/diagnostics.py: logger.error(f"Diagnostics failed: {results.get('reason', 'Unknown error')}")
- code/src/analysis/correlation.py: BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/analysis/correlation.py: seed = CONFIG.get("analysis", {}).get("random_seed", 42)
- code/src/analysis/regression.py: BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
- code/src/report/generate.py: "model_1": regression_results.get("model_1", {}),
- code/src/report/generate.py: "model_2": regression_results.get("model_2", {}),
- code/src/report/generate.py: "delta_r_squared": regression_results.get("delta_r_squared", np.nan),
- code/src/report/generate.py: "f_change": regression_results.get("f_change", np.nan),
- code/src/report/generate.py: "normality_passed": diagnostics_results.get("normality_passed", False),
- code/src/report/generate.py: "homoscedasticity_passed": diagnostics_results.get("homoscedasticity_passed", False),
- code/src/report/generate.py: "collinearity_flagged": diagnostics_results.get("collinearity_flagged", False),

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/auditory_trials.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/auditory_trials.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/trial_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/src/utils/security.py` — NOT invoked by the run-book
    - `code/src/utils/stats.py` — NOT invoked by the run-book
    - `code/src/analysis/filter.py` — NOT invoked by the run-book
    - `code/src/analysis/diagnostics.py` — NOT invoked by the run-book
    - `code/src/analysis/correlation.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/trial_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/derived/visual_trials.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/robustness.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/visual_trials.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/bootstrap_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/bootstrap.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/bootstrap_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/primary_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/tests/unit/test_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/primary_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/diagnostics.py` — NOT invoked by the run-book
    - `code/src/analysis/regression.py` — NOT invoked by the run-book
    - `code/src/report/generate.py` — NOT invoked by the run-book
    - `code/tests/unit/test_regression.py` — NOT invoked by the run-book
    - `code/code/performance_optimizer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/robustness_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/src/analysis/robustness.py` — NOT invoked by the run-book
    - `code/src/report/generate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/robustness_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/validate_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/validate_data.py`.

### `raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/download.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/download.py`.

### `raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/download.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/download.py`.

### `raw.githubusercontent.com/psychopy/datasets/main/sample_behavioral_data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/data/validate_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `raw.githubusercontent.com/psychopy/datasets/main/sample_behavioral_data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/data/validate_data.py`.
